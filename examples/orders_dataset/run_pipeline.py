"""End-to-end live pipeline run against the synthetic orders dataset.

This invokes real Gemini calls for every phase. Outputs go to
`./logs/` (pipeline state log) and `./outputs/` (per-phase JSON + markdown).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.orchestrator import DataAnalystOrchestrator  # noqa: E402

DATASET_DIR = Path(__file__).resolve().parent
CSV_PATH = DATASET_DIR / "orders.csv"


def _data_source_description() -> str:
    return (
        "Local CSV file at examples/orders_dataset/orders.csv — 200 rows of synthetic "
        "e-commerce orders with the following 12 columns: "
        "order_id (string, unique), customer_id (string), order_date (ISO date, "
        "2026-01-01 to 2026-05-10), channel (web | mobile_app | marketplace | phone; "
        "two rows have case-mismatched values 'Mobile_App' and 'WEB'), "
        "region (NA | EMEA | APAC | LATAM), "
        "product_category (electronics | apparel | home_goods | beauty | books), "
        "items (integer), revenue_usd (decimal, pre-discount gross), "
        "discount_pct (decimal 0.00–0.40, with 3 NULL rows), "
        "revenue_after_discount_usd (decimal), "
        "payment_method (credit_card | paypal | gift_card | bnpl), "
        "returned (boolean as 'true'/'false'). "
        "Overall return rate ≈ 12.5%. No PII columns. "
        "The dataset is small enough to load entirely in pandas; SQL pseudocode is "
        "fine but a Python (pandas) extraction plan is preferred."
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Live pipeline run against orders.csv")
    p.add_argument(
        "--phases",
        default="1,2,3,4,5,6,7,8",
        help="Comma-separated phases to run (default: 1,2,3,4,5,6,7,8)",
    )
    p.add_argument("--quiet", action="store_true")
    p.add_argument(
        "--log-dir",
        default=str(DATASET_DIR / "logs"),
        help="Where to write pipeline_state_*.json",
    )
    p.add_argument(
        "--output-dir",
        default=str(DATASET_DIR / "outputs"),
        help="Where to write per-phase output JSON / markdown",
    )
    args = p.parse_args()
    phases = [int(x) for x in args.phases.split(",") if x.strip()]

    if not CSV_PATH.exists():
        print(f"Dataset not found at {CSV_PATH}. Run examples/orders_dataset/generate.py first.")
        return 2

    orch = DataAnalystOrchestrator(
        log_dir=args.log_dir,
        output_dir=args.output_dir,
        verbose=not args.quiet,
    )
    # Auto-confirm row-loss alerts so the live run is non-interactive.
    orch.user_confirm = lambda question: True

    result = orch.run(
        objective="Identify the top drivers of product returns in our e-commerce orders dataset, segment them by channel and category, and recommend the two highest-leverage interventions for Q3.",
        data_source_description=_data_source_description(),
        stakeholder_type="ops team",
        business_domain="e-commerce",
        constraints={
            "time": "1 week",
            "tools": "Python + pandas (preferred); SQL pseudocode acceptable",
            "privacy": "no PII in this dataset",
        },
        success_looks_like=(
            "Ops team can name the top 2 measurable drivers of returns and pick "
            "at least one operational intervention to ship in Q3."
        ),
        phases_to_run=phases,
    )

    print("\n=== PIPELINE FINISHED ===")
    if result.blocked_phase is not None:
        print(f"⚠ Pipeline blocked at phase {result.blocked_phase}")
        return 2
    print(f"Ran phases: {sorted(result.phase_outputs.keys())}")
    for phase, out in sorted(result.phase_outputs.items()):
        status = out.get("status", "?") if isinstance(out, dict) else "?"
        print(f"  Phase {phase}: status={status}")
    print(f"\nLogs: {args.log_dir}")
    print(f"Outputs: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
