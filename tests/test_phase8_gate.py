"""Phase 8 quality-gate tests."""
from __future__ import annotations

import copy

from core.quality_gates import check_gate, gate_phase_8


def test_phase8_gate_passes_for_valid_output(valid_phase8_output, phase8_context):
    result = check_gate(8, valid_phase8_output, phase8_context)
    assert result.passed, result.failure_reason


def test_phase8_gate_fails_with_no_sub_questions_answered(
    valid_phase8_output, phase8_context
):
    out = copy.deepcopy(valid_phase8_output)
    out["phase_8_summary"]["sub_questions_answered"] = []
    result = gate_phase_8(out, phase8_context)
    assert not result.passed
    assert "sub_questions_answered" in result.failure_reason


def test_phase8_gate_fails_when_self_check_has_failures(
    valid_phase8_output, phase8_context
):
    out = copy.deepcopy(valid_phase8_output)
    out["phase_8_summary"]["quality_gate_checks_failed"] = 2
    result = gate_phase_8(out, phase8_context)
    assert not result.passed
    assert "quality_gate_checks_failed" in result.failure_reason


def test_phase8_gate_fails_when_summary_missing(phase8_context):
    out = {"phase": 8, "phase_name": "x", "status": "COMPLETE", "final_report": "..."}
    result = gate_phase_8(out, phase8_context)
    assert not result.passed
    assert "sub_questions_answered" in result.failure_reason
