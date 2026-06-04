"""
Real-Time Sales Performance Analytics Dashboard for Retail Businesses
Script 01: Generate Realistic Sample Dataset
Author: GURRAM MAHADEV KISHAN | UID: CUOL725165
Course: 23ONMCR-753 Major Project | Chandigarh University
"""

import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

# ── Config ────────────────────────────────────────────────────────────────
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

REGIONS      = ["North", "South", "East", "West", "Central"]
CATEGORIES   = ["Electronics", "Clothing", "Groceries", "Furniture", "Sports", "Cosmetics"]
PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "UPI", "Net Banking"]

PRODUCTS = {
    "Electronics": [
        ("Laptop",          45000, 38000),
        ("Smartphone",      22000, 17000),
        ("Tablet",          18000, 13000),
        ("Smart TV",        35000, 27000),
        ("Wireless Earbuds", 3500,  2200),
        ("Router",           2800,  1900),
    ],
    "Clothing": [
        ("Men's T-Shirt",     799,   350),
        ("Women's Kurti",    1299,   600),
        ("Denim Jeans",      2499,  1200),
        ("Winter Jacket",    3999,  2200),
        ("Formal Shirt",     1799,   900),
        ("Saree",            4999,  2500),
    ],
    "Groceries": [
        ("Basmati Rice 5kg", 450,   310),
        ("Cooking Oil 1L",   180,   130),
        ("Whole Wheat Flour 5kg", 250, 190),
        ("Sugar 1kg",         55,    42),
        ("Pulses 1kg",        140,   100),
        ("Tea Powder 500g",   210,   155),
    ],
    "Furniture": [
        ("Office Chair",    8500,   5800),
        ("Wooden Desk",    12000,   8500),
        ("Bookshelf",       6500,   4500),
        ("Sofa Set",       35000,  24000),
        ("Dining Table",   22000,  15000),
        ("Wardrobe",       18000,  12000),
    ],
    "Sports": [
        ("Cricket Bat",     2999,  1800),
        ("Yoga Mat",         899,   550),
        ("Dumbbells Set",   3499,  2200),
        ("Running Shoes",   4999,  3200),
        ("Badminton Racket",1499,   900),
        ("Cycle Helmet",    1299,   800),
    ],
    "Cosmetics": [
        ("Face Wash 100ml",  299,   160),
        ("Moisturiser 50g",  499,   280),
        ("Lipstick",         599,   310),
        ("Foundation",       899,   520),
        ("Hair Serum 100ml", 699,   400),
        ("Sunscreen SPF50",  450,   270),
    ],
}

CUSTOMER_NAMES = [
    "Rahul Sharma","Priya Patel","Amit Kumar","Sneha Gupta","Vijay Singh",
    "Anita Verma","Rohan Mehta","Kavita Joshi","Sanjay Yadav","Pooja Nair",
    "Arjun Reddy","Divya Iyer","Kiran Bose","Meera Das","Suresh Pillai",
    "Lakshmi Rao","Deepak Tiwari","Asha Pandey","Ravi Chandra","Sunita Mishra",
    "Harish Agarwal","Rekha Srivastava","Nikhil Dubey","Pallavi Shah","Arun Patil",
    "Geeta Bhatt","Mohit Saxena","Swati Kapoor","Rajesh Malhotra","Nisha Trivedi",
]

CITIES = {
    "North":   ["Delhi", "Chandigarh", "Lucknow", "Jaipur", "Amritsar"],
    "South":   ["Bangalore", "Chennai", "Hyderabad", "Kochi", "Mysore"],
    "East":    ["Kolkata", "Bhubaneswar", "Patna", "Guwahati", "Ranchi"],
    "West":    ["Mumbai", "Pune", "Ahmedabad", "Surat", "Nagpur"],
    "Central": ["Bhopal", "Indore", "Raipur", "Varanasi", "Gwalior"],
}

def seasonal_factor(dt):
    """Simulate higher sales in Oct-Dec (festive) and Apr-May (summer)."""
    m = dt.month
    if m in [10, 11, 12]: return random.uniform(1.3, 1.7)
    if m in [4, 5]:        return random.uniform(1.1, 1.4)
    if m in [1, 2]:        return random.uniform(0.7, 0.9)
    return random.uniform(0.9, 1.2)

def generate_transactions(n=5000):
    start = datetime(2023, 1, 1)
    end   = datetime(2024, 12, 31)
    delta = (end - start).days

    rows = []
    for i in range(1, n + 1):
        txn_date = start + timedelta(days=random.randint(0, delta))
        sf       = seasonal_factor(txn_date)

        region   = random.choice(REGIONS)
        city     = random.choice(CITIES[region])
        category = random.choice(CATEGORIES)
        product_name, base_price, base_cost = random.choice(PRODUCTS[category])

        qty = max(1, int(random.gauss(2, 1) * sf))
        unit_price = round(base_price * random.uniform(0.95, 1.10), 2)
        unit_cost  = round(base_cost  * random.uniform(0.97, 1.03), 2)
        discount   = round(random.choice([0, 0, 0, 5, 10, 15, 20]) / 100, 2)
        gross_amt  = round(unit_price * qty, 2)
        disc_amt   = round(gross_amt * discount, 2)
        net_amt    = round(gross_amt - disc_amt, 2)
        profit     = round((unit_price - unit_cost) * qty - disc_amt, 2)

        rows.append({
            "transaction_id":  f"TXN{i:06d}",
            "transaction_date": txn_date.strftime("%Y-%m-%d"),
            "customer_id":     f"CUST{random.randint(1, 500):04d}",
            "customer_name":   random.choice(CUSTOMER_NAMES),
            "region":          region,
            "city":            city,
            "category":        category,
            "product_name":    product_name,
            "quantity":        qty,
            "unit_price":      unit_price,
            "unit_cost":       unit_cost,
            "discount_pct":    discount,
            "gross_amount":    gross_amt,
            "discount_amount": disc_amt,
            "net_amount":      net_amt,
            "profit":          profit,
            "payment_method":  random.choice(PAYMENT_METHODS),
            "return_flag":     random.choices([0, 1], weights=[92, 8])[0],
        })
    return rows

def generate_customers():
    rows = []
    for i in range(1, 501):
        region = random.choice(REGIONS)
        rows.append({
            "customer_id":   f"CUST{i:04d}",
            "customer_name": random.choice(CUSTOMER_NAMES),
            "region":        region,
            "city":          random.choice(CITIES[region]),
            "signup_date":   (datetime(2022, 1, 1) + timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d"),
            "age_group":     random.choice(["18-25", "26-35", "36-45", "46-60", "60+"]),
            "gender":        random.choice(["Male", "Female"]),
        })
    return rows

def generate_products():
    rows = []
    pid = 1
    for cat, prods in PRODUCTS.items():
        for name, price, cost in prods:
            rows.append({
                "product_id":    f"PROD{pid:03d}",
                "product_name":  name,
                "category":      cat,
                "unit_price":    price,
                "unit_cost":     cost,
                "profit_margin": round((price - cost) / price * 100, 2),
            })
            pid += 1
    return rows

# ── Write CSVs ────────────────────────────────────────────────────────────
txns = generate_transactions(5000)
custs = generate_customers()
prods = generate_products()

def write_csv(filename, rows):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows → {path}")

write_csv("transactions.csv",  txns)
write_csv("customers.csv",     custs)
write_csv("products.csv",      prods)
print("\nDataset generation complete.")
