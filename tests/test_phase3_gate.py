"""Phase 3 quality-gate tests."""
from __future__ import annotations

import copy

from core.quality_gates import check_gate, gate_phase_3


def test_phase3_gate_passes_for_valid_output(valid_phase3_output, phase3_context):
    result = check_gate(3, valid_phase3_output, phase3_context)
    assert result.passed, result.failure_reason


def test_phase3_gate_fails_on_null_check_failure(valid_phase3_output, phase3_context):
    out = copy.deepcopy(valid_phase3_output)
    out["validation_suite"]["null_check"] = "FAILED"
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "null_check" in result.failure_reason


def test_phase3_gate_fails_with_empty_change_log(valid_phase3_output, phase3_context):
    out = copy.deepcopy(valid_phase3_output)
    out["change_log"] = []
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "change_log" in result.failure_reason


def test_phase3_gate_fails_on_row_loss_above_20pct(valid_phase3_output, phase3_context):
    out = copy.deepcopy(valid_phase3_output)
    out["validation_suite"]["row_loss_pct"] = 24.5
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "row_loss_pct" in result.failure_reason


def test_phase3_gate_fails_when_critical_anomaly_has_no_cleaning_decision(
    valid_phase3_output, phase3_context
):
    out = copy.deepcopy(valid_phase3_output)
    out["anomaly_taxonomy"].append({
        "column": "users.never_cleaned",
        "issue": "type mismatch",
        "type": "STRUCTURAL",
        "severity": "CRITICAL",
    })
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "never_cleaned" in result.failure_reason


def test_phase3_gate_allows_unhandled_note_severity_anomaly(
    valid_phase3_output, phase3_context
):
    # NOTE-severity anomalies are documentation-only — no cleaning required.
    out = copy.deepcopy(valid_phase3_output)
    out["anomaly_taxonomy"].append({
        "column": "users.benign",
        "issue": "harmless quirk",
        "type": "STRUCTURAL",
        "severity": "NOTE",
    })
    result = gate_phase_3(out, phase3_context)
    assert result.passed, result.failure_reason


def test_phase3_gate_fails_when_cleaning_decision_missing_reasoning(
    valid_phase3_output, phase3_context
):
    out = copy.deepcopy(valid_phase3_output)
    out["cleaning_decisions"][0]["reasoning"] = ""
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "cleaning_decisions" in result.failure_reason


def test_phase3_gate_fails_when_bias_audit_missing(valid_phase3_output, phase3_context):
    out = copy.deepcopy(valid_phase3_output)
    del out["bias_audit"]["risks_found"]
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "bias_audit" in result.failure_reason


def test_phase3_gate_fails_on_invalid_bias_severity(valid_phase3_output, phase3_context):
    out = copy.deepcopy(valid_phase3_output)
    out["bias_audit"]["severity"] = "EXTREME"
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "severity" in result.failure_reason


def test_phase3_gate_fails_with_empty_clean_schema(valid_phase3_output, phase3_context):
    out = copy.deepcopy(valid_phase3_output)
    out["clean_schema"] = []
    result = gate_phase_3(out, phase3_context)
    assert not result.passed
    assert "clean_schema" in result.failure_reason
