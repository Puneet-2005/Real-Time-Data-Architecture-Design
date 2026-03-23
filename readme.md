# MakeMyTrip — Real-Time Dynamic Pricing Engine
### Built by: Puneet | Submission: 24 Mar 2026

---

## What This Project Does

This is a working prototype of a **real-time dynamic pricing system** for MakeMyTrip's flight routes.

Instead of updating prices every few hours (old batch system), this engine:
- Processes live events every 0.4 seconds
- Calculates a new price using 3 signals — demand, competitor prices, and ML elasticity
- Displays a live updating terminal dashboard showing all route prices in real time

---

## Folder Structure

```
makemytrip_pricing/
│
├── data_simulator.py    ← Generates fake live events (searches, bookings, competitor prices)
├── pricing_engine.py    ← Brain — calculates dynamic price from 3 signals
├── price_cache.py       ← Memory store — saves latest price for each route instantly
├── dashboard.py         ← Run this — shows the live pricing table in terminal
└── README.md            ← This file
```

> All 4 files must be in the same folder. No subfolders needed.

---

## How To Run

### Step 1 — Install Python libraries (one time only)
Open terminal and run:
```
C:\Users\punee\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install numpy colorama
```

### Step 2 — Go to project folder
```
cd C:\Users\punee\OneDrive\Documents\makemytrip
```

### Step 3 — Run the dashboard
```
python3 dashboard.py
```

### Step 4 — Stop the program
Press **Ctrl + C**

---

## What You See When It Runs

```
========================================================================
  MakeMyTrip  |  Real-Time Dynamic Pricing Engine  |  LIVE
========================================================================
  Events processed: 42   Cache hits: 18   Last update: 14:32:05

  ROUTE       BASE      PRICE     MULT    DEMAND  COMP    ML    SEATS
  ---------------------------------------------------------------------
  DEL-BOM   Rs.4,500  Rs.5,310   1.18x   0.901  1.000  1.010  [######]
  BOM-BLR   Rs.3,800  Rs.4,256   1.12x   0.756  1.080  0.960  [####--]
  ...
```

Prices update automatically every 1.5 seconds.

---

## Understanding the Columns

| Column | What It Means |
|--------|---------------|
| ROUTE | Flight route (e.g. DEL-BOM = Delhi to Mumbai) |
| BASE | Starting price before any signals |
| PRICE | Final price shown to customer right now |
| MULT | Overall multiplier (1.18x = 18% above base) |
| DEMAND | Score from searches + bookings + seat scarcity |
| COMP | Competitor delta — are IndiGo/SpiceJet cheaper? |
| ML | Elasticity signal — how price-sensitive is demand? |
| SEATS | Visual occupancy bar — fuller = higher price |

---

## Color Guide

| Color | Meaning |
|-------|---------|
| Green | Price near base — normal demand |
| Yellow | Price 5–15% above base — mild surge |
| Red | Price surge — high demand detected |
| Cyan | Discount — low demand or competitor pressure |

---

## How Pricing Works (Simple Explanation)

```
Final Price = Base Price × Demand Score × Competitor Delta × ML Signal
```

Example:
```
DEL-BOM base = Rs.4,500
Demand score  = 1.18  (lots of searches, few seats left)
Competitor    = 1.00  (we match the market)
ML signal     = 1.00  (normal elasticity)

Final price   = 4,500 × 1.18 × 1.00 × 1.00 = Rs.5,310
```

Price is always kept between **70% and 200%** of base price — it never goes crazy.

---

## Architecture (4 Layers)

```
[Data Sources] → [Event Stream] → [Pricing Engine] → [Cache] → [Dashboard]

data_simulator.py   (simulates Kafka / Kinesis)
        ↓
pricing_engine.py   (simulates Apache Flink processing)
        ↓
price_cache.py      (simulates Redis in-memory store)
        ↓
dashboard.py        (the live output layer)
```

This mirrors a real production system on AWS/GCP — just running locally without cloud infrastructure.

---

## Requirements

- Python 3.x
- numpy
- colorama

Install with:
```
python3 -m pip install numpy colorama
```

---

## Project Context

**Company:** MakeMyTrip  
**Role:** Senior Principal Data Engineer  
**Goal:** Reduce pricing lag from 4–6 hours to under 1 second  
**Business Impact:** Supports Rs.8,000–10,000 Crore annual revenue target  
**References:** AWS Big Data Architecture, Google Cloud Big Data Analytics
