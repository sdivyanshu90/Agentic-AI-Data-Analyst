"""Phase 2 quality-gate tests.

Covers happy path + each distinct failure clause, including the cross-phase
invariant that every Phase 1 P1 sub-question has a data_source_map entry.
"""
from __future__ import annotations

import copy

import pytest

from core.quality_gates import check_gate, gate_phase_2


# ---------- happy path ----------


def test_phase2_gate_passes_for_valid_output(valid_phase2_output, phase2_context):
    result = check_gate(2, valid_phase2_output, phase2_context)
    assert result.passed, result.failure_reason


# ---------- data_source_map ----------


def test_phase2_gate_fails_when_data_source_map_empty(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    out["data_source_map"] = []
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "data_source_map" in result.failure_reason


def test_phase2_gate_fails_without_confirmed_source(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    for s in out["data_source_map"]:
        s["availability"] = "ASSUMED"
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "CONFIRMED" in result.failure_reason


def test_phase2_gate_fails_on_invalid_availability(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    out["data_source_map"][0]["availability"] = "MAYBE"
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "availability" in result.failure_reason


def test_phase2_gate_fails_when_source_missing_reasoning(
    valid_phase2_output, phase2_context
):
    out = copy.deepcopy(valid_phase2_output)
    out["data_source_map"][0]["reasoning"] = ""
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "reasoning" in result.failure_reason


# ---------- governance ----------


def test_phase2_gate_requires_governance_flags_key(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    del out["governance_flags"]
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "governance_flags" in result.failure_reason


def test_phase2_gate_fails_on_pii_without_mitigation(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    out["governance_flags"][0]["mitigation"] = ""
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "PII" in result.failure_reason


def test_phase2_gate_accepts_empty_governance_flags(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    out["governance_flags"] = []
    # Removing PII mitigation requirement only kicks in when there are PII flags.
    result = gate_phase_2(out, phase2_context)
    assert result.passed, result.failure_reason


# ---------- extraction plan & completeness ----------


def test_phase2_gate_fails_with_empty_extraction_plan(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    out["extraction_plan"] = []
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "extraction_plan" in result.failure_reason


def test_phase2_gate_fails_when_extraction_missing_reasoning(
    valid_phase2_output, phase2_context
):
    out = copy.deepcopy(valid_phase2_output)
    out["extraction_plan"][0]["reasoning"] = ""
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "extraction_plan" in result.failure_reason


def test_phase2_gate_fails_with_empty_completeness(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    out["completeness_assessment"] = []
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "completeness_assessment" in result.failure_reason


def test_phase2_gate_fails_with_empty_data_dictionary(valid_phase2_output, phase2_context):
    out = copy.deepcopy(valid_phase2_output)
    out["data_dictionary"] = []
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "data_dictionary" in result.failure_reason


# ---------- cross-phase invariant ----------


def test_phase2_gate_fails_when_p1_sub_question_unmapped(
    valid_phase2_output, phase2_context
):
    # Phase 1 sample has three P1 sub-questions: SQ1, SQ2, SQ3.
    # Drop SQ3 from data_source_map → gate must flag it.
    out = copy.deepcopy(valid_phase2_output)
    out["data_source_map"] = [s for s in out["data_source_map"] if s["sub_question_id"] != "SQ3"]
    result = gate_phase_2(out, phase2_context)
    assert not result.passed
    assert "SQ3" in result.failure_reason


def test_phase2_gate_passes_when_only_p2_p3_unmapped(valid_phase2_output, phase2_context):
    # The fixture covers P1 only (SQ1–SQ3); P2/P3 (SQ4, SQ5) absent is fine.
    result = gate_phase_2(valid_phase2_output, phase2_context)
    assert result.passed, result.failure_reason


def test_phase2_gate_works_without_context(valid_phase2_output):
    # When no context is supplied, the cross-phase check is skipped gracefully.
    result = gate_phase_2(valid_phase2_output, None)
    assert result.passed, result.failure_reason
