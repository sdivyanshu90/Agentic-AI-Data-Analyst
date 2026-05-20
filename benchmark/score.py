"""Score the three conditions against the ground truth.

Two independent scoring passes per deliverable:
  1. Deterministic keyword/structure scan (no LLM) — objective evidence.
  2. LLM-as-judge — one Gemini call per deliverable, given the full
     ground-truth answer key and a fixed 7-dimension rubric.

Output: benchmark/results/scores.json
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

from core.llm_client import call_llm, extract_json_output  # noqa: E402

RESULTS = REPO_ROOT / "benchmark" / "results"

RUBRIC = {
    "driver_coverage": "Identifies the true top churn drivers (tenure, Contract, "
        "InternetService, OnlineSecurity, TechSupport, PaymentMethod) and does NOT "
        "promote non-drivers (gender) as important. 0-10.",
    "statistical_rigour": "Uses hypothesis tests, p-values, effect sizes (Cramer's V "
        "/ Cohen's d), or significance reasoning rather than eyeballing raw rate "
        "spreads. Distinguishes signal strength. 0-10.",
    "data_quality": "Catches the real data-quality issues: TotalCharges stored as "
        "text with 11 blank values (all tenure=0 new customers), SeniorCitizen's "
        "0/1 encoding, the structural 'No internet service' levels. 0-10.",
    "confounding_root_cause": "Recognises that the predictors are correlated "
        "(Contract / tenure / InternetService / add-on services overlap), avoids "
        "double-counting, and reasons about WHY churn happens, not just WHAT "
        "correlates. 0-10.",
    "caveat_honesty": "States limitations, calibrates confidence, and flags that "
        "the analysis is observational/correlational, not causal. 0-10.",
    "actionability": "Recommendations are specific, measurable, prioritised, tied "
        "to the identified drivers, and mindful of cost/leverage. 0-10.",
    "traceability_comms": "Clear evidence chain from data to finding to "
        "recommendation; communication suited to a medium-technical business "
        "stakeholder. 0-10.",
}

JUDGE_SYSTEM = (
    "You are a rigorous, impartial principal data scientist grading analytical "
    "deliverables. You are given a verified ground-truth answer key computed "
    "directly from the raw data with pandas/scipy, a fixed rubric, and one "
    "analyst deliverable. Grade ONLY against the rubric and the ground truth. "
    "Be discerning and critical: a fluent, confident report that skips "
    "statistical rigour or data-quality checks must score lower on those "
    "dimensions than its prose suggests. Reward demonstrated process, not "
    "just correct-sounding conclusions. Return strict JSON."
)

# --- deterministic keyword probes -----------------------------------------
PROBES = {
    "mentions_tenure": r"\btenure\b",
    "mentions_contract": r"\bcontract\b",
    "mentions_internet_service": r"internet service|fiber",
    "mentions_payment_method": r"payment method|electronic check",
    "mentions_security_support": r"online ?security|tech ?support",
    "significance_testing": r"\bp[- ]?value|chi[- ]?squar|significan|hypothesis test|t-test|statistical(ly)? ",
    "effect_sizes": r"cram[eé]r|cohen|effect size|odds ratio|relative risk",
    "data_quality_totalcharges": r"totalcharges.{0,60}(text|string|blank|missing|coerce|convert|null|empty)|"
        r"(blank|missing|null|empty|11).{0,40}totalcharges",
    "confounding": r"confound|multicollinear|correlat.{0,30}(predictor|variable|feature|each other)|"
        r"overlap.{0,30}(variable|predictor|service)|interact(ion)? effect",
    "causal_caveat": r"correlat.{0,20}not.{0,20}caus|not.{0,15}causa|observational|"
        r"cannot.{0,20}(prove|establish).{0,20}caus",
    "gender_distractor_handled": r"gender.{0,80}(no |not |negligible|little|minimal|weak|insignificant|"
        r"doesn|isn|small)|gender.{0,30}(0\.8|distractor)",
}


def deterministic_scan(text: str) -> dict:
    low = text.lower()
    hits = {k: bool(re.search(pat, low)) for k, pat in PROBES.items()}
    hits["n_recommendations"] = len(re.findall(
        r"(?m)^\s*(?:[-*]|\d+[.)])\s", text))
    hits["length_chars"] = len(text)
    return hits


def judge(name: str, deliverable: str, ground_truth: dict) -> dict:
    rubric_txt = "\n".join(f"  - {k}: {v}" for k, v in RUBRIC.items())
    user = (
        "GROUND TRUTH ANSWER KEY (computed from the raw data — authoritative):\n"
        f"{json.dumps(ground_truth, indent=2)}\n\n"
        "RUBRIC — score each dimension 0-10 (integer):\n"
        f"{rubric_txt}\n\n"
        f"ANALYST DELIVERABLE TO GRADE (condition: {name}):\n"
        "<<<DELIVERABLE\n"
        f"{deliverable}\n"
        "DELIVERABLE>>>\n\n"
        "Return JSON exactly in this shape:\n"
        '{"scores": {"<dimension>": {"score": <int 0-10>, '
        '"justification": "<=40 words"}}, '
        '"overall_weighted": <float 0-10>, '
        '"one_line_verdict": "<=30 words"}\n'
        "Include every rubric dimension in scores. overall_weighted is the mean "
        "of the seven dimension scores."
    )
    resp = call_llm(JUDGE_SYSTEM, user, json_output=True, max_tokens=4096)
    return extract_json_output(resp.text)


DELIVERABLES = {
    "JUNIOR-A (single-shot LLM)": "junior_a_output.md",
    "JUNIOR-B (naive pandas)": "junior_b_output.md",
    "AGENTIC (8-phase pipeline)": "agentic_report.md",
}


def main() -> int:
    ground_truth = json.loads((RESULTS / "ground_truth.json").read_text())
    scores: dict = {"rubric": RUBRIC, "conditions": {}}

    for name, fname in DELIVERABLES.items():
        path = RESULTS / fname
        if not path.exists():
            print(f"SKIP {name}: {path} not found")
            continue
        text = path.read_text()
        print(f"Scoring {name} ({len(text)} chars)...", flush=True)
        det = deterministic_scan(text)
        t0 = time.time()
        verdict = judge(name, text, ground_truth)
        print(f"  judged in {time.time() - t0:.1f}s — "
              f"overall {verdict.get('overall_weighted')}")
        scores["conditions"][name] = {
            "deliverable_file": fname,
            "deterministic_scan": det,
            "llm_judge": verdict,
        }

    (RESULTS / "scores.json").write_text(json.dumps(scores, indent=2))
    print(f"\nWrote {RESULTS / 'scores.json'}")
    print("\n=== LLM-JUDGE OVERALL ===")
    for name, c in scores["conditions"].items():
        print(f"  {name:32s} {c['llm_judge'].get('overall_weighted')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
