"""Run the Part C stress scenario through the pipeline.

Usage:
  python benchmark/run_stress.py --label baseline --repo /path/to/snapshot \
      --phases 1,2,3,4,5,6,7,8
  python benchmark/run_stress.py --label v3   # current repo, default phases

Interactive confirmations (Phase 3 row-loss) are auto-approved and logged —
this is a benchmark harness, not a production run. A PhaseBlockedError is a
*result*, not a crash: the blocked phase and reason are recorded in meta.json
so the scorer can judge whether blocking was the correct behaviour.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_RESULTS = HERE / "stress_results"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="e.g. baseline | v3")
    ap.add_argument(
        "--repo",
        default=str(HERE.parent),
        help="Repo root whose pipeline code should run (default: this repo)",
    )
    ap.add_argument(
        "--phases",
        default="",
        help="Comma-separated phase list; empty = the repo's default order",
    )
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    sys.path.insert(0, str(repo))

    from orchestrator.orchestrator import DataAnalystOrchestrator, PhaseBlockedError  # noqa: E402

    # Scenario inputs always come from THIS repo so both runs get identical traps.
    sys.path.insert(0, str(HERE))
    import stress_scenario as sc  # noqa: E402

    results_dir = DEFAULT_RESULTS / args.label
    results_dir.mkdir(parents=True, exist_ok=True)

    orch = DataAnalystOrchestrator(
        log_dir=results_dir / "logs",
        output_dir=results_dir / "outputs",
        verbose=True,
    )

    confirmations: list[str] = []

    def auto_confirm(question: str) -> bool:
        print(f"\n[run_stress] AUTO-CONFIRM: {question}", flush=True)
        confirmations.append(question)
        return True

    orch.user_confirm = auto_confirm

    phases = None
    if args.phases.strip():
        phases = [
            float(x) if "." in x else int(x)
            for x in args.phases.split(",")
            if x.strip()
        ]

    started = time.time()
    meta: dict = {
        "label": args.label,
        "repo": str(repo),
        "phases_requested": phases,
        "auto_confirmations": confirmations,
    }

    try:
        result = orch.run(
            objective=sc.OBJECTIVE,
            data_source_description=sc.DATA_DESCRIPTION,
            stakeholder_type=sc.STAKEHOLDER,
            business_domain=sc.BUSINESS_DOMAIN,
            constraints=sc.CONSTRAINTS,
            phases_to_run=phases,
        )
    except PhaseBlockedError as exc:  # defensive: run() normally catches these
        meta["outcome"] = "BLOCKED_EXCEPTION"
        meta["blocked_reason"] = str(exc)
        meta["elapsed_s"] = round(time.time() - started, 1)
        (results_dir / "meta.json").write_text(json.dumps(meta, indent=2))
        print(f"\n[run_stress] pipeline raised PhaseBlockedError: {exc}")
        return 2

    meta["elapsed_s"] = round(time.time() - started, 1)
    meta["blocked_phase"] = result.blocked_phase
    meta["phases_completed"] = sorted(result.phase_outputs.keys(), key=float)
    meta["outcome"] = "BLOCKED" if result.blocked_phase is not None else "COMPLETE"
    (results_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=str))

    if result.final_report:
        (results_dir / "final_report.md").write_text(
            result.final_report, encoding="utf-8"
        )

    print(f"\n[run_stress] {args.label}: {meta['outcome']} "
          f"(phases {meta['phases_completed']}, {meta['elapsed_s']}s)")
    if result.blocked_phase is not None:
        # The blocked reason is in the last pipeline-state entry.
        entries = result.pipeline_state_log.get("pipeline_state", {}).get("phases", [])
        if entries:
            print(f"[run_stress] blocked at phase {result.blocked_phase}: "
                  f"{entries[-1].get('failure_reason', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
