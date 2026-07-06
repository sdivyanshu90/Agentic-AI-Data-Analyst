"""Gates for the senior-analyst phases (0, 6.5, 9) and the rigour extensions
retro-fitted into Phases 4-6 (hypothesis provenance, evidence grades,
confound sweep, sensitivity analysis, external benchmarks)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.quality_gates import (
    check_gate,
    gate_phase_0,
    gate_phase_4,
    gate_phase_5,
    gate_phase_6,
    gate_phase_6_5,
    gate_phase_9,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"


# ---------- Phase 0 ----------


def test_phase0_gate_passes_for_valid_output(valid_phase0_output):
    result = check_gate(0, valid_phase0_output, None)
    assert result.passed, result.failure_reason


def test_phase0_gate_fails_on_invalid_complexity(valid_phase0_output):
    out = copy.deepcopy(valid_phase0_output)
    out["complexity"] = "MEGA_PROJECT"
    result = gate_phase_0(out)
    assert not result.passed
    assert "complexity" in result.failure_reason


def test_phase0_gate_never_skips_known_event_check(valid_phase0_output):
    """No confound candidates AND no calendar questions = skipped check."""
    out = copy.deepcopy(valid_phase0_output)
    out["confound_candidates"] = []
    out["calendar_questions_for_user"] = []
    result = gate_phase_0(out)
    assert not result.passed
    assert "never skipped" in result.failure_reason


def test_phase0_gate_allows_empty_candidates_with_questions(valid_phase0_output):
    out = copy.deepcopy(valid_phase0_output)
    out["confound_candidates"] = []
    out["calendar_questions_for_user"] = ["What changed in the window?"]
    assert gate_phase_0(out).passed


def test_phase0_gate_requires_descope_when_deadline_tight(valid_phase0_output):
    out = copy.deepcopy(valid_phase0_output)
    out["scope_and_feasibility"]["deadline_feasibility"] = "FEASIBLE_WITH_DESCOPING"
    out["scope_and_feasibility"]["descope_proposal"] = []
    result = gate_phase_0(out)
    assert not result.passed
    assert "descope" in result.failure_reason


def test_phase0_gate_quick_answer_route_needs_draft(valid_phase0_output):
    out = copy.deepcopy(valid_phase0_output)
    out["complexity"] = "QUICK_LOOKUP"
    out["route"] = "SKIP_TO_QUICK_ANSWER"
    out["quick_answer_draft"] = ""
    result = gate_phase_0(out)
    assert not result.passed
    assert "quick_answer_draft" in result.failure_reason


def test_phase0_gate_quick_route_requires_quick_complexity(valid_phase0_output):
    out = copy.deepcopy(valid_phase0_output)
    out["route"] = "SKIP_TO_QUICK_ANSWER"
    out["quick_answer_draft"] = "SELECT count(*) ..."
    # complexity stays DEEP_INVESTIGATION → contradiction
    result = gate_phase_0(out)
    assert not result.passed
    assert "QUICK_LOOKUP" in result.failure_reason


# ---------- Phase 4/5 provenance extensions ----------


def test_phase4_gate_requires_provenance(valid_phase4_output, phase4_context):
    out = copy.deepcopy(valid_phase4_output)
    del out["hypotheses"][0]["provenance"]
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "provenance" in result.failure_reason


def test_phase4_gate_emergent_must_be_data_derived(valid_phase4_output, phase4_context):
    out = copy.deepcopy(valid_phase4_output)
    emergent = [h for h in out["hypotheses"] if h["source"] == "EMERGENT"][0]
    emergent["provenance"] = "PRE_REGISTERED"
    result = gate_phase_4(out, phase4_context)
    assert not result.passed
    assert "DATA_DERIVED" in result.failure_reason


def test_phase5_gate_passes_for_valid_output(valid_phase5_output, phase5_context):
    result = gate_phase_5(valid_phase5_output, phase5_context)
    assert result.passed, result.failure_reason


def test_phase5_gate_blocks_data_derived_confirmatory_without_holdout(
    valid_phase5_output, phase5_context
):
    out = copy.deepcopy(valid_phase5_output)
    t = [x for x in out["tests_conducted"] if x["hypothesis_provenance"] == "DATA_DERIVED"][0]
    t["evidence_grade"] = "CONFIRMATORY"
    t["holdout_validation"] = "NONE"
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "EXPLORATORY" in result.failure_reason


def test_phase5_gate_allows_data_derived_confirmatory_with_holdout(
    valid_phase5_output, phase5_context
):
    out = copy.deepcopy(valid_phase5_output)
    t = [x for x in out["tests_conducted"] if x["hypothesis_provenance"] == "DATA_DERIVED"][0]
    t["evidence_grade"] = "CONFIRMATORY"
    t["holdout_validation"] = "Confirmed on the held-out August cohort (30% split)"
    result = gate_phase_5(out, phase5_context)
    assert result.passed, result.failure_reason


def test_phase5_gate_rejects_provenance_drift_from_phase4(
    valid_phase5_output, phase5_context
):
    """Silently relabelling a DATA_DERIVED hypothesis defeats the guard."""
    out = copy.deepcopy(valid_phase5_output)
    t = [x for x in out["tests_conducted"] if x["hypothesis_provenance"] == "DATA_DERIVED"][0]
    t["hypothesis_provenance"] = "PRE_REGISTERED"
    result = gate_phase_5(out, phase5_context)
    assert not result.passed
    assert "contradicts" in result.failure_reason


# ---------- Phase 6 sweep extensions ----------


def test_phase6_gate_passes_for_valid_output(valid_phase6_output, phase6_context):
    result = gate_phase_6(valid_phase6_output, phase6_context)
    assert result.passed, result.failure_reason


def test_phase6_gate_requires_confound_sweep(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["confound_sweep"] = []
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "confound_sweep" in result.failure_reason


def test_phase6_gate_rejects_silent_unswept_dimensions(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["confound_sweep"][0]["dimensions_swept"] = []
    out["confound_sweep"][0]["dimensions_not_sweepable"] = []
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "silence" in result.failure_reason


def test_phase6_gate_requires_known_event_check_when_phase0_present(
    valid_phase6_output, phase6_context, valid_phase0_output
):
    ctx = copy.deepcopy(phase6_context)
    ctx["prior_outputs"][0] = valid_phase0_output
    out = copy.deepcopy(valid_phase6_output)
    out["confound_sweep"][0]["known_event_check"] = []
    result = gate_phase_6(out, ctx)
    assert not result.passed
    assert "known_event_check" in result.failure_reason


def test_phase6_gate_requires_sensitivity_for_high_impact(
    valid_phase6_output, phase6_context
):
    out = copy.deepcopy(valid_phase6_output)
    out["sensitivity_analysis"] = []
    # fixture has HIGH-impact insights, so this must fail
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "sensitivity_analysis" in result.failure_reason


def test_phase6_gate_rejects_sourceless_benchmark(valid_phase6_output, phase6_context):
    out = copy.deepcopy(valid_phase6_output)
    out["external_benchmarks"] = [
        {
            "finding_ref": "H1",
            "benchmark_metric": "SaaS churn median",
            "benchmark_value": "3.5% monthly",
            "source": "",
            "comparison": "we are above it",
        }
    ]
    result = gate_phase_6(out, phase6_context)
    assert not result.passed
    assert "fabricate" in result.failure_reason


# ---------- Phase 6.5 ----------


def test_phase65_gate_passes_for_valid_output(valid_phase65_output):
    result = check_gate(6.5, valid_phase65_output, None)
    assert result.passed, result.failure_reason


def test_phase65_gate_requires_alternative_explanations(valid_phase65_output):
    out = copy.deepcopy(valid_phase65_output)
    out["alternative_explanations"] = []
    result = gate_phase_6_5(out)
    assert not result.passed
    assert "alternative_explanations" in result.failure_reason


def test_phase65_gate_revisions_required_with_that_verdict(valid_phase65_output):
    out = copy.deepcopy(valid_phase65_output)
    out["verdict"] = "PROCEED_WITH_REVISIONS"
    out["required_revisions"] = []
    result = gate_phase_6_5(out)
    assert not result.passed
    assert "required_revisions" in result.failure_reason


def test_phase65_gate_rejects_rubber_stamp_proceed(valid_phase65_output):
    """A review that flagged an overclaim cannot conclude plain PROCEED."""
    out = copy.deepcopy(valid_phase65_output)
    out["verdict"] = "PROCEED"
    result = gate_phase_6_5(out)  # fixture carries one overclaim flag
    assert not result.passed
    assert "contradicts" in result.failure_reason


def test_phase65_gate_allows_clean_proceed(valid_phase65_output):
    out = copy.deepcopy(valid_phase65_output)
    out["overclaim_flags"] = []
    out["verdict"] = "PROCEED"
    out["required_revisions"] = []
    result = gate_phase_6_5(out)
    assert result.passed, result.failure_reason


def test_phase65_gate_block_requires_revisions(valid_phase65_output):
    out = copy.deepcopy(valid_phase65_output)
    out["verdict"] = "BLOCK"
    out["required_revisions"] = ["", "  "]
    result = gate_phase_6_5(out)
    assert not result.passed


# ---------- Phase 9 ----------


def test_phase9_gate_passes_for_valid_output(valid_phase9_output):
    result = check_gate(9, valid_phase9_output, None)
    assert result.passed, result.failure_reason


def test_phase9_gate_rejects_generic_metric_without_checkin(valid_phase9_output):
    out = copy.deepcopy(valid_phase9_output)
    out["success_metrics"][0]["check_in_date"] = ""
    result = gate_phase_9(out)
    assert not result.passed
    assert "check_in_date" in result.failure_reason


def test_phase9_gate_requires_monitoring_specs(valid_phase9_output):
    out = copy.deepcopy(valid_phase9_output)
    out["monitoring_specs"] = []
    result = gate_phase_9(out)
    assert not result.passed
    assert "monitoring_specs" in result.failure_reason


def test_phase9_gate_requires_knowledge_base_entry(valid_phase9_output):
    out = copy.deepcopy(valid_phase9_output)
    out["knowledge_base_entry"]["question"] = ""
    result = gate_phase_9(out)
    assert not result.passed
    assert "knowledge_base_entry" in result.failure_reason


# ---------- Schema validation for the new phases ----------


jsonschema = pytest.importorskip("jsonschema")


@pytest.mark.parametrize(
    "schema_name,fixture_name",
    [
        ("phase0.json", "valid_phase0_output"),
        ("phase6_5.json", "valid_phase65_output"),
        ("phase9.json", "valid_phase9_output"),
    ],
)
def test_new_phase_samples_validate_against_schemas(schema_name, fixture_name, request):
    schema = json.loads(
        (SCHEMAS_DIR / "phase_outputs" / schema_name).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    output = request.getfixturevalue(fixture_name)
    jsonschema.validate(output, schema)
