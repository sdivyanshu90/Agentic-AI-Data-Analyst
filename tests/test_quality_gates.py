"""Quality-gate tests focused on Phase 1.

The gate checks both the phase output (sub_questions, success_definition,
reasoning fields) AND the mission brief in the context packet (objective).
We exercise the happy path plus every distinct failure clause.
"""
from __future__ import annotations

import copy

import pytest

from core.quality_gates import check_gate, gate_phase_1


# ---------- happy path ----------


def test_phase1_gate_passes_for_valid_output(valid_phase1_output, sample_mission_brief):
    result = check_gate(1, valid_phase1_output, sample_mission_brief)
    assert result.passed, result.failure_reason


# ---------- mission brief preconditions ----------


def test_phase1_gate_fails_when_mission_brief_objective_missing(valid_phase1_output):
    bad_ctx = {"mission_brief": {"objective": ""}}
    result = gate_phase_1(valid_phase1_output, bad_ctx)
    assert not result.passed
    assert "objective" in result.failure_reason.lower()


# ---------- sub_questions ----------


def test_phase1_gate_fails_with_fewer_than_three_sub_questions(
    valid_phase1_output, sample_mission_brief
):
    out = copy.deepcopy(valid_phase1_output)
    out["sub_questions"] = out["sub_questions"][:2]
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "sub_questions" in result.failure_reason


def test_phase1_gate_fails_when_sub_question_missing_reasoning(
    valid_phase1_output, sample_mission_brief
):
    out = copy.deepcopy(valid_phase1_output)
    out["sub_questions"][0]["reasoning"] = ""
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "reasoning" in result.failure_reason


def test_phase1_gate_fails_on_invalid_priority(valid_phase1_output, sample_mission_brief):
    out = copy.deepcopy(valid_phase1_output)
    out["sub_questions"][0]["priority"] = "URGENT"
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "priority" in result.failure_reason


# ---------- success definition ----------


def test_phase1_gate_fails_with_blank_success_definition(
    valid_phase1_output, sample_mission_brief
):
    out = copy.deepcopy(valid_phase1_output)
    out["success_definition"] = "   "
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "success_definition" in result.failure_reason


# ---------- stakeholder profile ----------


def test_phase1_gate_fails_without_audience(valid_phase1_output, sample_mission_brief):
    out = copy.deepcopy(valid_phase1_output)
    out["stakeholder_profile"]["primary_audience"] = ""
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "primary_audience" in result.failure_reason


def test_phase1_gate_fails_on_bad_tolerance(valid_phase1_output, sample_mission_brief):
    out = copy.deepcopy(valid_phase1_output)
    out["stakeholder_profile"]["technical_tolerance"] = "Extreme"
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "technical_tolerance" in result.failure_reason


# ---------- audit-trail reasoning fields ----------


def test_phase1_gate_fails_when_classification_reasoning_missing(
    valid_phase1_output, sample_mission_brief
):
    out = copy.deepcopy(valid_phase1_output)
    out["analysis_classification"]["reasoning"] = ""
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "analysis_classification" in result.failure_reason


def test_phase1_gate_fails_when_decoding_reasoning_missing(
    valid_phase1_output, sample_mission_brief
):
    out = copy.deepcopy(valid_phase1_output)
    out["stakeholder_decoding"]["reasoning"] = ""
    result = gate_phase_1(out, sample_mission_brief)
    assert not result.passed
    assert "stakeholder_decoding" in result.failure_reason


# ---------- gate-registry sanity ----------


def test_check_gate_unknown_phase_raises():
    with pytest.raises(KeyError):
        check_gate(99, {}, None)


def test_gate_result_is_truthy_when_passed():
    result = gate_phase_1(
        {
            "sub_questions": [
                {"id": "SQ1", "question": "Q1?", "priority": "P1", "reasoning": "r"},
                {"id": "SQ2", "question": "Q2?", "priority": "P2", "reasoning": "r"},
                {"id": "SQ3", "question": "Q3?", "priority": "P3", "reasoning": "r"},
            ],
            "success_definition": "Stakeholders can act.",
            "stakeholder_profile": {
                "primary_audience": "execs",
                "technical_tolerance": "Low",
            },
            "analysis_classification": {"types": ["Descriptive"], "reasoning": "r"},
            "stakeholder_decoding": {"reasoning": "r"},
        },
        {"mission_brief": {"objective": "X"}},
    )
    assert bool(result) is True
