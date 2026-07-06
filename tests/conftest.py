"""Shared pytest fixtures and path setup."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def valid_phase1_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase1_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase2_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase2_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase3_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase3_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase4_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase4_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase5_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase5_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase6_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase6_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase7_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase7_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase8_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase8_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase0_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase0_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase65_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase65_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def valid_phase9_output() -> dict:
    sample_path = REPO_ROOT / "examples" / "sample_run" / "dry_run_phase9_output.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


@pytest.fixture
def phase2_context(sample_mission_brief, valid_phase1_output) -> dict:
    """Context-packet-shaped fixture that the Phase 2 gate consumes."""
    return {
        "mission_brief": sample_mission_brief["mission_brief"],
        "prior_outputs": {1: valid_phase1_output},
        "pipeline_state": {"current_phase": 1, "phases": []},
    }


@pytest.fixture
def phase3_context(sample_mission_brief, valid_phase1_output, valid_phase2_output) -> dict:
    return {
        "mission_brief": sample_mission_brief["mission_brief"],
        "prior_outputs": {1: valid_phase1_output, 2: valid_phase2_output},
        "pipeline_state": {"current_phase": 2, "phases": []},
    }


@pytest.fixture
def phase4_context(
    sample_mission_brief, valid_phase1_output, valid_phase2_output, valid_phase3_output
) -> dict:
    return {
        "mission_brief": sample_mission_brief["mission_brief"],
        "prior_outputs": {
            1: valid_phase1_output,
            2: valid_phase2_output,
            3: valid_phase3_output,
        },
        "pipeline_state": {"current_phase": 3, "phases": []},
    }


@pytest.fixture
def phase5_context(
    sample_mission_brief,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
    valid_phase4_output,
) -> dict:
    return {
        "mission_brief": sample_mission_brief["mission_brief"],
        "prior_outputs": {
            1: valid_phase1_output,
            2: valid_phase2_output,
            3: valid_phase3_output,
            4: valid_phase4_output,
        },
        "pipeline_state": {"current_phase": 4, "phases": []},
    }


@pytest.fixture
def phase6_context(
    sample_mission_brief,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
    valid_phase4_output,
    valid_phase5_output,
) -> dict:
    return {
        "mission_brief": sample_mission_brief["mission_brief"],
        "prior_outputs": {
            1: valid_phase1_output,
            2: valid_phase2_output,
            3: valid_phase3_output,
            4: valid_phase4_output,
            5: valid_phase5_output,
        },
        "pipeline_state": {"current_phase": 5, "phases": []},
    }


@pytest.fixture
def phase7_context(
    sample_mission_brief,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
    valid_phase4_output,
    valid_phase5_output,
    valid_phase6_output,
) -> dict:
    return {
        "mission_brief": sample_mission_brief["mission_brief"],
        "prior_outputs": {
            1: valid_phase1_output,
            2: valid_phase2_output,
            3: valid_phase3_output,
            4: valid_phase4_output,
            5: valid_phase5_output,
            6: valid_phase6_output,
        },
        "pipeline_state": {"current_phase": 6, "phases": []},
    }


@pytest.fixture
def phase8_context(
    sample_mission_brief,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
    valid_phase4_output,
    valid_phase5_output,
    valid_phase6_output,
    valid_phase7_output,
) -> dict:
    return {
        "mission_brief": sample_mission_brief["mission_brief"],
        "prior_outputs": {
            1: valid_phase1_output,
            2: valid_phase2_output,
            3: valid_phase3_output,
            4: valid_phase4_output,
            5: valid_phase5_output,
            6: valid_phase6_output,
            7: valid_phase7_output,
        },
        "pipeline_state": {"current_phase": 7, "phases": []},
    }


@pytest.fixture
def sample_mission_brief() -> dict:
    return {
        "mission_brief": {
            "objective": "Analyse Q3 churn in our SaaS product",
            "business_domain": "SaaS",
            "stakeholder_type": "product team",
            "data_source_description": "PostgreSQL DB: users, events, subscriptions",
            "constraints": {
                "time": "2 weeks",
                "tools": "SQL + Python",
                "privacy": "PII must be anonymised",
            },
            "success_looks_like": "Product team can pinpoint the top 3 drivers of Q3 churn",
            "assumptions": [],
        }
    }
