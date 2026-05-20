"""Phase 4 Agent — Exploratory Data Analysis.

Code-capable: when the mission brief carries a real `dataset_path`, this agent
computes the actual univariate/bivariate distributions and correlations by
running pandas against the real file (via the `run_python` tool), rather than
estimating them. See `core.phase_execution`.
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 4
PHASE_NAME = "Exploratory Data Analysis"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 4 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=True)
