"""Phase 7 Agent — Data Visualisation & Dashboard Design.

Delegates to the shared `core.phase_execution.run_phase` runner (reasoning
call; not code-capable — Phase 7 designs charts from the prior phases' findings).
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 7
PHASE_NAME = "Visualisation & Dashboard Design"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 7 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=False)
