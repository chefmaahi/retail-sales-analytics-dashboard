-- ============================================================
-- Real-Time Sales Performance Analytics Dashboard
-- Script 04: MySQL Schema & Analytical Queries (CORRECTED)
-- Author : GURRAM MAHADEV KISHAN | UID: CUOL725165
-- Course : 23ONMCR-753 Major Project | Chandigarh University
-- ============================================================

-- ── Create and use database ─────────────────────────────────
CREATE DATABASE IF NOT EXISTS retail_sales_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE retail_sales_db;

-- ── Table: products ─────────────────────────────────────────
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    product_id       VARCHAR(10)    PRIMARY KEY,
    product_name     VARCHAR(100)   NOT NULL,
    category         VARCHAR(50)    NOT NULL,
    unit_price       DECIMAL(10,2),
    unit_cost        DECIMAL(10,2),
    profit_margin    DECIMAL(5,2),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ── Table: customers ────────────────────────────────────────
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id    VARCHAR(10)   PRIMARY KEY,
    customer_name  VARCHAR(100)  NOT NULL,
    region         VARCHAR(20),
    city           VARCHAR(50),
    signup_date    DATE,
    age_group      VARCHAR(10),
    gender         VARCHAR(10)
) ENGINE=InnoDB;

-- ── Table: transactions ─────────────────────────────────────
-- FIX 1: Drop order matters — transactions references both customers & products
DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    transaction_id    VARCHAR(12)   PRIMARY KEY,
    transaction_date  DATE          NOT NULL,
    year              SMALLINT,
    month             TINYINT,
    month_name        VARCHAR(3),
    quarter           VARCHAR(2),
    weekday           VARCHAR(10),
    -- FIX 2: BOOLEAN instead of deprecated TINYINT(1) display width
    is_weekend        BOOLEAN       DEFAULT FALSE,
    customer_id       VARCHAR(10),
    customer_name     VARCHAR(100),
    region            VARCHAR(20),
    city              VARCHAR(50),
    -- FIX 3: Added product_id to properly link the products table via FK
    product_id        VARCHAR(10),
    category          VARCHAR(50),
    product_name      VARCHAR(100),
    quantity          INT           NOT NULL,
    unit_price        DECIMAL(10,2),
    unit_cost         DECIMAL(10,2),
    discount_pct      DECIMAL(4,2),
    gross_amount      DECIMAL(14,2),
    discount_amount   DECIMAL(14,2),
    net_amount        DECIMAL(14,2),
    profit            DECIMAL(14,2),
    profit_margin_pct DECIMAL(5,2),
    payment_method    VARCHAR(20),
    -- FIX 2: BOOLEAN instead of deprecated TINYINT(1) display width
    return_flag       BOOLEAN       DEFAULT FALSE,
    -- FIX 1: FK to customers
    FOREIGN KEY (customer_id)  REFERENCES customers(customer_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    -- FIX 3: FK to products (now possible because product_id column exists)
    FOREIGN KEY (product_id)   REFERENCES products(product_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- ── Indexes for dashboard performance ───────────────────────
CREATE INDEX idx_txn_date      ON transactions(transaction_date);
CREATE INDEX idx_txn_region    ON transactions(region);
CREATE INDEX idx_txn_category  ON transactions(category);
CREATE INDEX idx_txn_year_qtr  ON transactions(year, quarter);
CREATE INDEX idx_txn_product   ON transactions(product_name);
-- FIX 3: Added index on product_id for FK join performance
CREATE INDEX idx_txn_product_id ON transactions(product_id);
CREATE INDEX idx_txn_cust      ON transactions(customer_id);

-- ============================================================
-- ANALYTICAL QUERIES (for Power BI / reporting)
-- ============================================================

-- Q1: Overall KPI Dashboard Card Values
SELECT
    COUNT(*)                                    AS total_transactions,
    COUNT(DISTINCT customer_id)                 AS unique_customers,
    SUM(quantity)                               AS total_units_sold,
    ROUND(SUM(gross_amount), 2)                 AS gross_revenue,
    ROUND(SUM(net_amount), 2)                   AS net_revenue,
    ROUND(SUM(profit), 2)                       AS total_profit,
    ROUND(AVG(profit_margin_pct), 2)            AS avg_profit_margin_pct,
    ROUND(SUM(net_amount) / COUNT(*), 2)        AS avg_order_value,
    ROUND(SUM(return_flag)*100.0/COUNT(*), 2)   AS return_rate_pct
FROM transactions;

-- Q2: Monthly Revenue & Profit Trend
SELECT  year, month, month_name,
        SUM(quantity)                   AS units_sold,
        ROUND(SUM(gross_amount), 2)     AS gross_revenue,
        ROUND(SUM(net_amount), 2)       AS net_revenue,
        ROUND(SUM(profit), 2)           AS total_profit,
        ROUND(AVG(profit_margin_pct),2) AS avg_margin
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY year, month, month_name
ORDER BY year, month;

-- Q3: Category-wise Revenue Share
SELECT  category,
        COUNT(*)                        AS total_orders,
        SUM(quantity)                   AS units_sold,
        ROUND(SUM(net_amount), 2)       AS net_revenue,
        ROUND(SUM(profit), 2)           AS profit,
        ROUND(AVG(profit_margin_pct),2) AS avg_margin,
        ROUND(SUM(net_amount)*100.0/(
            SELECT SUM(net_amount)
            FROM transactions
            WHERE return_flag = FALSE
        ), 2)                           AS revenue_share_pct
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY category
ORDER BY net_revenue DESC;

-- Q4: Region Performance
SELECT  region,
        COUNT(DISTINCT customer_id)     AS unique_customers,
        COUNT(*)                        AS orders,
        ROUND(SUM(net_amount), 2)       AS net_revenue,
        ROUND(SUM(profit), 2)           AS profit,
        ROUND(AVG(profit_margin_pct),2) AS avg_margin
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY region
ORDER BY net_revenue DESC;

-- Q5: Top 10 Products
SELECT  product_name, category,
        SUM(quantity)             AS units_sold,
        ROUND(SUM(net_amount),2)  AS net_revenue,
        ROUND(SUM(profit),2)      AS profit
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY product_name, category
ORDER BY net_revenue DESC
LIMIT 10;

-- Q6: Quarterly Seasonality (Year-over-Year)
SELECT  year, quarter,
        ROUND(SUM(net_amount),2) AS net_revenue,
        ROUND(SUM(profit),2)     AS profit,
        COUNT(*)                 AS orders
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY year, quarter
ORDER BY year, quarter;

-- Q7: Payment Method Distribution
-- FIX 4: Denominator now excludes returned transactions for consistent percentages
SELECT  payment_method,
        COUNT(*)                  AS transactions,
        ROUND(SUM(net_amount),2)  AS total_value,
        ROUND(COUNT(*)*100.0/(
            SELECT COUNT(*) FROM transactions WHERE return_flag = FALSE
        ), 2)                     AS pct
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY payment_method
ORDER BY transactions DESC;

-- Q8: Customer RFM Analysis
-- FIX 5: Anchored recency to dataset end date (2024-12-31) instead of CURDATE()
--        so results stay consistent regardless of when the query is run.
SELECT  customer_id,
        COUNT(*)                   AS frequency,
        ROUND(SUM(net_amount), 2)  AS monetary,
        DATEDIFF('2024-12-31', MAX(transaction_date)) AS recency_days
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY customer_id
ORDER BY monetary DESC
LIMIT 20;

-- Q9: Return Rate by Category
SELECT  category,
        COUNT(*)                                   AS total_orders,
        SUM(return_flag)                           AS returns,
        ROUND(SUM(return_flag)*100.0/COUNT(*), 2)  AS return_rate_pct
FROM    transactions
GROUP BY category
ORDER BY return_rate_pct DESC;

-- Q10: Daily Sales (for time-series chart in Power BI)
SELECT  transaction_date,
        COUNT(*)                  AS orders,
        SUM(quantity)             AS units,
        ROUND(SUM(net_amount),2)  AS net_revenue,
        ROUND(SUM(profit),2)      AS profit
FROM    transactions
WHERE   return_flag = FALSE
GROUP BY transaction_date
ORDER BY transaction_date;
