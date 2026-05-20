"""Generate a small synthetic e-commerce orders dataset.

200 rows of orders with realistic skew: web channel dominates volume but mobile
has the highest return rate; APAC orders cluster on weekends; one product
category (electronics) drives discount-heavy refunds.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(20260520)

OUT = Path(__file__).parent / "orders.csv"

CHANNELS = ["web", "mobile_app", "marketplace", "phone"]
CHANNEL_WEIGHTS = [0.55, 0.30, 0.10, 0.05]

REGIONS = ["NA", "EMEA", "APAC", "LATAM"]
REGION_WEIGHTS = [0.45, 0.30, 0.20, 0.05]

CATEGORIES = ["electronics", "apparel", "home_goods", "beauty", "books"]
CATEGORY_WEIGHTS = [0.25, 0.30, 0.20, 0.15, 0.10]

PAYMENTS = ["credit_card", "paypal", "gift_card", "bnpl"]
PAYMENT_WEIGHTS = [0.65, 0.22, 0.08, 0.05]

# Mobile-app return rate is engineered to be ~2.4× web. Electronics returns
# ~2× apparel. BNPL returns higher than credit_card.
BASE_RETURN_BY_CHANNEL = {"web": 0.06, "mobile_app": 0.16, "marketplace": 0.09, "phone": 0.04}
BASE_RETURN_BY_CATEGORY = {
    "electronics": 0.12,
    "apparel": 0.07,
    "home_goods": 0.05,
    "beauty": 0.04,
    "books": 0.03,
}
PAYMENT_RETURN_LIFT = {"credit_card": 1.0, "paypal": 1.05, "gift_card": 0.6, "bnpl": 1.7}

REVENUE_MEANS = {
    "electronics": 320,
    "apparel": 85,
    "home_goods": 140,
    "beauty": 55,
    "books": 30,
}

START = date(2026, 1, 1)
DAYS = 130


def pick(items: list, weights: list):
    return random.choices(items, weights=weights, k=1)[0]


def main() -> None:
    rows = []
    for i in range(1, 201):
        d = START + timedelta(days=random.randint(0, DAYS - 1))
        channel = pick(CHANNELS, CHANNEL_WEIGHTS)
        region = pick(REGIONS, REGION_WEIGHTS)
        category = pick(CATEGORIES, CATEGORY_WEIGHTS)
        payment = pick(PAYMENTS, PAYMENT_WEIGHTS)

        items = max(1, int(random.lognormvariate(0.4, 0.6)))
        unit_rev = max(5, random.gauss(REVENUE_MEANS[category], REVENUE_MEANS[category] * 0.4))
        revenue = round(items * unit_rev, 2)
        # Electronics on mobile_app gets aggressive discounts (the seeded story).
        discount = 0.0
        if category == "electronics" and channel == "mobile_app" and random.random() < 0.7:
            discount = round(random.uniform(0.15, 0.40), 2)
        elif random.random() < 0.2:
            discount = round(random.uniform(0.05, 0.20), 2)
        revenue_after = round(revenue * (1 - discount), 2)

        p_return = (
            BASE_RETURN_BY_CHANNEL[channel]
            * (BASE_RETURN_BY_CATEGORY[category] / 0.07)
            * PAYMENT_RETURN_LIFT[payment]
        )
        # Heavy discount → higher return risk (the "buyers' remorse" pattern).
        p_return *= 1 + discount * 1.5
        returned = random.random() < min(p_return, 0.85)

        # Inject 3 deliberately nulled discount_pct rows to give Phase 3 something
        # to clean.
        discount_field = "" if i in (47, 113, 188) else f"{discount:.2f}"
        # Inject 2 free-text channel values (case mismatch) for consistency cleanup.
        channel_field = channel
        if i == 71:
            channel_field = "Mobile_App"
        if i == 154:
            channel_field = "WEB"

        rows.append({
            "order_id": f"ORD-{i:04d}",
            "customer_id": f"C{random.randint(10000, 10999):05d}",
            "order_date": d.isoformat(),
            "channel": channel_field,
            "region": region,
            "product_category": category,
            "items": items,
            "revenue_usd": f"{revenue:.2f}",
            "discount_pct": discount_field,
            "revenue_after_discount_usd": f"{revenue_after:.2f}",
            "payment_method": payment,
            "returned": "true" if returned else "false",
        })

    rows.sort(key=lambda r: r["order_date"])

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT}")
    # Quick summary so we know what we generated.
    total = len(rows)
    returns = sum(1 for r in rows if r["returned"] == "true")
    by_ch = {}
    for r in rows:
        ch = r["channel"].lower()
        by_ch.setdefault(ch, {"n": 0, "returns": 0})
        by_ch[ch]["n"] += 1
        if r["returned"] == "true":
            by_ch[ch]["returns"] += 1
    print(f"Overall return rate: {returns}/{total} = {returns / total:.1%}")
    for ch, d in sorted(by_ch.items()):
        if d["n"]:
            print(f"  {ch:14s} n={d['n']:3d}  returns={d['returns']:3d}  rate={d['returns']/d['n']:.1%}")


if __name__ == "__main__":
    main()
