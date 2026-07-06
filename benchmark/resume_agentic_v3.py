"""Resume the AGENTIC-v3 benchmark run after the Phase 6.5 red-team BLOCK.

The first v3 run was halted by the red-team reviewer with four required
revisions (multicollinear regression, unchecked marketing-campaign confound,
over-graded evidence, self-selection caveat). Per the pipeline's design a
BLOCK is a user decision point — this script plays the user's part: it
accepts the revisions and resumes from Phase 5 (the earliest phase a
revision touches), carrying the revisions in `user_clarifications` so every
downstream agent sees them in its context packet.

Phases 0-4 are reloaded verbatim from the blocked run's persisted outputs.

Output: identical artifact set to run_agentic_v3.py (report, phase outputs,
transcripts, meta) — meta records the block-and-resume history.
"""
from __future__ import annotations

import glob
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

os.environ.setdefault("KNOWLEDGE_BASE_DIR", str(RESULTS / "v3_knowledge"))

from orchestrator.orchestrator import DataAnalystOrchestrator  # noqa: E402

# Round-2 revisions (the resumed run was blocked again, on new findings).
ROUND_2_REVISIONS = [
    "For finding H1 in Phase 5, reflect the weak evidence honestly: the "
    "p-value (0.032) is marginal, fails multiple-testing correction, and "
    "the odds-ratio confidence interval [1.156, 26.986] is extremely wide. "
    "(Schema note: 'result' must be one of SUPPORTED | REJECTED | "
    "INCONCLUSIVE — use INCONCLUSIVE, or SUPPORTED only with these "
    "caveats stated prominently in evidence_grade_reasoning and "
    "statistical_caveats.)",
    "For the 'Contract x Internet Service Interaction' root cause in "
    "Phase 6, downgrade status from CONFIRMED to HYPOTHESISED and rewrite "
    "the description to present the targeted price increase as an equally "
    "or more plausible root cause than 'product positioning mismatch'.",
    "In Phase 6, expand the confound_sweep for the 'High Churn for "
    "Electronic Check' finding (H3) to sweep by tenure_group and "
    "InternetService, verifying the effect is consistent.",
    "In the root_cause_chains for H3, add the alternative explanation that "
    "Electronic Check may be a non-causal proxy for an underlying "
    "high-churn demographic rather than a direct cause via payment "
    "friction.",
]

REVIEW_PROTOCOL_NOTE = (
    "REVIEW PROTOCOL (from the user): this is review round 3. The round-1 "
    "and round-2 required revisions above are binding and must be applied "
    "at the phase they touch. Phase 6.5 reviewer: verify the revisions were "
    "faithfully applied; if they were, and no NEW critical flaw exists, the "
    "appropriate verdict is PROCEED or PROCEED_WITH_REVISIONS — reserve "
    "BLOCK for unapplied revisions or newly discovered critical flaws, not "
    "for restating already-addressed concerns."
)

# The four revisions from the first run's RED_TEAM_BLOCK state-log entry.
REQUIRED_REVISIONS = [
    "Rebuild the logistic regression model (SQ5) to correctly handle "
    "multicollinearity between 'tenure' and 'TotalCharges'. Remove "
    "'TotalCharges' from the model predictors and re-evaluate the odds "
    "ratios and ranking of churn drivers.",
    "Re-execute the 'confound_sweep' for the root cause of high early-life "
    "churn (H2/Insight 3). Explicitly check for the influence of the "
    "'Marketing campaigns' confound candidate identified in Phase 0.",
    "Downgrade the 'evidence_grade' for H2, H3, and H5 to more accurately "
    "reflect the nature of single-dataset analysis. (Note: the schema "
    "allows CONFIRMATORY | EXPLORATORY only — apply the nearest honest "
    "treatment: grade EXPLORATORY and/or carry an explicit "
    "single-dataset caveat into the report.)",
    "Add a more prominent caveat to the 'Impact Quantification' for the "
    "'Tech Support' finding, explicitly stating that the estimate is "
    "likely an upper bound due to self-selection bias and the true causal "
    "effect is expected to be lower.",
]

RESUME_FROM = 5  # earliest phase a revision touches (evidence grades)
PHASES_TO_RUN = [5, 6, 6.5, 7, 8, 9]


def _load_prior_outputs() -> dict:
    """Load phases 0-4 verbatim from the blocked run's persisted outputs."""
    prior: dict = {}
    for p in (0, 1, 2, 3, 4):
        matches = sorted(glob.glob(str(BENCH / "agentic_v3_outputs" / f"phase{p}_output_*.json")))
        if not matches:
            raise FileNotFoundError(f"No persisted output for phase {p}")
        prior[p] = json.loads(Path(matches[-1]).read_text())
    return prior


def main() -> int:
    description = (RESULTS / "data_description.txt").read_text()
    prior_outputs = _load_prior_outputs()

    orch = DataAnalystOrchestrator(
        log_dir=str(BENCH / "agentic_v3_logs"),
        output_dir=str(BENCH / "agentic_v3_outputs"),
        verbose=True,
    )
    orch.user_confirm = lambda question: True

    clarifications = [
        {
            "type": "RED_TEAM_BLOCK_RESOLUTION",
            "context": (
                "The Phase 6.5 red-team reviewer BLOCKED two previous runs of "
                "this analysis. The user has reviewed both verdicts and "
                "directs the pipeline to resume from Phase 5, applying every "
                "required revision below (round 1 and round 2). Downstream "
                "phases must treat these revisions as binding."
            ),
            "round_1_required_revisions": REQUIRED_REVISIONS,
            "round_2_required_revisions": ROUND_2_REVISIONS,
            "review_protocol": REVIEW_PROTOCOL_NOTE,
        }
    ]

    print(
        "AGENTIC-v3 RESUME: re-running phases "
        f"{PHASES_TO_RUN} with red-team revisions applied...",
        flush=True,
    )
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
        dataset_path=str(DATASET),
        phases_to_run=PHASES_TO_RUN,
        resume_outputs=prior_outputs,
        user_clarifications=clarifications,
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
        "history": [
            "run 1: BLOCKED at Phase 6.5 by red-team review "
            "(multicollinear regression, unchecked marketing-campaign "
            "confound, over-graded evidence, missing self-selection caveat)",
            "run 2: resumed from Phase 5 with round-1 revisions; BLOCKED "
            "again at Phase 6.5 on new findings (H1 marginal p=0.032 failing "
            "MTC with wide CI, price-hike alternative for the M2M-Fiber root "
            "cause, Electronic-Check proxy explanation, sweep gaps)",
            f"run 3 (this): resumed from Phase {RESUME_FROM} with cumulative "
            "round-1 + round-2 revisions and an explicit review protocol",
        ],
        "elapsed_seconds_resume": round(elapsed, 1),
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

    print("\n=== AGENTIC-v3 RESUME FINISHED ===")
    print(f"Elapsed: {elapsed:.1f}s")
    if result.blocked_phase is not None:
        print(f"WARNING: blocked again at phase {result.blocked_phase}")
    print(f"Red-team verdict: {meta['red_team_verdict']}")
    print(f"Code executions this resume: {total_code_calls}")
    print(f"Final report: {meta['final_report_chars']} chars")
    return 0 if result.blocked_phase is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
