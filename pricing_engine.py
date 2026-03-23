from collections import defaultdict, deque
from datetime import datetime
import numpy as np
from data_simulator import get_base_price


# ── Config ────────────────────────────────────────────────────────────────────
WINDOW_SEARCHES   = 30   # seconds: how far back we count searches
WINDOW_BOOKINGS   = 60   # seconds: how far back we count bookings
MAX_PRICE_MULT    = 2.0  # never charge more than 2x base
MIN_PRICE_MULT    = 0.7  # never go below 70% of base


# ── State stores (simulates Redis in-memory) ──────────────────────────────────
search_events    = defaultdict(deque)   # route -> deque of timestamps
booking_events   = defaultdict(deque)   # route -> deque of (timestamp, seats)
inventory_state  = defaultdict(lambda: {"remaining": 100, "total": 180})
competitor_prices = defaultdict(dict)   # route -> {competitor: price}
current_prices   = {}                   # route -> computed price
price_history    = defaultdict(list)    # route -> [(timestamp, price)]


# ── Event ingestion ───────────────────────────────────────────────────────────
def ingest_event(event):
    """Route incoming event to the right handler."""
    t = event["type"]
    if t == "search":
        _handle_search(event)
    elif t == "booking":
        _handle_booking(event)
    elif t == "inventory":
        _handle_inventory(event)
    elif t == "competitor_price":
        _handle_competitor(event)

    # Recompute price for the affected route
    route = event.get("route")
    if route:
        new_price = compute_price(route)
        current_prices[route] = new_price
        price_history[route].append((datetime.now(), new_price))
        if len(price_history[route]) > 100:
            price_history[route].pop(0)
    return current_prices


def _handle_search(event):
    route = event["route"]
    now = datetime.now().timestamp()
    search_events[route].append(now)
    _evict_old(search_events[route], now, WINDOW_SEARCHES)


def _handle_booking(event):
    route = event["route"]
    now = datetime.now().timestamp()
    booking_events[route].append((now, event["seats_booked"]))
    _evict_old_tuples(booking_events[route], now, WINDOW_BOOKINGS)


def _handle_inventory(event):
    route = event["route"]
    inventory_state[route]["remaining"] = event["seats_remaining"]
    inventory_state[route]["total"] = event["total_seats"]


def _handle_competitor(event):
    route = event["route"]
    competitor_prices[route][event["competitor"]] = event["price"]


def _evict_old(dq, now, window):
    while dq and now - dq[0] > window:
        dq.popleft()


def _evict_old_tuples(dq, now, window):
    while dq and now - dq[0][0] > window:
        dq.popleft()


# ── Scoring signals ───────────────────────────────────────────────────────────
def demand_score(route):
    """
    Returns a multiplier based on searches + bookings + inventory scarcity.
    Range: roughly 0.8 to 1.5
    """
    searches = len(search_events[route])
    bookings = sum(s for _, s in booking_events[route])
    inv = inventory_state[route]
    occupancy = 1.0 - (inv["remaining"] / max(inv["total"], 1))

    # Normalize signals to 0-1 range
    search_signal  = min(searches / 20.0, 1.0)   # saturates at 20 searches/30s
    booking_signal = min(bookings / 10.0, 1.0)   # saturates at 10 seats/60s
    scarcity       = occupancy                    # already 0-1

    # Weighted combination
    score = (search_signal * 0.35) + (booking_signal * 0.40) + (scarcity * 0.25)

    # Map to multiplier: neutral at 0.5 score → 1.0x, high demand → up to 1.5x
    multiplier = 0.85 + (score * 1.30)
    return round(min(multiplier, 1.5), 4)


def competitor_delta(route):
    """
    Returns a multiplier based on how our base price compares to competitors.
    If competitors are cheaper, we lower; if we're cheapest, we can nudge up.
    Range: 0.88 to 1.10
    """
    comp = competitor_prices.get(route, {})
    if not comp:
        return 1.0

    our_base = get_base_price(route)
    avg_competitor = np.mean(list(comp.values()))
    min_competitor = min(comp.values())

    ratio = our_base / avg_competitor  # >1 means we're more expensive

    if ratio > 1.10:
        return 0.92   # undercut — we're too expensive vs market
    elif ratio > 1.02:
        return 0.97
    elif ratio < 0.90:
        return 1.08   # we're cheapest — slight upward nudge
    else:
        return 1.0    # roughly at market


def ml_elasticity_signal(route):
    """
    Simulates an ML demand-elasticity model output.
    In production this would be a trained model (e.g. XGBoost).
    Here we approximate using recent booking velocity.
    Range: 0.95 to 1.15
    """
    bookings_last_min = sum(s for _, s in booking_events[route])
    # Fast booking velocity = inelastic demand = can charge more
    velocity_score = min(bookings_last_min / 8.0, 1.0)
    return round(0.95 + velocity_score * 0.20, 4)


# ── Final price computation ───────────────────────────────────────────────────
def compute_price(route):
    """
    Combine all three signals into a final price.
    Final = base × demand_score × competitor_delta × ml_signal
    Clamped to [MIN_PRICE_MULT, MAX_PRICE_MULT] × base
    """
    base  = get_base_price(route)
    d     = demand_score(route)
    c     = competitor_delta(route)
    ml    = ml_elasticity_signal(route)

    raw_multiplier = d * c * ml
    clamped = max(MIN_PRICE_MULT, min(raw_multiplier, MAX_PRICE_MULT))
    final = round(base * clamped)

    return {
        "route":         f"{route[0]}-{route[1]}",
        "base_price":    base,
        "final_price":   final,
        "multiplier":    round(clamped, 4),
        "demand_score":  d,
        "comp_delta":    c,
        "ml_signal":     ml,
        "searches_30s":  len(search_events[route]),
        "seats_left":    inventory_state[route]["remaining"],
        "updated_at":    datetime.now().strftime("%H:%M:%S"),
    }


def get_all_prices():
    return {r: compute_price(r) for r in get_base_price.__globals__["BASE_PRICES"]}
