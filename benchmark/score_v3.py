"""Score AGENTIC-v3 (the 11-phase, code-executing pipeline).

Same three checks as score_v2.py (LLM-as-judge on the 7-dimension rubric,
deterministic keyword scan, numbers verification against the pandas/scipy
ground truth) plus a PROCESS AUDIT of the senior-analyst phases:

  * Phase 0  — triage route, confound candidates
  * Phase 4/5 — hypothesis provenance + evidence grades actually used
  * Phase 6  — confound sweep / sensitivity analysis coverage
  * Phase 6.5 — red-team verdict, kills, overclaim flags, required revisions
  * Phase 9  — success metrics, drift alerts, knowledge-base entry

Output: benchmark/results/scores_v3.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

sys.path.insert(0, str(REPO_ROOT / "benchmark"))
from score import deterministic_scan, judge, RUBRIC  # noqa: E402
from score_v2 import summarise_transcripts, verify_numbers  # noqa: E402

RESULTS = REPO_ROOT / "benchmark" / "results"


def process_audit(phase_outputs: dict) -> dict:
    """Summarise what the new senior-analyst phases actually did."""
    def get(p):
        return phase_outputs.get(p) or phase_outputs.get(str(p)) or {}

    p0, p4, p5 = get(0), get(4), get(5)
    p6, p65, p9 = get(6), get(6.5), get(9)

    hyps = p4.get("hypotheses") or []
    tests = p5.get("tests_conducted") or []
    alts = p65.get("alternative_explanations") or []
    return {
        "phase0": {
            "complexity": p0.get("complexity"),
            "route": p0.get("route"),
            "confound_candidates": [
                c.get("event") for c in (p0.get("confound_candidates") or [])
            ],
            "deadline_feasibility": (p0.get("scope_and_feasibility") or {}).get(
                "deadline_feasibility"
            ),
        },
        "provenance": {
            "hypotheses": {
                h.get("id"): h.get("provenance") for h in hyps
            },
            "evidence_grades": {
                t.get("hypothesis_id"): t.get("evidence_grade") for t in tests
            },
            "exploratory_count": sum(
                1 for t in tests if t.get("evidence_grade") == "EXPLORATORY"
            ),
        },
        "phase6": {
            "confound_sweep_findings": [
                s.get("finding_ref") for s in (p6.get("confound_sweep") or [])
            ],
            "post_sweep_verdicts": {
                s.get("finding_ref"): s.get("post_sweep_verdict")
                for s in (p6.get("confound_sweep") or [])
            },
            "sensitivity_entries": len(p6.get("sensitivity_analysis") or []),
            "fragile_findings": [
                s.get("finding_ref")
                for s in (p6.get("sensitivity_analysis") or [])
                if s.get("robustness") == "FRAGILE"
            ],
            "external_benchmarks": [
                {
                    "metric": b.get("benchmark_metric"),
                    "value": b.get("benchmark_value"),
                    "source": b.get("source"),
                }
                for b in (p6.get("external_benchmarks") or [])
            ],
        },
        "red_team": {
            "verdict": p65.get("verdict"),
            "alternatives_audited": len(alts),
            "findings_killed": [
                a.get("original_finding")
                for a in alts
                if a.get("original_survives") is False
            ],
            "overclaim_flags": [
                {
                    "finding": f.get("finding"),
                    "stated": f.get("stated_confidence"),
                    "corrected": f.get("corrected_confidence"),
                }
                for f in (p65.get("overclaim_flags") or [])
            ],
            "required_revisions": p65.get("required_revisions") or [],
        },
        "phase9": {
            "success_metrics": len(p9.get("success_metrics") or []),
            "check_in_dates": [
                m.get("check_in_date") for m in (p9.get("success_metrics") or [])
            ],
            "monitoring_specs": len(p9.get("monitoring_specs") or []),
            "kb_gotchas": (p9.get("knowledge_base_entry") or {}).get(
                "gotchas_discovered"
            )
            or [],
        },
    }


def main() -> int:
    ground_truth = json.loads((RESULTS / "ground_truth.json").read_text())
    report_path = RESULTS / "agentic_v3_report.md"
    if not report_path.exists():
        print(f"ERROR: {report_path} not found — run run_agentic_v3.py first.")
        return 2
    report = report_path.read_text()

    name = "AGENTIC-v3 (11-phase pipeline + code execution)"
    print(f"Scoring {name} ({len(report)} chars)...", flush=True)

    det = deterministic_scan(report)
    numbers = verify_numbers(report)
    print(f"  numbers verified: {numbers['passed']}/{numbers['total']}")

    transcripts = {}
    tpath = RESULTS / "agentic_v3_transcripts.json"
    if tpath.exists():
        raw = json.loads(tpath.read_text())
        transcripts = {float(k): v for k, v in raw.items()}
    tsummary = summarise_transcripts(transcripts)
    print(f"  executed {tsummary['total_code_executions']} code block(s) "
          f"across phases {tsummary['code_executing_phases']}")

    phase_outputs = json.loads((RESULTS / "agentic_v3_phase_outputs.json").read_text())
    audit = process_audit(phase_outputs)
    print(f"  red-team verdict: {audit['red_team']['verdict']} "
          f"({len(audit['red_team']['overclaim_flags'])} overclaim flag(s))")

    t0 = time.time()
    verdict = judge(name, report, ground_truth)
    print(f"  judged in {time.time() - t0:.1f}s — "
          f"overall {verdict.get('overall_weighted')}")

    out = {
        "condition": name,
        "rubric": RUBRIC,
        "deterministic_scan": det,
        "numbers_verification": numbers,
        "execution_transcript_summary": tsummary,
        "process_audit": audit,
        "llm_judge": verdict,
    }
    (RESULTS / "scores_v3.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote {RESULTS / 'scores_v3.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
