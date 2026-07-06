"""Orchestrator routing for the senior-analyst phases: Phase 0 quick-answer
skip, Phase 6.5 red-team BLOCK, and Phase 9 knowledge-base persistence."""
from __future__ import annotations

import copy
import json

import pytest

from orchestrator.orchestrator import DataAnalystOrchestrator


class FakeResult:
    def __init__(self, payload: dict):
        self.output = payload


def _orch(tmp_path) -> DataAnalystOrchestrator:
    orch = DataAnalystOrchestrator(
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "outputs",
        verbose=False,
    )
    orch.knowledge_dir = tmp_path / "knowledge_base"
    return orch


def test_phase0_quick_lookup_skips_pipeline(tmp_path, monkeypatch, valid_phase0_output):
    orch = _orch(tmp_path)

    out0 = copy.deepcopy(valid_phase0_output)
    out0["complexity"] = "QUICK_LOOKUP"
    out0["route"] = "SKIP_TO_QUICK_ANSWER"
    out0["quick_answer_draft"] = "SELECT count(*) FROM users WHERE churned;"

    monkeypatch.setattr("agents.phase0_triage.run", lambda packet: FakeResult(out0))

    calls = {"phase1": 0}

    def fail_if_called(packet):  # pragma: no cover - the assertion is the point
        calls["phase1"] += 1
        raise AssertionError("Phase 1 must not run on the quick-answer route")

    monkeypatch.setattr("agents.phase1_requirements.run", fail_if_called)
    monkeypatch.setattr(
        "orchestrator.orchestrator.DataAnalystOrchestrator._run_quick_answer",
        lambda self, brief, out: "**Quick answer:** run the query below.",
    )

    result = orch.run(
        objective="How many users churned last month?",
        data_source_description="warehouse.users",
        stakeholder_type="product team",
    )

    assert calls["phase1"] == 0
    assert result.blocked_phase is None
    assert result.final_report and "Quick answer" in result.final_report
    assert result.pipeline_state_log["pipeline_state"]["overall_status"] == "COMPLETE"


def test_phase65_block_verdict_halts_pipeline(
    tmp_path, monkeypatch, valid_phase65_output
):
    orch = _orch(tmp_path)

    out65 = copy.deepcopy(valid_phase65_output)
    out65["verdict"] = "BLOCK"
    out65["required_revisions"] = [
        "Re-run Phase 6 with the reseller cohort excluded before any churn claim."
    ]

    monkeypatch.setattr("agents.phase65_redteam.run", lambda packet: FakeResult(out65))

    def fail_if_called(packet):  # pragma: no cover
        raise AssertionError("Phase 7 must not run after a red-team BLOCK")

    monkeypatch.setattr("agents.phase7_visualisation.run", fail_if_called)

    result = orch.run(
        objective="x",
        data_source_description="y",
        stakeholder_type="z",
        phases_to_run=[6.5, 7],
    )

    assert result.blocked_phase == 6.5
    last = result.pipeline_state_log["pipeline_state"]["phases"][-1]
    assert last["failure_reason"] == "RED_TEAM_BLOCK"
    assert "reseller" in last["output_summary"]


def test_phase9_persists_knowledge_base_entry(
    tmp_path, monkeypatch, valid_phase9_output
):
    orch = _orch(tmp_path)
    monkeypatch.setattr(
        "agents.phase9_monitoring.run", lambda packet: FakeResult(valid_phase9_output)
    )

    result = orch.run(
        objective="Analyse Q3 churn in our SaaS product",
        data_source_description="warehouse",
        stakeholder_type="product team",
        phases_to_run=[9],
    )

    assert result.blocked_phase is None
    entries_path = orch.knowledge_dir / "entries.jsonl"
    assert entries_path.exists()
    lines = entries_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["question"] == valid_phase9_output["knowledge_base_entry"]["question"]
    assert entry["objective"] == "Analyse Q3 churn in our SaaS product"
    assert entry["recorded_at"]

    # And the next run recalls it.
    recalled = orch._load_knowledge_base()
    assert len(recalled) == 1
    assert recalled[0]["question"] == entry["question"]
