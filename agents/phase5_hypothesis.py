"""Phase 5 Agent — Hypothesis Testing & Validation.

Code-capable: when the mission brief carries a real `dataset_path`, this agent
runs the actual statistical tests (chi-square, t-tests, regression, effect
sizes) against the real file via the `run_python` tool — so its p-values and
effect sizes are computed, not asserted. See `core.phase_execution`.
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 5
PHASE_NAME = "Hypothesis Testing & Validation"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 5 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=True)
