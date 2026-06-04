"""
Real-Time Sales Performance Analytics Dashboard for Retail Businesses
Script 02: ETL Process — Extract, Transform, Load
Author: GURRAM MAHADEV KISHAN | UID: CUOL725165
Course: 23ONMCR-753 Major Project | Chandigarh University

Run AFTER 01_generate_dataset.py
"""

import csv, os, sqlite3
from datetime import datetime

INPUT_DIR  = "data"
OUTPUT_DIR = "data"
DB_PATH    = "data/retail_sales.db"

# ──────────────────────────────────────────────
# STEP 1 — EXTRACT
# ──────────────────────────────────────────────
def read_csv(filename):
    path = os.path.join(INPUT_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

print("=== ETL Pipeline: Real-Time Sales Analytics ===\n")
print("[EXTRACT] Reading raw CSV files...")
raw_txns  = read_csv("transactions.csv")
raw_custs = read_csv("customers.csv")
raw_prods = read_csv("products.csv")
print(f"  Transactions : {len(raw_txns):,} records")
print(f"  Customers    : {len(raw_custs):,} records")
print(f"  Products     : {len(raw_prods):,} records")

# ──────────────────────────────────────────────
# STEP 2 — TRANSFORM
# ──────────────────────────────────────────────
print("\n[TRANSFORM] Cleaning and enriching data...")

errors_found = 0

def clean_transactions(rows):
    global errors_found
    cleaned = []
    seen_ids = set()
    for r in rows:
        # Remove duplicates
        if r["transaction_id"] in seen_ids:
            errors_found += 1
            continue
        seen_ids.add(r["transaction_id"])

        # Validate numeric fields
        try:
            qty      = int(r["quantity"])
            net_amt  = float(r["net_amount"])
            profit   = float(r["profit"])
            discount = float(r["discount_pct"])
        except ValueError:
            errors_found += 1
            continue

        # Drop negative qty or amount (data quality rule)
        if qty <= 0 or net_amt < 0:
            errors_found += 1
            continue

        # Parse date → add year/month/quarter/weekday columns
        dt = datetime.strptime(r["transaction_date"], "%Y-%m-%d")
        r["year"]      = dt.year
        r["month"]     = dt.month
        r["month_name"]= dt.strftime("%b")
        r["quarter"]   = f"Q{(dt.month - 1) // 3 + 1}"
        r["weekday"]   = dt.strftime("%A")
        r["is_weekend"]= 1 if dt.weekday() >= 5 else 0

        # Derived KPIs
        r["profit_margin_pct"] = round(profit / net_amt * 100, 2) if net_amt > 0 else 0
        r["is_return"]         = int(r["return_flag"])

        # Normalize text
        r["region"]   = r["region"].strip().title()
        r["category"] = r["category"].strip().title()

        cleaned.append(r)
    return cleaned

cleaned_txns = clean_transactions(raw_txns)
print(f"  Transactions after cleaning : {len(cleaned_txns):,} (removed {errors_found} bad rows)")

# ──────────────────────────────────────────────
# STEP 3 — LOAD into SQLite
# ──────────────────────────────────────────────
print("\n[LOAD] Creating SQLite database and loading tables...")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()
cur.executescript("PRAGMA journal_mode=WAL;")

# ── Table: products ───────────────────────────
cur.execute("DROP TABLE IF EXISTS products")
cur.execute("""
CREATE TABLE products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    unit_price      REAL,
    unit_cost       REAL,
    profit_margin   REAL
)""")
for r in raw_prods:
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?)",
        (r["product_id"], r["product_name"], r["category"],
         float(r["unit_price"]), float(r["unit_cost"]), float(r["profit_margin"])))
print(f"  Loaded {len(raw_prods)} rows into 'products'")

# ── Table: customers ──────────────────────────
cur.execute("DROP TABLE IF EXISTS customers")
cur.execute("""
CREATE TABLE customers (
    customer_id   TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region        TEXT,
    city          TEXT,
    signup_date   TEXT,
    age_group     TEXT,
    gender        TEXT
)""")
for r in raw_custs:
    cur.execute("INSERT INTO customers VALUES (?,?,?,?,?,?,?)",
        (r["customer_id"], r["customer_name"], r["region"],
         r["city"], r["signup_date"], r["age_group"], r["gender"]))
print(f"  Loaded {len(raw_custs)} rows into 'customers'")

# ── Table: transactions ───────────────────────
cur.execute("DROP TABLE IF EXISTS transactions")
cur.execute("""
CREATE TABLE transactions (
    transaction_id   TEXT PRIMARY KEY,
    transaction_date TEXT,
    year             INTEGER,
    month            INTEGER,
    month_name       TEXT,
    quarter          TEXT,
    weekday          TEXT,
    is_weekend       INTEGER,
    customer_id      TEXT,
    customer_name    TEXT,
    region           TEXT,
    city             TEXT,
    category         TEXT,
    product_name     TEXT,
    quantity         INTEGER,
    unit_price       REAL,
    unit_cost        REAL,
    discount_pct     REAL,
    gross_amount     REAL,
    discount_amount  REAL,
    net_amount       REAL,
    profit           REAL,
    profit_margin_pct REAL,
    payment_method   TEXT,
    return_flag      INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)""")
for r in cleaned_txns:
    cur.execute("""INSERT INTO transactions VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        r["transaction_id"], r["transaction_date"],
        int(r["year"]), int(r["month"]), r["month_name"],
        r["quarter"], r["weekday"], int(r["is_weekend"]),
        r["customer_id"], r["customer_name"],
        r["region"], r["city"], r["category"], r["product_name"],
        int(r["quantity"]), float(r["unit_price"]), float(r["unit_cost"]),
        float(r["discount_pct"]), float(r["gross_amount"]),
        float(r["discount_amount"]), float(r["net_amount"]),
        float(r["profit"]), float(r["profit_margin_pct"]),
        r["payment_method"], int(r["return_flag"])
    ))
print(f"  Loaded {len(cleaned_txns):,} rows into 'transactions'")

# ── View: monthly_summary ─────────────────────
cur.execute("DROP VIEW IF EXISTS monthly_summary")
cur.execute("""
CREATE VIEW monthly_summary AS
SELECT  year, month, month_name,
        COUNT(*)                          AS total_transactions,
        SUM(quantity)                     AS total_units_sold,
        ROUND(SUM(gross_amount),2)        AS gross_revenue,
        ROUND(SUM(discount_amount),2)     AS total_discount,
        ROUND(SUM(net_amount),2)          AS net_revenue,
        ROUND(SUM(profit),2)              AS total_profit,
        ROUND(AVG(profit_margin_pct),2)   AS avg_profit_margin
FROM    transactions
WHERE   return_flag = 0
GROUP BY year, month
ORDER BY year, month
""")

# ── View: category_summary ────────────────────
cur.execute("DROP VIEW IF EXISTS category_summary")
cur.execute("""
CREATE VIEW category_summary AS
SELECT  category,
        COUNT(*)                       AS total_orders,
        SUM(quantity)                  AS total_units,
        ROUND(SUM(net_amount),2)       AS net_revenue,
        ROUND(SUM(profit),2)           AS total_profit,
        ROUND(AVG(profit_margin_pct),2) AS avg_margin
FROM    transactions
WHERE   return_flag = 0
GROUP BY category
ORDER BY net_revenue DESC
""")

# ── View: region_summary ──────────────────────
cur.execute("DROP VIEW IF EXISTS region_summary")
cur.execute("""
CREATE VIEW region_summary AS
SELECT  region,
        COUNT(DISTINCT customer_id)    AS unique_customers,
        COUNT(*)                       AS total_orders,
        ROUND(SUM(net_amount),2)       AS net_revenue,
        ROUND(SUM(profit),2)           AS total_profit,
        ROUND(AVG(profit_margin_pct),2) AS avg_margin
FROM    transactions
WHERE   return_flag = 0
GROUP BY region
ORDER BY net_revenue DESC
""")

conn.commit()
conn.close()

print("\n[VALIDATE] Quick summary from DB:")
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()
for tbl in ["transactions", "customers", "products"]:
    cur.execute(f"SELECT COUNT(*) FROM {tbl}")
    print(f"  {tbl}: {cur.fetchone()[0]:,} rows")

cur.execute("SELECT SUM(net_amount), SUM(profit) FROM transactions WHERE return_flag=0")
rev, profit = cur.fetchone()
print(f"\n  Total Net Revenue : ₹{rev:,.2f}")
print(f"  Total Profit      : ₹{profit:,.2f}")
print(f"  Overall Margin    : {profit/rev*100:.1f}%")
conn.close()

print("\nETL Pipeline complete. DB saved to:", DB_PATH)
