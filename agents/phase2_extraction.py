"""Phase 2 Agent — Data Identification, Collection & Extraction.

Delegates to the shared `core.phase_execution.run_phase` runner (reasoning
call; not code-capable — Phase 2 plans the schema and extraction approach).
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 2
PHASE_NAME = "Data Identification & Extraction"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 2 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=False)
