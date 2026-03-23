import random
import time
from datetime import datetime, timedelta

ROUTES = [
    ("DEL", "BOM"), ("BOM", "BLR"), ("DEL", "BLR"),
    ("BOM", "HYD"), ("DEL", "CCU"), ("BLR", "MAA"),
]

HOTELS = ["Hotel Taj Delhi", "Marriott Mumbai", "ITC Bangalore",
          "Hyatt Hyderabad", "Oberoi Kolkata"]

BASE_PRICES = {
    ("DEL", "BOM"): 4500, ("BOM", "BLR"): 3800, ("DEL", "BLR"): 5200,
    ("BOM", "HYD"): 3200, ("DEL", "CCU"): 4800, ("BLR", "MAA"): 2900,
}

HOTEL_BASE = {h: random.randint(3000, 8000) for h in HOTELS}


def generate_search_event():
    route = random.choice(ROUTES)
    return {
        "type": "search",
        "timestamp": datetime.now().isoformat(),
        "route": route,
        "travel_date": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
        "passengers": random.randint(1, 4),
    }


def generate_booking_event():
    route = random.choice(ROUTES)
    return {
        "type": "booking",
        "timestamp": datetime.now().isoformat(),
        "route": route,
        "seats_booked": random.randint(1, 3),
        "price_paid": BASE_PRICES[route] * random.uniform(0.9, 1.3),
    }


def generate_inventory_event():
    route = random.choice(ROUTES)
    return {
        "type": "inventory",
        "timestamp": datetime.now().isoformat(),
        "route": route,
        "seats_remaining": random.randint(2, 120),
        "total_seats": 180,
    }


def generate_competitor_event():
    route = random.choice(ROUTES)
    base = BASE_PRICES[route]
    return {
        "type": "competitor_price",
        "timestamp": datetime.now().isoformat(),
        "route": route,
        "competitor": random.choice(["IndiGo", "SpiceJet", "AirAsia", "Vistara"]),
        "price": base * random.uniform(0.75, 1.25),
    }


def stream_events(callback, interval=0.5):
    """Continuously generate events and pass to callback."""
    generators = [
        generate_search_event,
        generate_search_event,   # searches are more frequent
        generate_search_event,
        generate_booking_event,
        generate_inventory_event,
        generate_competitor_event,
    ]
    print(f"[simulator] Starting event stream (interval={interval}s)")
    while True:
        event = random.choice(generators)()
        callback(event)
        time.sleep(interval)


def get_base_price(route):
    return BASE_PRICES.get(route, 4000)
