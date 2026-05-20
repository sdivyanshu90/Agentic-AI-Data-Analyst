"""End-to-end sample run.

Default mode calls the LLM (requires GEMINI_API_KEY).
`--dry-run` short-circuits the Phase 1 agent with a canned output so the
orchestrator pipeline can be exercised without API calls.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.orchestrator import DataAnalystOrchestrator  # noqa: E402

SAMPLE_DIR = Path(__file__).resolve().parent
SAMPLE_OUTPUTS: dict[int, Path] = {
    1: SAMPLE_DIR / "dry_run_phase1_output.json",
    2: SAMPLE_DIR / "dry_run_phase2_output.json",
    3: SAMPLE_DIR / "dry_run_phase3_output.json",
    4: SAMPLE_DIR / "dry_run_phase4_output.json",
    5: SAMPLE_DIR / "dry_run_phase5_output.json",
    6: SAMPLE_DIR / "dry_run_phase6_output.json",
    7: SAMPLE_DIR / "dry_run_phase7_output.json",
    8: SAMPLE_DIR / "dry_run_phase8_output.json",
}


def _build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run an end-to-end example pipeline.")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Stub phase agents with canned outputs — no API calls.",
    )
    p.add_argument(
        "--phases",
        default="1,2,3,4,5,6,7,8",
        help="Comma-separated phases to run (default: 1,2,3,4,5,6,7,8).",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress transition cards.",
    )
    return p.parse_args()


class _FakeResult:
    def __init__(self, payload: dict):
        self.output = payload
        self.raw_text = json.dumps(payload)
        self.usage = None


def _load_canned(phase: int) -> dict[str, Any]:
    path = SAMPLE_OUTPUTS.get(phase)
    if path is None or not path.exists():
        raise FileNotFoundError(f"No canned dry-run output available for Phase {phase}.")
    return json.loads(path.read_text(encoding="utf-8"))


PHASE_AGENT_MODULES = {
    1: "agents.phase1_requirements.run",
    2: "agents.phase2_extraction.run",
    3: "agents.phase3_cleaning.run",
    4: "agents.phase4_eda.run",
    5: "agents.phase5_hypothesis.run",
    6: "agents.phase6_advanced.run",
    7: "agents.phase7_visualisation.run",
    8: "agents.phase8_reporting.run",
}


def main() -> int:
    args = _build_args()
    phases = [int(x) for x in args.phases.split(",") if x.strip()]

    orch = DataAnalystOrchestrator(verbose=not args.quiet)

    run_kwargs = dict(
        objective="Analyse Q3 churn in our SaaS product",
        data_source_description="PostgreSQL DB: users, events, subscriptions tables",
        stakeholder_type="product team",
        business_domain="SaaS",
        constraints={
            "time": "2 weeks",
            "tools": "SQL + Python",
            "privacy": "PII must be anonymised",
        },
        success_looks_like="Product team can pinpoint the top 3 drivers of Q3 churn",
        phases_to_run=phases,
    )

    if args.dry_run:
        with contextlib.ExitStack() as stack:
            for phase in phases:
                if phase not in PHASE_AGENT_MODULES:
                    print(f"No dry-run stub for Phase {phase}; aborting.", file=sys.stderr)
                    return 2
                canned = _load_canned(phase)
                stack.enter_context(
                    mock.patch(PHASE_AGENT_MODULES[phase], return_value=_FakeResult(canned))
                )
            result = orch.run(**run_kwargs)
    else:
        result = orch.run(**run_kwargs)

    print("\n--- mission brief ---")
    print(json.dumps(result.mission_brief, indent=2))

    for phase in phases:
        out = result.phase_outputs.get(phase)
        if out is None:
            continue
        print(f"\n--- phase {phase} output (truncated) ---")
        if phase == 1:
            preview = {
                "status": out.get("status"),
                "n_sub_questions": len(out.get("sub_questions") or []),
                "success_definition": out.get("success_definition"),
            }
        elif phase == 2:
            preview = {
                "status": out.get("status"),
                "n_sources": len(out.get("data_source_map") or []),
                "n_inferred_schemas": sum(
                    1 for s in (out.get("schema_reconnaissance") or [])
                    if s.get("schema_status") == "INFERRED"
                ),
                "n_pii_flags": sum(
                    1 for g in (out.get("governance_flags") or [])
                    if g.get("flag_type") == "PII"
                ),
                "phase_3_handoff_notes_preview": (out.get("phase_3_handoff_notes") or "")[:160],
            }
        elif phase == 3:
            suite = out.get("validation_suite") or {}
            preview = {
                "status": out.get("status"),
                "n_anomalies": len(out.get("anomaly_taxonomy") or []),
                "n_cleaning_decisions": len(out.get("cleaning_decisions") or []),
                "n_change_log_entries": len(out.get("change_log") or []),
                "row_loss_pct": suite.get("row_loss_pct"),
                "validation": {
                    k: suite.get(k)
                    for k in (
                        "null_check",
                        "range_check",
                        "date_check",
                        "enum_check",
                        "row_count_check",
                        "join_integrity_check",
                    )
                },
                "bias_severity": (out.get("bias_audit") or {}).get("severity"),
            }
        elif phase == 4:
            preview = {
                "status": out.get("status"),
                "n_univariate": len(out.get("univariate_analysis") or []),
                "n_bivariate": len(out.get("bivariate_analysis") or []),
                "n_hypotheses": len(out.get("hypotheses") or []),
                "n_viz_specs": len(out.get("eda_visualisation_spec") or []),
                "hypotheses_to_test": (out.get("phase_5_handoff") or {}).get(
                    "hypotheses_to_test"
                ),
            }
        elif phase == 5:
            tests = out.get("tests_conducted") or []
            mtc = out.get("multiple_testing_correction") or {}
            preview = {
                "status": out.get("status"),
                "n_tests": len(tests),
                "result_breakdown": {
                    r: sum(1 for t in tests if t.get("result") == r)
                    for r in ("SUPPORTED", "REJECTED", "INCONCLUSIVE")
                },
                "n_high_practical_sig": sum(
                    1 for t in tests if t.get("practical_significance") == "HIGH"
                ),
                "mtc_applied": mtc.get("applied"),
                "mtc_method": mtc.get("method"),
                "n_caveats": len(out.get("statistical_caveats") or []),
            }
        elif phase == 6:
            ranks = out.get("insight_ranking") or []
            preview = {
                "status": out.get("status"),
                "n_analyses": len(out.get("analyses") or []),
                "n_root_cause_chains": len(out.get("root_cause_chains") or []),
                "n_simpsons_paradox": sum(
                    1 for d in (out.get("segment_deep_dives") or [])
                    if d.get("simpsons_paradox_detected")
                ),
                "top_insight": ranks[0].get("insight") if ranks else None,
                "n_unanswered": len(out.get("unanswered_subquestions") or []),
            }
        elif phase == 7:
            review = out.get("accessibility_review") or {}
            preview = {
                "status": out.get("status"),
                "dashboard_type": (out.get("dashboard_architecture") or {}).get(
                    "dashboard_type"
                ),
                "n_specs": len(out.get("visualisation_specs") or []),
                "n_anti_patterns_corrected": len(out.get("anti_pattern_audit") or []),
                "accessibility": {
                    k: review.get(k)
                    for k in (
                        "colourblind_safe",
                        "wcag_contrast_met",
                        "alt_text_written",
                        "min_font_size_met",
                    )
                },
                "n_chart_headlines": len(
                    (out.get("phase_8_handoff") or {}).get(
                        "chart_titles_as_insight_headlines"
                    )
                    or []
                ),
            }
        elif phase == 8:
            summary = out.get("phase_8_summary") or {}
            report = out.get("final_report") or ""
            preview = {
                "status": out.get("status"),
                "report_words": len(report.split()),
                "sub_questions_answered": summary.get("sub_questions_answered"),
                "sub_questions_unanswered": summary.get("sub_questions_unanswered"),
                "recommendation_count": summary.get("recommendation_count"),
                "confidence_distribution": summary.get("confidence_distribution"),
                "quality_gate_checks_failed": summary.get(
                    "quality_gate_checks_failed"
                ),
            }
        else:
            preview = {"status": out.get("status")}
        print(json.dumps(preview, indent=2))

    if result.blocked_phase is not None:
        print(f"\nPipeline blocked at phase {result.blocked_phase}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
