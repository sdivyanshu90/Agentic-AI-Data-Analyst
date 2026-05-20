"""JUNIOR-A baseline: a single-shot LLM analysis.

One Gemini call (same model + same per-call extended-thinking budget the
agentic pipeline uses) prompted to act as a junior data analyst. No
orchestration, no phase structure, no quality gates. This isolates the
value of the agentic structure: JUNIOR-A and AGENTIC differ ONLY in
orchestration.

Output: benchmark/results/junior_a_output.md
        benchmark/results/junior_a_meta.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.llm_client import call_llm  # noqa: E402

RESULTS = REPO_ROOT / "benchmark" / "results"

SYSTEM_PROMPT = (
    "You are a junior data analyst. A stakeholder has handed you a dataset and "
    "a business question. Produce your analysis in one pass: examine the data "
    "described, work out what drives the outcome, and give recommendations. "
    "Write a clear analysis in Markdown for a business audience. Be practical "
    "and concise."
)


def main() -> int:
    description = (RESULTS / "data_description.txt").read_text()

    user_message = (
        "Here is the dataset and the business question. Please analyse it and "
        "give me your findings and recommendations.\n\n"
        f"{description}\n\n"
        "Deliver: (1) what the data shows, (2) the main drivers of the outcome, "
        "(3) your recommendations."
    )

    print("JUNIOR-A: calling Gemini (single shot)...", flush=True)
    t0 = time.time()
    response = call_llm(SYSTEM_PROMPT, user_message, json_output=False, max_tokens=8192)
    elapsed = time.time() - t0

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "junior_a_output.md").write_text(response.text)
    meta = {
        "baseline": "JUNIOR-A (single-shot LLM)",
        "model": response.model,
        "llm_calls": 1,
        "elapsed_seconds": round(elapsed, 1),
        "usage": response.usage,
    }
    (RESULTS / "junior_a_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"JUNIOR-A done in {elapsed:.1f}s — {len(response.text)} chars")
    print(f"Usage: {response.usage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
