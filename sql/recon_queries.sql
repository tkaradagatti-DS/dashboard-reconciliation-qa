-- recon_queries.sql
-- Example SQL reconciliation queries (SQLite style)

-- Source totals (month/region)
SELECT
  substr(transaction_date, 1, 7) AS month,
  region,
  SUM(revenue) AS source_revenue,
  COUNT(*) AS source_orders
FROM source_transactions
GROUP BY month, region;

-- Dashboard totals (month/region)
SELECT
  substr(month, 1, 7) AS month,
  region,
  SUM(revenue) AS dashboard_revenue,
  SUM(orders) AS dashboard_orders
FROM dashboard_extract
GROUP BY month, region;

-- Join and compare
SELECT
  s.month,
  s.region,
  s.source_revenue,
  d.dashboard_revenue,
  (d.dashboard_revenue - s.source_revenue) AS revenue_diff,
  100.0 * (d.dashboard_revenue - s.source_revenue) / s.source_revenue AS revenue_diff_pct,
  s.source_orders,
  d.dashboard_orders,
  (d.dashboard_orders - s.source_orders) AS orders_diff
FROM (
  SELECT substr(transaction_date, 1, 7) AS month, region, SUM(revenue) AS source_revenue, COUNT(*) AS source_orders
  FROM source_transactions
  GROUP BY month, region
) s
LEFT JOIN (
  SELECT substr(month, 1, 7) AS month, region, SUM(revenue) AS dashboard_revenue, SUM(orders) AS dashboard_orders
  FROM dashboard_extract
  GROUP BY month, region
) d
ON s.month = d.month AND s.region = d.region;
