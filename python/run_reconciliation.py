"""
run_reconciliation.py

Compares aggregated metrics from a source transactions file to a dashboard extract and flags mismatches.

Run:
  pip install -r python/requirements.txt
  python python/run_reconciliation.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
IMG = ROOT / "images"

OUT.mkdir(parents=True, exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)

SOURCE_FILE = DATA / "source_transactions.csv"
DASH_FILE = DATA / "dashboard_extract.csv"

# tolerances
REV_TOL_PCT = 0.5
ORD_TOL = 1


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE_FILE}")
    if not DASH_FILE.exists():
        raise FileNotFoundError(f"Missing dashboard extract file: {DASH_FILE}")

    source = pd.read_csv(SOURCE_FILE)
    dash = pd.read_csv(DASH_FILE)

    source["transaction_date"] = pd.to_datetime(source["transaction_date"])
    source["month"] = source["transaction_date"].dt.to_period("M").dt.to_timestamp()

    src_agg = (
        source.groupby(["month", "region"])
        .agg(source_revenue=("revenue", "sum"), source_orders=("transaction_id", "count"))
        .reset_index()
    )
    src_agg["source_revenue"] = src_agg["source_revenue"].round(2)

    dash["month"] = pd.to_datetime(dash["month"])
    dash = dash.rename(columns={"revenue": "dashboard_revenue", "orders": "dashboard_orders"})

    recon = src_agg.merge(dash, on=["month", "region"], how="left")

    recon["revenue_diff"] = (recon["dashboard_revenue"] - recon["source_revenue"]).round(2)
    recon["revenue_diff_pct"] = (recon["revenue_diff"] / recon["source_revenue"] * 100).round(2)
    recon["orders_diff"] = recon["dashboard_orders"] - recon["source_orders"]

    recon["revenue_pass"] = recon["revenue_diff_pct"].abs() <= REV_TOL_PCT
    recon["orders_pass"] = recon["orders_diff"].abs() <= ORD_TOL
    recon["overall_pass"] = recon["revenue_pass"] & recon["orders_pass"]

    summary = pd.DataFrame(
        [
            {
                "checks_run": len(recon),
                "checks_passed": int(recon["overall_pass"].sum()),
                "checks_failed": int((~recon["overall_pass"]).sum()),
                "failed_pct": round((~recon["overall_pass"]).mean() * 100, 2),
                "revenue_tolerance_pct": REV_TOL_PCT,
                "orders_tolerance_abs": ORD_TOL,
            }
        ]
    )

    recon.to_csv(OUT / "reconciliation_report.csv", index=False)
    summary.to_csv(OUT / "reconciliation_summary.csv", index=False)

    failed = recon[~recon["overall_pass"]].sort_values(["month", "region"])
    top_failed = failed.head(15)[
        [
            "month",
            "region",
            "source_revenue",
            "dashboard_revenue",
            "revenue_diff",
            "revenue_diff_pct",
            "source_orders",
            "dashboard_orders",
            "orders_diff",
        ]
    ]

    md_lines = [
        "# Reconciliation Summary",
        "",
        f"- Checks run: **{int(summary.loc[0, 'checks_run'])}**",
        f"- Failed checks: **{int(summary.loc[0, 'checks_failed'])}** ({summary.loc[0, 'failed_pct']}%)",
        f"- Tolerances: revenue ±{REV_TOL_PCT}% ; orders ±{ORD_TOL}",
        "",
        "## Sample failed checks (top 15)",
        "",
        top_failed.to_markdown(index=False),
    ]
    (OUT / "reconciliation_summary.md").write_text("\n".join(md_lines), encoding="utf-8")

    # Chart: failures by month
    fail_by_month = recon.groupby("month")["overall_pass"].apply(lambda s: (~s).sum()).reset_index(name="failed_checks")
    fig = plt.figure()
    plt.plot(fail_by_month["month"], fail_by_month["failed_checks"], marker="o")
    plt.title("Failed Reconciliation Checks by Month")
    plt.ylabel("Failed checks")
    plt.xlabel("Month")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(IMG / "failed_checks_by_month.png", dpi=160)
    plt.close(fig)

    # Heatmap-ish view of revenue % diffs
    pivot = recon.pivot_table(index="region", columns="month", values="revenue_diff_pct", aggfunc="mean")
    fig = plt.figure(figsize=(10, 3.2))
    plt.imshow(pivot.values, aspect="auto")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.xticks(range(len(pivot.columns)), [c.strftime("%Y-%m") for c in pivot.columns], rotation=90)
    plt.title("Revenue Difference % (Dashboard - Source)")
    plt.colorbar(label="Diff %")
    plt.tight_layout()
    fig.savefig(IMG / "revenue_diff_heatmap.png", dpi=160)
    plt.close(fig)

    # Workflow graphic
    fig = plt.figure(figsize=(9, 2.6))
    plt.axis("off")
    plt.text(0.02, 0.55, "Source Data\n(transactions)", fontsize=12, va="center")
    plt.text(0.28, 0.55, "→  Aggregate (Month/Region)", fontsize=12, va="center")
    plt.text(0.58, 0.55, "→  Compare to Dashboard Extract", fontsize=12, va="center")
    plt.text(0.88, 0.55, "→  Pass/Fail", fontsize=12, va="center", ha="right")
    plt.title("Workflow", y=0.95)
    plt.tight_layout()
    fig.savefig(IMG / "workflow.png", dpi=160)
    plt.close(fig)

    print("✅ Done. Outputs written to:", OUT)
    print("✅ Charts written to:", IMG)


if __name__ == "__main__":
    main()
