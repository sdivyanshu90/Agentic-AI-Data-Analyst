"""Validate the example Phase 1 output and pipeline state against their schemas."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_phase1_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase1.json")
    Validator = jsonschema.Draft202012Validator
    Validator.check_schema(schema)


def test_sample_phase1_output_validates(valid_phase1_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase1.json")
    jsonschema.validate(valid_phase1_output, schema)


def test_phase2_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase2.json")
    Validator = jsonschema.Draft202012Validator
    Validator.check_schema(schema)


def test_sample_phase2_output_validates(valid_phase2_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase2.json")
    jsonschema.validate(valid_phase2_output, schema)


def test_phase2_schema_rejects_invalid_availability(valid_phase2_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase2.json")
    bad = _copy.deepcopy(valid_phase2_output)
    bad["data_source_map"][0]["availability"] = "TOTALLY_AVAILABLE"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase3_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase3.json")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_sample_phase3_output_validates(valid_phase3_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase3.json")
    jsonschema.validate(valid_phase3_output, schema)


def test_phase3_schema_rejects_invalid_severity(valid_phase3_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase3.json")
    bad = _copy.deepcopy(valid_phase3_output)
    bad["bias_audit"]["severity"] = "EXTREME"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase4_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase4.json")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_sample_phase4_output_validates(valid_phase4_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase4.json")
    jsonschema.validate(valid_phase4_output, schema)


def test_phase4_schema_rejects_bad_hypothesis_id(valid_phase4_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase4.json")
    bad = _copy.deepcopy(valid_phase4_output)
    bad["hypotheses"][0]["id"] = "Hypothesis-One"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase5_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase5.json")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_sample_phase5_output_validates(valid_phase5_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase5.json")
    jsonschema.validate(valid_phase5_output, schema)


def test_phase5_schema_rejects_string_p_value(valid_phase5_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase5.json")
    bad = _copy.deepcopy(valid_phase5_output)
    bad["tests_conducted"][0]["p_value"] = "0.001"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase6_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase6.json")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_sample_phase6_output_validates(valid_phase6_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase6.json")
    jsonschema.validate(valid_phase6_output, schema)


def test_phase6_schema_rejects_invalid_root_status(valid_phase6_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase6.json")
    bad = _copy.deepcopy(valid_phase6_output)
    bad["root_cause_chains"][0]["root_cause"]["status"] = "DEFINITELY"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase7_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase7.json")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_sample_phase7_output_validates(valid_phase7_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase7.json")
    jsonschema.validate(valid_phase7_output, schema)


def test_phase7_schema_rejects_invalid_dashboard_type(valid_phase7_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase7.json")
    bad = _copy.deepcopy(valid_phase7_output)
    bad["dashboard_architecture"]["dashboard_type"] = "STRATEGIC"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase8_schema_is_valid_jsonschema():
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase8.json")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_sample_phase8_output_validates(valid_phase8_output):
    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase8.json")
    jsonschema.validate(valid_phase8_output, schema)


def test_phase8_schema_rejects_invalid_summary_status(valid_phase8_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase8.json")
    bad = _copy.deepcopy(valid_phase8_output)
    bad["phase_8_summary"]["status"] = "ABORTED"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase8_schema_rejects_missing_final_report(valid_phase8_output):
    import copy as _copy

    schema = _load(SCHEMAS_DIR / "phase_outputs" / "phase8.json")
    bad = _copy.deepcopy(valid_phase8_output)
    del bad["final_report"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_mission_brief_schema_validates(sample_mission_brief):
    schema = _load(SCHEMAS_DIR / "mission_brief.json")
    jsonschema.validate(sample_mission_brief, schema)


def test_pipeline_state_schema_validates():
    schema = _load(SCHEMAS_DIR / "pipeline_state_log.json")
    sample = {
        "pipeline_state": {
            "mission_brief": {"objective": "x"},
            "current_phase": 1,
            "overall_status": "IN_PROGRESS",
            "phases": [
                {
                    "phase_number": 1,
                    "phase_name": "Stakeholder Requirement Gathering",
                    "status": "COMPLETE",
                    "attempt_count": 1,
                    "key_decisions": ["Classified as Descriptive"],
                    "reasoning_summary": "ok",
                    "output_summary": "5 sub-questions",
                    "quality_gate_passed": True,
                    "timestamp": "2026-05-19T10:00:00Z",
                }
            ],
        }
    }
    jsonschema.validate(sample, schema)


def test_pipeline_state_rejects_unknown_status():
    schema = _load(SCHEMAS_DIR / "pipeline_state_log.json")
    bad = {
        "pipeline_state": {
            "mission_brief": {},
            "current_phase": 1,
            "overall_status": "FROZEN",  # invalid
            "phases": [],
        }
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
