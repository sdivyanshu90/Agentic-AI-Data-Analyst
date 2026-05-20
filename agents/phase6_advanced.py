"""Phase 6 Agent — Advanced Analysis & Root Cause.

Code-capable: when the mission brief carries a real `dataset_path`, this agent
runs the actual segmentation, Pareto and interaction/confounding analysis
against the real file via the `run_python` tool. See `core.phase_execution`.
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 6
PHASE_NAME = "Advanced Analysis & Root Cause"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 6 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=True)
