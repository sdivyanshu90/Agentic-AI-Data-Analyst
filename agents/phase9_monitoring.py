"""Phase 9 Agent — Impact Tracking & Monitoring Handoff.

Runs after Phase 8. Instruments every recommendation with a success metric
and check-in date, defines drift alerts for key findings, and produces the
knowledge-base entry the Orchestrator persists for future runs.
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 9
PHASE_NAME = "Impact Tracking & Monitoring Handoff"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 9 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=False)
