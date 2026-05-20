"""Phase 6 quality-gate tests."""
from __future__ import annotations

import copy

from core.quality_gates import check_gate, gate_phase_6


def test_phase6_gate_passes_for_valid_output(valid_phase6_output, phase6_context):
    result = check_gate(6, valid_phase6_output, phase6_context)
    assert result.passed, result.failure_reason


def test_phase6_gate_fails_on_empty_chains(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["root_cause_chains"] = []
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "root_cause_chains" in result.failure_reason


def test_phase6_gate_fails_when_symptom_missing(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["root_cause_chains"][0]["symptom"] = ""
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "symptom" in result.failure_reason


def test_phase6_gate_fails_when_proximate_evidence_missing(
    valid_phase6_output, phase6_context
):
    out = copy.deepcopy(valid_phase6_output)
    out["root_cause_chains"][0]["proximate_cause"]["evidence"] = ""
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "proximate_cause" in result.failure_reason


def test_phase6_gate_fails_when_root_evidence_missing(
    valid_phase6_output, phase6_context
):
    out = copy.deepcopy(valid_phase6_output)
    out["root_cause_chains"][0]["root_cause"]["evidence"] = ""
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "root_cause" in result.failure_reason


def test_phase6_gate_fails_on_invalid_root_cause_status(
    valid_phase6_output, phase6_context
):
    out = copy.deepcopy(valid_phase6_output)
    out["root_cause_chains"][0]["root_cause"]["status"] = "MAYBE"
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "status" in result.failure_reason


def test_phase6_gate_fails_when_hypothesised_lacks_data_needed(
    valid_phase6_output, phase6_context
):
    out = copy.deepcopy(valid_phase6_output)
    # First chain is HYPOTHESISED in our sample; blank the explainer.
    out["root_cause_chains"][0]["root_cause"]["data_needed_to_confirm"] = ""
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "data_needed_to_confirm" in result.failure_reason


def test_phase6_gate_fails_on_empty_insight_ranking(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["insight_ranking"] = []
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "insight_ranking" in result.failure_reason


def test_phase6_gate_fails_on_invalid_impact_level(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["insight_ranking"][0]["impact"] = "EXTREME"
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "impact" in result.failure_reason


def test_phase6_gate_fails_on_duplicate_ranks(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["insight_ranking"][1]["rank"] = out["insight_ranking"][0]["rank"]
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "rank" in result.failure_reason


def test_phase6_gate_fails_on_missing_method_reasoning(
    valid_phase6_output, phase6_context
):
    out = copy.deepcopy(valid_phase6_output)
    out["analyses"][0]["method_reasoning"] = ""
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "method_reasoning" in result.failure_reason


def test_phase6_gate_fails_when_p1_subquestion_unaddressed(
    valid_phase6_output, phase6_context
):
    # Phase 1's P1 sub-questions are SQ1, SQ2, SQ3.
    # Drop SQ3 from analyses AND from unanswered_subquestions → gate must flag it.
    out = copy.deepcopy(valid_phase6_output)
    out["analyses"] = [a for a in out["analyses"] if a["subquestion_id"] != "SQ3"]
    out["unanswered_subquestions"] = [
        u for u in out["unanswered_subquestions"] if u["subquestion_id"] != "SQ3"
    ]
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "SQ3" in result.failure_reason


def test_phase6_gate_allows_subquestion_via_unanswered(
    valid_phase6_output, phase6_context
):
    # Moving SQ3 from analyses to unanswered_subquestions should still pass.
    out = copy.deepcopy(valid_phase6_output)
    out["analyses"] = [a for a in out["analyses"] if a["subquestion_id"] != "SQ3"]
    out["unanswered_subquestions"].append({
        "subquestion_id": "SQ3",
        "reason": "Deferred for follow-up run",
        "status": "DEFERRED",
        "path_to_answer": "Re-run with extended window",
    })
    result = gate_phase_6(out, phase6_context)
    assert result.passed, result.failure_reason


def test_phase6_gate_works_without_context(valid_phase6_output):
    # Cross-phase check skipped when no context provided.
    result = gate_phase_6(valid_phase6_output, None)
    assert result.passed, result.failure_reason
