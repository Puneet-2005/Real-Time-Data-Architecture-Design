"""
dashboard.py — MakeMyTrip Real-Time Dynamic Pricing Dashboard
Run:  python dashboard.py

Shows live price updates in the terminal as events stream in.
Press Ctrl+C to stop.
"""
import threading
import time
import os
from colorama import Fore, Style, init

import price_cache
import pricing_engine
from data_simulator import stream_events

init(autoreset=True)

REFRESH_RATE = 1.5   # seconds between screen redraws


# ── Event handler (runs in background thread) ─────────────────────────────────
def on_event(event):
    """Called for every simulated event. Updates engine + cache."""
    updated = pricing_engine.ingest_event(event)
    for route_key, record in updated.items():
        key = f"{route_key[0]}-{route_key[1]}" if isinstance(route_key, tuple) else route_key
        price_cache.set_price(key, record)


# ── Rendering helpers ─────────────────────────────────────────────────────────
def color_multiplier(mult):
    if mult >= 1.3:
        return Fore.RED + f"{mult:.3f}x" + Style.RESET_ALL
    elif mult >= 1.1:
        return Fore.YELLOW + f"{mult:.3f}x" + Style.RESET_ALL
    elif mult <= 0.9:
        return Fore.CYAN + f"{mult:.3f}x" + Style.RESET_ALL
    else:
        return Fore.GREEN + f"{mult:.3f}x" + Style.RESET_ALL


def color_price(final, base):
    diff_pct = ((final - base) / base) * 100
    price_str = f"Rs.{final:,}"
    if diff_pct > 15:
        return Fore.RED + price_str + Style.RESET_ALL
    elif diff_pct > 5:
        return Fore.YELLOW + price_str + Style.RESET_ALL
    elif diff_pct < -5:
        return Fore.CYAN + price_str + Style.RESET_ALL
    else:
        return Fore.GREEN + price_str + Style.RESET_ALL


def seats_bar(remaining, total=180):
    filled = int((1 - remaining / total) * 10)
    bar = "#" * filled + "-" * (10 - filled)
    if filled >= 8:
        return Fore.RED + f"[{bar}]" + Style.RESET_ALL
    elif filled >= 5:
        return Fore.YELLOW + f"[{bar}]" + Style.RESET_ALL
    else:
        return Fore.GREEN + f"[{bar}]" + Style.RESET_ALL


# ── Main display loop ─────────────────────────────────────────────────────────
def render_dashboard():
    stats = price_cache.cache_stats()
    all_prices = price_cache.get_all()

    os.system("cls" if os.name == "nt" else "clear")

    # Header
    print(Fore.WHITE + Style.BRIGHT + "=" * 72)
    print("  MakeMyTrip  |  Real-Time Dynamic Pricing Engine  |  LIVE")
    print("=" * 72 + Style.RESET_ALL)
    print(f"  Events processed: {Fore.CYAN}{stats['writes']}{Style.RESET_ALL}   "
          f"Cache hits: {Fore.CYAN}{stats['hits']}{Style.RESET_ALL}   "
          f"Last update: {Fore.CYAN}{stats['last_write'] or '--'}{Style.RESET_ALL}")
    print()

    if not all_prices:
        print("  Waiting for first events...")
        return

    # Table header
    print(f"  {'ROUTE':<12} {'BASE':>8} {'PRICE':>10} {'MULT':>8}  "
          f"{'DEMAND':>7}  {'COMP':>6}  {'ML':>6}  {'SEATS':<14} {'SRC 30s':>6}")
    print("  " + "-" * 88)

    for key in sorted(all_prices.keys()):
        r = all_prices[key]
        route      = r.get("route", key)
        base       = r.get("base_price", 0)
        final      = r.get("final_price", 0)
        mult       = r.get("multiplier", 1.0)
        demand     = r.get("demand_score", 1.0)
        comp       = r.get("comp_delta", 1.0)
        ml         = r.get("ml_signal", 1.0)
        seats      = r.get("seats_left", 100)
        searches   = r.get("searches_30s", 0)
        updated    = r.get("updated_at", "--")

        print(
            f"  {route:<12}"
            f"  {Fore.WHITE}Rs.{base:,}{Style.RESET_ALL}".rjust(14) +
            f"  {color_price(final, base)}".rjust(18) +
            f"  {color_multiplier(mult)}".rjust(16) +
            f"  {demand:.3f}  {comp:.3f}  {ml:.3f}  "
            f"{seats_bar(seats)}  {searches:>4}  {updated}"
        )

    print()

    # Signal legend
    print(f"  {Fore.GREEN}Green{Style.RESET_ALL} = near base   "
          f"{Fore.YELLOW}Yellow{Style.RESET_ALL} = +5–15%   "
          f"{Fore.RED}Red{Style.RESET_ALL} = surge   "
          f"{Fore.CYAN}Cyan{Style.RESET_ALL} = discount")
    print(f"  Demand = search+booking+scarcity   "
          f"Comp = competitor delta   ML = elasticity signal")
    print()
    print(f"  {Style.DIM}Press Ctrl+C to stop{Style.RESET_ALL}")


def display_loop():
    while True:
        render_dashboard()
        time.sleep(REFRESH_RATE)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting MakeMyTrip Dynamic Pricing Engine...")
    print("Initialising event stream and pricing engine...")
    time.sleep(0.5)

    # Warm up with initial prices so dashboard isn't empty
    initial = pricing_engine.get_all_prices()
    for key, record in initial.items():
        route_str = f"{key[0]}-{key[1]}"
        price_cache.set_price(route_str, record)

    # Thread 1: event stream (background)
    event_thread = threading.Thread(
        target=stream_events,
        args=(on_event, 0.4),
        daemon=True
    )
    event_thread.start()

    # Thread 2: display loop (background)
    display_thread = threading.Thread(target=display_loop, daemon=True)
    display_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopped. Final cache stats:", price_cache.cache_stats())
