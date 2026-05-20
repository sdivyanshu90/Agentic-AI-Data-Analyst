"""Retry with enriched context.

CLAUDE.md rule: never retry with identical input. Inject the gate failure
reason + the previous (failed) output so the agent can self-correct
instead of reproducing the same mistake.
"""
from __future__ import annotations

from typing import Any

from .quality_gates import GateResult


def build_retry_context(
    *,
    attempt: int,
    previous_output: dict | None,
    gate_result: GateResult,
) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "previous_output": previous_output,
        "quality_gate_failure_reason": gate_result.failure_reason,
        "specific_instruction": (
            "Your previous output failed the quality gate because: "
            f"{gate_result.failure_reason}. Fix this specific issue and "
            "re-run all tasks. Do not repeat the previous output verbatim."
        ),
    }
