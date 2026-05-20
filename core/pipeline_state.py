"""Append-only PIPELINE STATE LOG.

CLAUDE.md invariant #10: never overwrite a previous phase entry. The log
captures every phase attempt — successful or retried — so downstream
agents and the human auditor can replay the run.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PipelineStateLog:
    mission_brief: dict = field(default_factory=dict)
    current_phase: int = 0
    overall_status: str = "IN_PROGRESS"
    phases: list[dict[str, Any]] = field(default_factory=list)

    def set_mission_brief(self, brief: dict) -> None:
        self.mission_brief = brief

    def attempt_count(self, phase_number: int) -> int:
        return sum(1 for entry in self.phases if entry["phase_number"] == phase_number)

    def append_phase(
        self,
        *,
        phase_number: int,
        phase_name: str,
        status: str,
        key_decisions: list,
        reasoning_summary: str,
        output_summary: str,
        quality_gate_passed: bool,
        failure_reason: str = "",
    ) -> dict:
        entry = {
            "phase_number": phase_number,
            "phase_name": phase_name,
            "status": status,
            "attempt_count": self.attempt_count(phase_number) + 1,
            "key_decisions": key_decisions,
            "reasoning_summary": reasoning_summary,
            "output_summary": output_summary,
            "quality_gate_passed": quality_gate_passed,
            "failure_reason": failure_reason,
            "timestamp": _utc_now(),
        }
        self.phases.append(entry)
        self.current_phase = phase_number
        return entry

    def mark_complete(self) -> None:
        self.overall_status = "COMPLETE"

    def mark_blocked(self) -> None:
        self.overall_status = "BLOCKED"

    def to_dict(self) -> dict:
        return {
            "pipeline_state": {
                "mission_brief": self.mission_brief,
                "current_phase": self.current_phase,
                "overall_status": self.overall_status,
                "phases": list(self.phases),
            }
        }

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8")
        return p

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineStateLog":
        state = data.get("pipeline_state") or data
        return cls(
            mission_brief=state.get("mission_brief") or {},
            current_phase=state.get("current_phase", 0),
            overall_status=state.get("overall_status", "IN_PROGRESS"),
            phases=list(state.get("phases") or []),
        )
