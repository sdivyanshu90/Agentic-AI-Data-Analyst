"""AGENTIC condition: run the full 8-phase pipeline on the Telco churn data.

Same dataset description and business question handed to JUNIOR-A and
JUNIOR-B — the only difference here is the agentic orchestration.

Output: benchmark/results/agentic_report.md     (Phase 8 final report)
        benchmark/results/agentic_phase_outputs.json
        benchmark/results/agentic_meta.json
        benchmark/agentic_logs/ , benchmark/agentic_outputs/
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.orchestrator import DataAnalystOrchestrator  # noqa: E402

BENCH = REPO_ROOT / "benchmark"
RESULTS = BENCH / "results"


def main() -> int:
    description = (RESULTS / "data_description.txt").read_text()

    orch = DataAnalystOrchestrator(
        log_dir=str(BENCH / "agentic_logs"),
        output_dir=str(BENCH / "agentic_outputs"),
        verbose=True,
    )
    # Non-interactive: auto-confirm any row-loss / PARTIAL prompts.
    orch.user_confirm = lambda question: True

    print("AGENTIC: running full 8-phase pipeline (live Gemini calls)...", flush=True)
    t0 = time.time()
    result = orch.run(
        objective=(
            "Identify the top drivers of customer churn in our telecom subscriber "
            "base and recommend the two or three highest-leverage, cost-effective "
            "interventions to reduce it."
        ),
        data_source_description=description,
        stakeholder_type="Customer Retention / Marketing leadership",
        business_domain="telecom / subscription services",
        constraints={
            "time": "one analysis cycle",
            "tools": "Python + pandas",
            "privacy": "no PII beyond an opaque customerID",
        },
        success_looks_like=(
            "Retention leadership can name the top 2-3 measurable drivers of churn "
            "and commit to at least two concrete interventions."
        ),
        phases_to_run=[1, 2, 3, 4, 5, 6, 7, 8],
    )
    elapsed = time.time() - t0

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "agentic_phase_outputs.json").write_text(
        json.dumps(result.phase_outputs, indent=2, default=str)
    )
    if result.final_report:
        (RESULTS / "agentic_report.md").write_text(result.final_report)

    meta = {
        "condition": "AGENTIC (8-phase pipeline)",
        "elapsed_seconds": round(elapsed, 1),
        "blocked_phase": result.blocked_phase,
        "phases_run": sorted(result.phase_outputs.keys()),
        "phase_status": {
            str(p): (o.get("status") if isinstance(o, dict) else "?")
            for p, o in sorted(result.phase_outputs.items())
        },
        "has_final_report": bool(result.final_report),
        "final_report_chars": len(result.final_report or ""),
    }
    (RESULTS / "agentic_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n=== AGENTIC PIPELINE FINISHED ===")
    print(f"Elapsed: {elapsed:.1f}s")
    if result.blocked_phase is not None:
        print(f"WARNING: blocked at phase {result.blocked_phase}")
    print(f"Phases run: {meta['phases_run']}")
    for p, s in meta["phase_status"].items():
        print(f"  Phase {p}: {s}")
    print(f"Final report: {meta['final_report_chars']} chars")
    return 0 if result.blocked_phase is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
