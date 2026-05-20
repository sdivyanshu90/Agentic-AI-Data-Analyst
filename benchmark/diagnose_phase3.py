"""Diagnostic: run ONLY Phase 3 against the real dataset.

Reuses the Phase 1 & 2 outputs already persisted from the v2 run, so we can
inspect Phase 3's behaviour (does it execute code? what validation_suite does
it produce?) without re-running the whole pipeline.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import agents.phase3_cleaning as phase3  # noqa: E402
from core.context_packet import build_context_packet  # noqa: E402

BENCH = REPO_ROOT / "benchmark"
DATASET = BENCH / "data" / "Telco-Customer-Churn.csv"
V2_OUT = BENCH / "agentic_v2_outputs"


def main() -> int:
    p1 = sorted(glob.glob(str(V2_OUT / "phase1_output_*.json")))[-1]
    p2 = sorted(glob.glob(str(V2_OUT / "phase2_output_*.json")))[-1]
    phase1 = json.load(open(p1))
    phase2 = json.load(open(p2))

    mission_brief = {
        "objective": "Identify the top drivers of customer churn and recommend interventions.",
        "business_domain": "telecom / subscription services",
        "stakeholder_type": "Customer Retention / Marketing leadership",
        "data_source_description": (BENCH / "results" / "data_description.txt").read_text(),
        "constraints": {"tools": "Python + pandas"},
        "success_looks_like": "Top 2-3 drivers named.",
        "assumptions": [],
        "dataset_path": str(DATASET),
    }
    packet = build_context_packet(
        mission_brief=mission_brief,
        prior_outputs={1: phase1, 2: phase2},
        pipeline_state={"phases": []},
    )

    print("Running Phase 3 against the real dataset...", flush=True)
    result = phase3.run(packet)

    print(f"\n=== code_calls: {result.code_calls} ===")
    for i, t in enumerate(result.transcript or [], 1):
        print(f"--- exec {i} ok={t['ok']} ---")
        print("CODE:", (t["code"] or "")[:400])
        print("OUT :", (t["output"] or t["error"] or "")[:400])
    out = result.output
    print(f"\n=== status: {out.get('status')} ===")
    print("validation_suite:", json.dumps(out.get("validation_suite"), indent=2))
    if "parse_error" in out:
        print("parse_error:", out["parse_error"])
    (BENCH / "results" / "diagnose_phase3_output.json").write_text(
        json.dumps(out, indent=2, default=str)
    )
    print("\nFull output -> benchmark/results/diagnose_phase3_output.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
