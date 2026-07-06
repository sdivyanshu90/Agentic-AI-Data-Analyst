"""Phase 6.5 Agent — Independent Red-Team Peer Review.

A separate adversarial invocation between Phase 6 and Phase 7: it did not
produce the analysis and its only job is to break Phases 4–6's conclusions
before they reach a stakeholder. Code-capable so it can spot-check claimed
figures against the real dataset when one is available.
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 6.5
PHASE_NAME = "Independent Red-Team Peer Review"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 6.5 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=True)
