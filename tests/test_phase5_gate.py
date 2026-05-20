"""Phase 5 quality-gate tests."""
from __future__ import annotations

import copy

from core.quality_gates import check_gate, gate_phase_5


def test_phase5_gate_passes_for_valid_output(valid_phase5_output, phase5_context):
    result = check_gate(5, valid_phase5_output, phase5_context)
    assert result.passed, result.failure_reason


def test_phase5_gate_fails_with_no_tests(valid_phase5_output, phase5_context):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"] = []
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "tests_conducted" in result.failure_reason


def test_phase5_gate_fails_on_null_p_value(valid_phase5_output, phase5_context):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][0]["p_value"] = None
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "p_value" in result.failure_reason


def test_phase5_gate_fails_on_string_p_value(valid_phase5_output, phase5_context):
    # CLAUDE.md: p-values must be floats, not strings.
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][0]["p_value"] = "0.001"
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "p_value" in result.failure_reason


def test_phase5_gate_fails_on_out_of_range_p_value(valid_phase5_output, phase5_context):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][0]["p_value"] = 1.5
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "p_value" in result.failure_reason


def test_phase5_gate_fails_on_invalid_result(valid_phase5_output, phase5_context):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][0]["result"] = "PROVEN"
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "result" in result.failure_reason


def test_phase5_gate_fails_on_invalid_practical_significance(
    valid_phase5_output, phase5_context
):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][0]["practical_significance"] = "ENORMOUS"
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "practical_significance" in result.failure_reason


def test_phase5_gate_fails_on_missing_reasoning(valid_phase5_output, phase5_context):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][0]["test_selection_reasoning"] = ""
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "test_selection_reasoning" in result.failure_reason


def test_phase5_gate_fails_on_invalid_power_flag(valid_phase5_output, phase5_context):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][0]["power_analysis"]["power_flag"] = "MAYBE"
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "power_flag" in result.failure_reason


def test_phase5_gate_fails_on_duplicate_hypothesis_id(
    valid_phase5_output, phase5_context
):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"][1]["hypothesis_id"] = out["tests_conducted"][0]["hypothesis_id"]
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "duplicate" in result.failure_reason.lower()


def test_phase5_gate_requires_mtc_when_more_than_three_tests(
    valid_phase5_output, phase5_context
):
    # CLAUDE.md: multiple_testing_correction.applied required when n>3.
    out = copy.deepcopy(valid_phase5_output)
    out["multiple_testing_correction"]["applied"] = False
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "multiple_testing_correction" in result.failure_reason


def test_phase5_gate_allows_no_mtc_for_three_or_fewer_tests(
    valid_phase5_output, phase5_context
):
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"] = out["tests_conducted"][:3]
    out["findings_summary"] = out["findings_summary"][:3]
    out["multiple_testing_correction"]["applied"] = False
    out["multiple_testing_correction"]["method"] = "None"
    out["multiple_testing_correction"]["hypotheses_surviving_correction"] = []
    # Match the Phase 4 handoff: drop H4 from the context so the cross-phase
    # coverage check is satisfied for this 3-test scenario.
    ctx = copy.deepcopy(phase5_context)
    ctx["prior_outputs"][4]["phase_5_handoff"]["hypotheses_to_test"] = ["H1", "H2", "H3"]
    ctx["prior_outputs"][4]["hypotheses"] = [
        h for h in ctx["prior_outputs"][4]["hypotheses"] if h["id"] != "H4"
    ]
    result = gate_phase_5(out, ctx)
    assert result.passed, result.failure_reason


def test_phase5_gate_fails_when_findings_missing_test(
    valid_phase5_output, phase5_context
):
    out = copy.deepcopy(valid_phase5_output)
    out["findings_summary"] = out["findings_summary"][:-1]
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "findings_summary" in result.failure_reason


def test_phase5_gate_fails_when_phase4_hypothesis_untested(
    valid_phase5_output, phase5_context
):
    # H4 is declared in Phase 4's handoff but we drop it from tests_conducted.
    out = copy.deepcopy(valid_phase5_output)
    out["tests_conducted"] = [t for t in out["tests_conducted"] if t["hypothesis_id"] != "H4"]
    out["findings_summary"] = [f for f in out["findings_summary"] if f["hypothesis_id"] != "H4"]
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "H4" in result.failure_reason


def test_phase5_gate_works_without_context(valid_phase5_output):
    # Cross-phase check skipped when no context provided.
    result = gate_phase_5(valid_phase5_output, None)
    assert result.passed, result.failure_reason
