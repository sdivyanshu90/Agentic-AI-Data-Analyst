"""Phase 4 quality-gate tests."""
from __future__ import annotations

import copy

from core.quality_gates import check_gate, gate_phase_4


def test_phase4_gate_passes_for_valid_output(valid_phase4_output, phase4_context):
    result = check_gate(4, valid_phase4_output, phase4_context)
    assert result.passed, result.failure_reason


def test_phase4_gate_fails_with_fewer_than_two_hypotheses(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["hypotheses"] = out["hypotheses"][:1]
    out["phase_5_handoff"]["hypotheses_to_test"] = ["H1"]
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "hypotheses" in result.failure_reason


def test_phase4_gate_fails_when_hypothesis_missing_reasoning(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["hypotheses"][0]["reasoning"] = ""
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "reasoning" in result.failure_reason


def test_phase4_gate_fails_when_hypothesis_missing_expected_test_type(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["hypotheses"][0]["expected_test_type"] = ""
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "expected_test_type" in result.failure_reason


def test_phase4_gate_fails_on_invalid_hypothesis_id_format(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["hypotheses"][0]["id"] = "HYPO_ONE"
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "id" in result.failure_reason


def test_phase4_gate_fails_on_duplicate_hypothesis_id(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["hypotheses"][1]["id"] = out["hypotheses"][0]["id"]
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "duplicate" in result.failure_reason.lower()


def test_phase4_gate_fails_on_invalid_hypothesis_source(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["hypotheses"][0]["source"] = "MADE_UP"
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "source" in result.failure_reason


def test_phase4_gate_fails_on_empty_univariate(valid_phase4_output, phase4_context):
    out = copy.deepcopy(valid_phase4_output)
    out["univariate_analysis"] = []
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "univariate_analysis" in result.failure_reason


def test_phase4_gate_fails_on_bivariate_missing_reasoning(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["bivariate_analysis"][0]["reasoning"] = ""
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "bivariate_analysis" in result.failure_reason


def test_phase4_gate_fails_on_invalid_strength(valid_phase4_output, phase4_context):
    out = copy.deepcopy(valid_phase4_output)
    out["bivariate_analysis"][0]["strength"] = "MASSIVE"
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "strength" in result.failure_reason


def test_phase4_gate_fails_on_viz_missing_reasoning(valid_phase4_output, phase4_context):
    out = copy.deepcopy(valid_phase4_output)
    out["eda_visualisation_spec"][0]["reasoning"] = ""
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "eda_visualisation_spec" in result.failure_reason


def test_phase4_gate_fails_when_handoff_references_unknown_hypothesis(
    valid_phase4_output, phase4_context
):
    out = copy.deepcopy(valid_phase4_output)
    out["phase_5_handoff"]["hypotheses_to_test"].append("H99")
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "H99" in result.failure_reason


def test_phase4_gate_fails_with_empty_handoff_list(valid_phase4_output, phase4_context):
    out = copy.deepcopy(valid_phase4_output)
    out["phase_5_handoff"]["hypotheses_to_test"] = []
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "hypotheses_to_test" in result.failure_reason
