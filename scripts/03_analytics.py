"""
Real-Time Sales Performance Analytics Dashboard for Retail Businesses
Script 03: Backend Analytics Module — KPIs, Trends, Forecasting
Author: GURRAM MAHADEV KISHAN | UID: CUOL725165
Course: 23ONMCR-753 Major Project | Chandigarh University

Run AFTER 02_etl_pipeline.py
"""

import sqlite3, csv, os, math
from collections import defaultdict

DB_PATH    = "data/retail_sales.db"
OUTPUT_DIR = "data/analytics"
os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()

def write_csv(filename, rows):
    if not rows: return
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  Saved {len(rows)} rows → {path}")

print("=== Analytics Module ===\n")

# ── 1. Overall KPIs ───────────────────────────
print("[1] Overall KPIs")
cur.execute("""
SELECT
    COUNT(*)                           AS total_transactions,
    COUNT(DISTINCT customer_id)        AS unique_customers,
    SUM(quantity)                      AS total_units_sold,
    ROUND(SUM(gross_amount),2)         AS gross_revenue,
    ROUND(SUM(discount_amount),2)      AS total_discount_given,
    ROUND(SUM(net_amount),2)           AS net_revenue,
    ROUND(SUM(profit),2)               AS total_profit,
    ROUND(AVG(profit_margin_pct),2)    AS avg_profit_margin,
    ROUND(SUM(net_amount)*1.0/COUNT(*),2) AS avg_order_value,
    SUM(return_flag)                   AS total_returns,
    ROUND(SUM(return_flag)*100.0/COUNT(*),2) AS return_rate_pct
FROM transactions
""")
row = dict(cur.fetchone())
for k, v in row.items():
    print(f"  {k:<35}: {v:,}" if isinstance(v, (int, float)) else f"  {k:<35}: {v}")
write_csv("kpi_summary.csv", [row])

# ── 2. Monthly Revenue Trend ──────────────────
print("\n[2] Monthly Revenue Trend")
cur.execute("""
SELECT year, month, month_name,
       SUM(quantity)          AS units_sold,
       ROUND(SUM(net_amount),2) AS net_revenue,
       ROUND(SUM(profit),2)   AS profit,
       ROUND(AVG(profit_margin_pct),2) AS avg_margin
FROM transactions WHERE return_flag=0
GROUP BY year, month ORDER BY year, month
""")
monthly = [dict(r) for r in cur.fetchall()]
write_csv("monthly_trend.csv", monthly)
print(f"  {len(monthly)} monthly records extracted")

# ── 3. Category Performance ───────────────────
print("\n[3] Category Performance")
cur.execute("""
SELECT category,
       COUNT(*) AS orders, SUM(quantity) AS units,
       ROUND(SUM(net_amount),2) AS net_revenue,
       ROUND(SUM(profit),2) AS profit,
       ROUND(AVG(profit_margin_pct),2) AS avg_margin,
       ROUND(SUM(net_amount)*100.0/(SELECT SUM(net_amount) FROM transactions WHERE return_flag=0),2) AS revenue_share_pct
FROM transactions WHERE return_flag=0
GROUP BY category ORDER BY net_revenue DESC
""")
cat = [dict(r) for r in cur.fetchall()]
write_csv("category_performance.csv", cat)
for c in cat:
    print(f"  {c['category']:<14} Rev: ₹{c['net_revenue']:>12,.2f}  Margin: {c['avg_margin']}%")

# ── 4. Region Performance ─────────────────────
print("\n[4] Region Performance")
cur.execute("""
SELECT region,
       COUNT(DISTINCT customer_id) AS unique_customers,
       COUNT(*) AS orders,
       ROUND(SUM(net_amount),2) AS net_revenue,
       ROUND(SUM(profit),2) AS profit,
       ROUND(AVG(profit_margin_pct),2) AS avg_margin
FROM transactions WHERE return_flag=0
GROUP BY region ORDER BY net_revenue DESC
""")
reg = [dict(r) for r in cur.fetchall()]
write_csv("region_performance.csv", reg)
for r in reg:
    print(f"  {r['region']:<10} Rev: ₹{r['net_revenue']:>12,.2f}  Customers: {r['unique_customers']}")

# ── 5. Top 10 Products ────────────────────────
print("\n[5] Top 10 Products by Revenue")
cur.execute("""
SELECT product_name, category,
       SUM(quantity) AS units_sold,
       ROUND(SUM(net_amount),2) AS net_revenue,
       ROUND(SUM(profit),2) AS profit,
       ROUND(AVG(profit_margin_pct),2) AS avg_margin
FROM transactions WHERE return_flag=0
GROUP BY product_name ORDER BY net_revenue DESC LIMIT 10
""")
top_prods = [dict(r) for r in cur.fetchall()]
write_csv("top_products.csv", top_prods)
for i, p in enumerate(top_prods, 1):
    print(f"  {i:2}. {p['product_name']:<25} ₹{p['net_revenue']:>12,.2f}")

# ── 6. Payment Method Distribution ───────────────────────────────
print("\n[6] Payment Method Distribution")
cur.execute("""
SELECT payment_method,
       COUNT(*) AS transactions,
       ROUND(SUM(net_amount),2) AS total_value,
       ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM transactions),2) AS pct
FROM transactions GROUP BY payment_method ORDER BY transactions DESC
""")
pay = [dict(r) for r in cur.fetchall()]
write_csv("payment_methods.csv", pay)

# ── 7. Seasonality (Quarter) ───────────────────────────────────
print("\n[7] Quarterly Seasonality")
cur.execute("""
SELECT quarter, year,
       COUNT(*) AS orders,
       ROUND(SUM(net_amount),2) AS net_revenue,
       ROUND(SUM(profit),2) AS profit
FROM transactions WHERE return_flag=0
GROUP BY year, quarter ORDER BY year, quarter
""")
quarterly = [dict(r) for r in cur.fetchall()]
write_csv("quarterly_seasonality.csv", quarterly)
for q in quarterly:
    print(f"  {q['year']} {q['quarter']}  Rev: ₹{q['net_revenue']:>12,.2f}")

# ── 8. Simple Linear Trend Forecast (next 6 months) ──────────────────────
print("\n[8] Revenue Forecast (Linear Trend — next 6 months)")

# Use monthly data for 2024 to project 2025 H1
months_2024 = [(r["month"], r["net_revenue"]) for r in monthly if r["year"] == 2024]
n = len(months_2024)
if n >= 6:
    xs = list(range(1, n + 1))
    ys = [m[1] for m in months_2024]
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    b1 = sum((xs[i]-x_mean)*(ys[i]-y_mean) for i in range(n)) / sum((x-x_mean)**2 for x in xs)
    b0 = y_mean - b1 * x_mean

    forecast_rows = []
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for step in range(1, 7):
        xi = n + step
        pred = round(b0 + b1 * xi, 2)
        m_idx = (months_2024[-1][0] - 1 + step) % 12
        forecast_rows.append({
            "forecast_step": step,
            "month_name": month_names[m_idx],
            "year": 2025,
            "predicted_revenue": max(0, pred),
        })
        print(f"  2025-{month_names[m_idx]}: ₹{max(0,pred):>12,.2f}")
    write_csv("revenue_forecast.csv", forecast_rows)

# ── 9. Customer Segmentation (RFM proxy) ─────────────────────────────────
print("\n[9] Customer Segment Summary (RFM Proxy)")
cur.execute("""
SELECT customer_id,
       COUNT(*) AS frequency,
       ROUND(SUM(net_amount),2) AS monetary,
       MAX(transaction_date) AS last_purchase
FROM transactions WHERE return_flag=0
GROUP BY customer_id
""")
cust_data = [dict(r) for r in cur.fetchall()]

# Simple segmentation by monetary quartile
cust_data.sort(key=lambda x: x["monetary"], reverse=True)
n = len(cust_data)
for i, c in enumerate(cust_data):
    pct = i / n
    if pct < 0.25:   c["segment"] = "Champion"
    elif pct < 0.50: c["segment"] = "Loyal"
    elif pct < 0.75: c["segment"] = "Potential"
    else:            c["segment"] = "At Risk"

write_csv("customer_segments.csv", cust_data)
seg_count = defaultdict(int)
for c in cust_data:
    seg_count[c["segment"]] += 1
for seg, cnt in seg_count.items():
    print(f"  {seg:<12}: {cnt} customers")

conn.close()
print("\nAll analytics outputs saved to:", OUTPUT_DIR)
