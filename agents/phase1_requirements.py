"""Phase 1 Agent — Stakeholder Requirement Gathering & Problem Framing.

Delegates to the shared `core.phase_execution.run_phase` runner (reasoning
call; not code-capable — Phase 1 frames the problem before any data is touched).
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 1
PHASE_NAME = "Stakeholder Requirement Gathering"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 1 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=False)
