"""Phase 7 quality-gate tests."""
from __future__ import annotations

import copy

from core.quality_gates import check_gate, gate_phase_7


def test_phase7_gate_passes_for_valid_output(valid_phase7_output, phase7_context):
    result = check_gate(7, valid_phase7_output, phase7_context)
    assert result.passed, result.failure_reason


def test_phase7_gate_fails_with_empty_specs(valid_phase7_output, phase7_context):
    out = copy.deepcopy(valid_phase7_output)
    out["visualisation_specs"] = []
    result = gate_phase_7(out, phase7_context)
    assert not result.passed
    assert "visualisation_specs" in result.failure_reason


def test_phase7_gate_fails_when_colourblind_unsafe(valid_phase7_output, phase7_context):
    out = copy.deepcopy(valid_phase7_output)
    out["accessibility_review"]["colourblind_safe"] = False
    result = gate_phase_7(out, phase7_context)
    assert not result.passed
    assert "colourblind_safe" in result.failure_reason


def test_phase7_gate_fails_when_wcag_contrast_unmet(valid_phase7_output, phase7_context):
    # CLAUDE.md: wcag_contrast_met=false blocks Phase 8.
    out = copy.deepcopy(valid_phase7_output)
    out["accessibility_review"]["wcag_contrast_met"] = False
    result = gate_phase_7(out, phase7_context)
    assert not result.passed
    assert "wcag_contrast_met" in result.failure_reason


def test_phase7_gate_fails_on_anti_pattern_without_correction(
    valid_phase7_output, phase7_context
):
    out = copy.deepcopy(valid_phase7_output)
    out["anti_pattern_audit"][0]["correction_applied"] = ""
    result = gate_phase_7(out, phase7_context)
    assert not result.passed
    assert "correction_applied" in result.failure_reason


def test_phase7_gate_fails_on_pie_chart_with_five_slices(
    valid_phase7_output, phase7_context
):
    # CLAUDE.md invariant #9: pie >4 slices forbidden.
    out = copy.deepcopy(valid_phase7_output)
    out["visualisation_specs"].append({
        "chart_name": "Acquisition channel mix pie",
        "purpose": "Channel composition",
        "chart_type": "Pie chart",
        "slice_count": 5,
        "data_source": {"table": "x", "columns": ["channel"]},
        "x_axis": {"field": "channel"},
        "alt_text": "Pie chart with 5 slices",
    })
    result = gate_phase_7(out, phase7_context)
    assert not result.passed
    assert "pie" in result.failure_reason.lower()


def test_phase7_gate_allows_pie_chart_with_four_slices(
    valid_phase7_output, phase7_context
):
    out = copy.deepcopy(valid_phase7_output)
    out["visualisation_specs"].append({
        "chart_name": "Voluntary vs involuntary churn mix",
        "purpose": "Churn type composition",
        "chart_type": "Pie chart",
        "slice_count": 3,
        "data_source": {"table": "x", "columns": ["churn_type"]},
        "x_axis": {"field": "churn_type"},
        "alt_text": "Pie chart with 3 slices",
    })
    result = gate_phase_7(out, phase7_context)
    assert result.passed, result.failure_reason


def test_phase7_gate_fails_on_chart_map_missing_reasoning(
    valid_phase7_output, phase7_context
):
    out = copy.deepcopy(valid_phase7_output)
    out["insight_to_chart_map"][0]["chart_reasoning"] = ""
    result = gate_phase_7(out, phase7_context)
    assert not result.passed
    assert "chart_reasoning" in result.failure_reason


def test_phase7_gate_fails_when_no_chart_headlines_handed_off(
    valid_phase7_output, phase7_context
):
    out = copy.deepcopy(valid_phase7_output)
    out["phase_8_handoff"]["chart_titles_as_insight_headlines"] = []
    result = gate_phase_7(out, phase7_context)
    assert not result.passed
    assert "chart_titles_as_insight_headlines" in result.failure_reason
