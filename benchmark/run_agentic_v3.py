"""AGENTIC-v3 condition: the full 11-phase pipeline WITH real code execution.

Same dataset, objective, and fairness controls as run_agentic_v2.py; the only
change is the pipeline itself — the senior-analyst phases are now in the loop:

  Phase 0    intake triage + known-event confound calendar
  Phases 1-6 as before (4/5 now carry hypothesis provenance / evidence grades,
             6 runs the systematic confound sweep + sensitivity analysis)
  Phase 6.5  independent red-team peer review (adversarial, code-capable)
  Phases 7-8 as before
  Phase 9    impact tracking, drift alerts, knowledge-base entry

Output: benchmark/results/agentic_v3_report.md
        benchmark/results/agentic_v3_phase_outputs.json
        benchmark/results/agentic_v3_meta.json
        benchmark/results/agentic_v3_transcripts.json   (executed-code audit trail)
        benchmark/agentic_v3_logs/ , benchmark/agentic_v3_outputs/
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BENCH = REPO_ROOT / "benchmark"
RESULTS = BENCH / "results"
DATASET = BENCH / "data" / "Telco-Customer-Churn.csv"

# Keep the benchmark's institutional memory separate from any other runs.
os.environ.setdefault("KNOWLEDGE_BASE_DIR", str(RESULTS / "v3_knowledge"))

from orchestrator.orchestrator import DataAnalystOrchestrator  # noqa: E402


def main() -> int:
    description = (RESULTS / "data_description.txt").read_text()

    orch = DataAnalystOrchestrator(
        log_dir=str(BENCH / "agentic_v3_logs"),
        output_dir=str(BENCH / "agentic_v3_outputs"),
        verbose=True,
    )
    orch.user_confirm = lambda question: True

    print("AGENTIC-v3: running 11-phase pipeline WITH real code execution...", flush=True)
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
        dataset_path=str(DATASET),  # real code execution for phases 3-6 and 6.5
        # phases_to_run omitted -> full 11-phase order [0..9]
    )
    elapsed = time.time() - t0

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "agentic_v3_phase_outputs.json").write_text(
        json.dumps(result.phase_outputs, indent=2, default=str)
    )
    if result.final_report:
        (RESULTS / "agentic_v3_report.md").write_text(result.final_report)
    (RESULTS / "agentic_v3_transcripts.json").write_text(
        json.dumps(orch.execution_transcripts, indent=2, default=str)
    )

    total_code_calls = sum(len(t) for t in orch.execution_transcripts.values())
    meta = {
        "condition": "AGENTIC-v3 (11-phase pipeline + real code execution)",
        "model": os.environ.get("LLM_MODEL", "gemini-2.5-pro"),
        "elapsed_seconds": round(elapsed, 1),
        "blocked_phase": result.blocked_phase,
        "phases_run": sorted(result.phase_outputs.keys(), key=float),
        "phase_status": {
            str(p): (o.get("status") if isinstance(o, dict) else "?")
            for p, o in sorted(result.phase_outputs.items(), key=lambda kv: float(kv[0]))
        },
        "red_team_verdict": (result.phase_outputs.get(6.5) or {}).get("verdict"),
        "code_executing_phases": sorted(orch.execution_transcripts.keys(), key=float),
        "code_calls_per_phase": {
            str(p): len(t)
            for p, t in sorted(orch.execution_transcripts.items(), key=lambda kv: float(kv[0]))
        },
        "total_code_executions": total_code_calls,
        "has_final_report": bool(result.final_report),
        "final_report_chars": len(result.final_report or ""),
    }
    (RESULTS / "agentic_v3_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n=== AGENTIC-v3 PIPELINE FINISHED ===")
    print(f"Elapsed: {elapsed:.1f}s")
    if result.blocked_phase is not None:
        print(f"WARNING: blocked at phase {result.blocked_phase}")
    print(f"Phases run: {meta['phases_run']}")
    for p, s in meta["phase_status"].items():
        print(f"  Phase {p}: {s}")
    print(f"Red-team verdict: {meta['red_team_verdict']}")
    print(f"Code-executing phases: {meta['code_executing_phases']}")
    print(f"Total code executions: {total_code_calls}")
    print(f"Final report: {meta['final_report_chars']} chars")
    return 0 if result.blocked_phase is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
