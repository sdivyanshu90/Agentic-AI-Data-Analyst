"""Phase 0 Agent — Intake Triage & Context Calendar Check.

Runs before Phase 1. Classifies request complexity, builds the known-event
confound calendar, surfaces stakeholder conflicts, and decides the route
(SKIP_TO_QUICK_ANSWER vs FULL_PIPELINE). Reasoning call — no data touched yet.
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 0
PHASE_NAME = "Intake Triage & Context Calendar Check"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 0 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=False)
