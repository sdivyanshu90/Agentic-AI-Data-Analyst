"""Score AGENTIC-v2 (the code-executing pipeline) and verify its numbers.

Three checks:
  1. LLM-as-judge on the same 7-dimension rubric as score.py.
  2. Deterministic keyword scan.
  3. NUMBERS VERIFICATION — confirm the report's headline figures match the
     pandas/scipy ground truth, and that the executed-code transcript proves
     they were computed rather than recalled.

Output: benchmark/results/scores_v2.json
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

sys.path.insert(0, str(REPO_ROOT / "benchmark"))
from score import RUBRIC, deterministic_scan, judge  # noqa: E402

RESULTS = REPO_ROOT / "benchmark" / "results"

# Ground-truth facts the v2 report must get right. Each: (label, regex, note).
# Regexes are tolerant of rounding / phrasing.
NUMBER_CHECKS = [
    ("overall_churn_rate", r"26\.[345]\d?\s*%|26\.5\s*%", "≈26.5%"),
    ("totalcharges_blanks", r"\b11\b[^.]{0,60}(blank|null|missing|empty|non-numeric|"
        r"whitespace|space)|(blank|null|missing|empty|non-numeric)[^.]{0,60}\b11\b",
        "11 blank TotalCharges"),
    ("m2m_churn", r"4[0-4](?:\.\d+)?\s*%", "month-to-month ≈42.7%"),
    ("two_year_churn", r"\b[23](?:\.\d+)?\s*%", "two-year ≈2.7%"),
    ("fiber_churn", r"4[12](?:\.\d+)?\s*%", "fiber optic ≈41.9%"),
    ("electronic_check_churn", r"4[45](?:\.\d+)?\s*%", "electronic check ≈45.3%"),
    ("contract_is_driver", r"contract", "Contract identified as a driver"),
    ("tenure_is_driver", r"tenure", "tenure identified as a driver"),
]


def verify_numbers(report: str) -> dict:
    low = report.lower()
    checks = []
    for label, pattern, note in NUMBER_CHECKS:
        hit = bool(re.search(pattern, low))
        checks.append({"fact": label, "expected": note, "present": hit})
    passed = sum(c["present"] for c in checks)
    return {"checks": checks, "passed": passed, "total": len(checks),
            "accuracy": round(passed / len(checks), 3)}


def summarise_transcripts(transcripts: dict) -> dict:
    total_calls = 0
    ok_calls = 0
    sample = []
    for phase, calls in sorted(transcripts.items()):
        for c in calls:
            total_calls += 1
            if c.get("ok"):
                ok_calls += 1
            if len(sample) < 3:
                sample.append({"phase": phase, "code": (c.get("code") or "")[:240]})
    return {
        "code_executing_phases": sorted(transcripts.keys()),
        "total_code_executions": total_calls,
        "successful_executions": ok_calls,
        "sample_executed_code": sample,
    }


def main() -> int:
    ground_truth = json.loads((RESULTS / "ground_truth.json").read_text())
    report_path = RESULTS / "agentic_v2_report.md"
    if not report_path.exists():
        print(f"ERROR: {report_path} not found — run run_agentic_v2.py first.")
        return 2
    report = report_path.read_text()

    name = "AGENTIC-v2 (8-phase pipeline + code execution)"
    print(f"Scoring {name} ({len(report)} chars)...", flush=True)

    det = deterministic_scan(report)
    numbers = verify_numbers(report)
    print(f"  numbers verified: {numbers['passed']}/{numbers['total']}")

    transcripts = {}
    tpath = RESULTS / "agentic_v2_transcripts.json"
    if tpath.exists():
        raw = json.loads(tpath.read_text())
        transcripts = {int(k): v for k, v in raw.items()}
    tsummary = summarise_transcripts(transcripts)
    print(f"  executed {tsummary['total_code_executions']} code block(s) "
          f"across phases {tsummary['code_executing_phases']}")

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
        "llm_judge": verdict,
    }
    (RESULTS / "scores_v2.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote {RESULTS / 'scores_v2.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
