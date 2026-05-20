"""Pipeline state log behaviour: append-only, attempt counting, persistence."""
from __future__ import annotations

import json

from core.pipeline_state import PipelineStateLog


def test_append_phase_increments_attempt_count_per_phase(tmp_path):
    log = PipelineStateLog()
    log.set_mission_brief({"objective": "x"})

    log.append_phase(
        phase_number=1,
        phase_name="Phase 1",
        status="RETRYING",
        key_decisions=[],
        reasoning_summary="first try",
        output_summary="bad",
        quality_gate_passed=False,
        failure_reason="missing field",
    )
    log.append_phase(
        phase_number=1,
        phase_name="Phase 1",
        status="COMPLETE",
        key_decisions=["ok"],
        reasoning_summary="second try",
        output_summary="good",
        quality_gate_passed=True,
    )

    assert [p["attempt_count"] for p in log.phases] == [1, 2]
    # Append-only: prior entries are untouched.
    assert log.phases[0]["status"] == "RETRYING"
    assert log.phases[0]["quality_gate_passed"] is False


def test_save_and_reload_roundtrip(tmp_path):
    log = PipelineStateLog()
    log.set_mission_brief({"objective": "y"})
    log.append_phase(
        phase_number=1,
        phase_name="Phase 1",
        status="COMPLETE",
        key_decisions=[],
        reasoning_summary="",
        output_summary="",
        quality_gate_passed=True,
    )
    log.mark_complete()

    path = tmp_path / "state.json"
    log.save(path)

    data = json.loads(path.read_text())
    reloaded = PipelineStateLog.from_dict(data)
    assert reloaded.overall_status == "COMPLETE"
    assert reloaded.mission_brief["objective"] == "y"
    assert reloaded.phases[0]["phase_number"] == 1


def test_retry_context_builder_exposes_failure_reason():
    from core.quality_gates import GateResult
    from core.retry import build_retry_context

    ctx = build_retry_context(
        attempt=2,
        previous_output={"phase": 1, "status": "COMPLETE"},
        gate_result=GateResult(passed=False, failure_reason="missing X"),
    )
    assert ctx["attempt"] == 2
    assert ctx["quality_gate_failure_reason"] == "missing X"
    assert "missing X" in ctx["specific_instruction"]
