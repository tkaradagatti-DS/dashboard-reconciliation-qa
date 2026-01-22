# Dashboard Refresh QA Checklist

Use this checklist after refreshing a dashboard or updating an ETL pipeline.

## 1) Scope + refresh window
- Confirm refresh period (e.g., last 30 days / full history).
- Confirm timezone used (UTC vs local).
- Confirm whether late-arriving data is expected.

## 2) Totals reconciliation
- Compare key totals (revenue, orders, headcount, etc.) between:
  - source system
  - staging tables
  - dashboard model tables
- Set tolerances (e.g., ±0.5% for revenue).

## 3) Dimensional checks
- Verify mappings (region, product, channel).
- Check for “Unknown / Null” categories and quantify them.
- Confirm row counts and distinct keys (e.g., customer_id, transaction_id).

## 4) Duplicate and missing data checks
- Check duplicates in fact tables (duplicate transaction_id).
- Check missing foreign keys (facts that don’t join to dimensions).
- Check missing date values.

## 5) KPI logic confirmation
- Ensure KPI definitions match the agreed spec.
- Validate a few sample calculations manually (spot checks).

## 6) Sign-off output
- Save reconciliation report (CSV/Excel).
- Summarise: pass/fail + top issues + actions.

## Common mismatch causes
- Filters applied in dashboard but not applied in source query
- Incorrect joins (many-to-many causing duplication)
- Missing mappings (e.g., new regions/products not in lookup tables)
- Partial refresh window / late arriving data
- Unintended deduplication or removal of rows
