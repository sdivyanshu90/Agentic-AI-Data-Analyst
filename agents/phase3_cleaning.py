"""Phase 3 Agent — Data Quality & Cleaning.

Code-capable: when the mission brief carries a real `dataset_path`, this agent
runs pandas against the actual file (via the `run_python` tool) to find the
true null counts, dtype problems and anomalies — instead of inferring them
from the prose data description. See `core.phase_execution`.
"""
from __future__ import annotations

from core.phase_execution import PhaseRunResult, run_phase

PHASE_NUMBER = 3
PHASE_NAME = "Data Quality & Cleaning"

__all__ = ["PhaseRunResult", "run", "PHASE_NUMBER", "PHASE_NAME"]


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 3 against the given context packet."""
    return run_phase(PHASE_NUMBER, PHASE_NAME, context_packet, code_capable=True)
