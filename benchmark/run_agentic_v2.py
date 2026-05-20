"""AGENTIC-v2 condition: the 8-phase pipeline WITH real code execution.

Identical to run_agentic.py except `dataset_path` is supplied — so phases 3-6
receive a `run_python` tool and compute their figures by executing pandas
against the real Telco CSV instead of reasoning from the prose description.

Output: benchmark/results/agentic_v2_report.md
        benchmark/results/agentic_v2_phase_outputs.json
        benchmark/results/agentic_v2_meta.json
        benchmark/results/agentic_v2_transcripts.json   (executed-code audit trail)
        benchmark/agentic_v2_logs/ , benchmark/agentic_v2_outputs/
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
DATASET = BENCH / "data" / "Telco-Customer-Churn.csv"


def main() -> int:
    description = (RESULTS / "data_description.txt").read_text()

    orch = DataAnalystOrchestrator(
        log_dir=str(BENCH / "agentic_v2_logs"),
        output_dir=str(BENCH / "agentic_v2_outputs"),
        verbose=True,
    )
    orch.user_confirm = lambda question: True

    print("AGENTIC-v2: running 8-phase pipeline WITH real code execution...", flush=True)
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
        dataset_path=str(DATASET),   # <-- the upgrade: real code execution
    )
    elapsed = time.time() - t0

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "agentic_v2_phase_outputs.json").write_text(
        json.dumps(result.phase_outputs, indent=2, default=str)
    )
    if result.final_report:
        (RESULTS / "agentic_v2_report.md").write_text(result.final_report)
    (RESULTS / "agentic_v2_transcripts.json").write_text(
        json.dumps(orch.execution_transcripts, indent=2, default=str)
    )

    total_code_calls = sum(len(t) for t in orch.execution_transcripts.values())
    import os as _os
    meta = {
        "condition": "AGENTIC-v2 (8-phase pipeline + real code execution)",
        "model": _os.environ.get("LLM_MODEL", "gemini-2.5-pro"),
        "elapsed_seconds": round(elapsed, 1),
        "blocked_phase": result.blocked_phase,
        "phases_run": sorted(result.phase_outputs.keys()),
        "phase_status": {
            str(p): (o.get("status") if isinstance(o, dict) else "?")
            for p, o in sorted(result.phase_outputs.items())
        },
        "code_executing_phases": sorted(orch.execution_transcripts.keys()),
        "code_calls_per_phase": {
            str(p): len(t) for p, t in sorted(orch.execution_transcripts.items())
        },
        "total_code_executions": total_code_calls,
        "has_final_report": bool(result.final_report),
        "final_report_chars": len(result.final_report or ""),
    }
    (RESULTS / "agentic_v2_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n=== AGENTIC-v2 PIPELINE FINISHED ===")
    print(f"Elapsed: {elapsed:.1f}s")
    if result.blocked_phase is not None:
        print(f"WARNING: blocked at phase {result.blocked_phase}")
    print(f"Phases run: {meta['phases_run']}")
    for p, s in meta["phase_status"].items():
        print(f"  Phase {p}: {s}")
    print(f"Code-executing phases: {meta['code_executing_phases']}")
    print(f"Total code executions: {total_code_calls}")
    print(f"Final report: {meta['final_report_chars']} chars")
    return 0 if result.blocked_phase is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
