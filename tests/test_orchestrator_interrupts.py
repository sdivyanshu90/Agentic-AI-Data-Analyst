"""Orchestrator interrupt tests: row-loss confirmation and PARTIAL status."""
from __future__ import annotations

import copy

import pytest

from orchestrator.orchestrator import (
    DataAnalystOrchestrator,
    PhaseBlockedError,
)


class FakeResult:
    def __init__(self, payload: dict):
        self.output = payload


def _run_phase3_with_outputs(
    orch: DataAnalystOrchestrator,
    phase1_out: dict,
    phase2_out: dict,
    phase3_out: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "agents.phase1_requirements.run", lambda packet: FakeResult(phase1_out)
    )
    monkeypatch.setattr(
        "agents.phase2_extraction.run", lambda packet: FakeResult(phase2_out)
    )
    monkeypatch.setattr(
        "agents.phase3_cleaning.run", lambda packet: FakeResult(phase3_out)
    )
    return orch.run(
        objective="x",
        data_source_description="y",
        stakeholder_type="z",
        phases_to_run=[1, 2, 3],
    )


def test_row_loss_above_threshold_prompts_user_and_blocks_on_no(
    tmp_path,
    monkeypatch,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
):
    orch = DataAnalystOrchestrator(
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "outputs",
        verbose=False,
    )
    # Force an above-threshold but below-gate-fail row loss.
    out3 = copy.deepcopy(valid_phase3_output)
    out3["validation_suite"]["row_loss_pct"] = 15.0  # > 10% alert, < 20% block

    prompted: dict = {}

    def fake_confirm(question: str) -> bool:
        prompted["q"] = question
        return False  # user says no

    orch.user_confirm = fake_confirm

    result = _run_phase3_with_outputs(
        orch, valid_phase1_output, valid_phase2_output, out3, monkeypatch
    )

    assert result.blocked_phase == 3
    assert "15.0" in prompted["q"]
    last = result.pipeline_state_log["pipeline_state"]["phases"][-1]
    assert last["status"] == "FAILED"
    assert last["failure_reason"] == "USER_ROW_LOSS_ABORT"


def test_row_loss_below_threshold_does_not_prompt(
    tmp_path,
    monkeypatch,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
):
    orch = DataAnalystOrchestrator(
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "outputs",
        verbose=False,
    )
    # Sample has 0.76% row loss — well under the 10% alert threshold.
    called: dict = {"n": 0}

    def fake_confirm(question: str) -> bool:
        called["n"] += 1
        return True

    orch.user_confirm = fake_confirm

    result = _run_phase3_with_outputs(
        orch,
        valid_phase1_output,
        valid_phase2_output,
        valid_phase3_output,
        monkeypatch,
    )
    assert result.blocked_phase is None
    assert called["n"] == 0


def test_row_loss_above_threshold_proceeds_on_yes(
    tmp_path,
    monkeypatch,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
):
    orch = DataAnalystOrchestrator(
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "outputs",
        verbose=False,
    )
    out3 = copy.deepcopy(valid_phase3_output)
    out3["validation_suite"]["row_loss_pct"] = 18.0  # above alert, below block

    orch.user_confirm = lambda q: True  # user says yes

    result = _run_phase3_with_outputs(
        orch, valid_phase1_output, valid_phase2_output, out3, monkeypatch
    )
    assert result.blocked_phase is None
    assert 3 in result.phase_outputs


def test_phase6_simpsons_paradox_surfaces_in_warnings(valid_phase6_output):
    from orchestrator.orchestrator import _extract_warnings

    out = copy.deepcopy(valid_phase6_output)
    out["segment_deep_dives"][0]["simpsons_paradox_detected"] = True
    out["segment_deep_dives"][0]["simpsons_paradox_description"] = (
        "Aggregate paid_search > organic, but reverses inside every plan_tier."
    )
    warnings = _extract_warnings(6, out)
    assert any("SIMPSON'S PARADOX" in w for w in warnings), warnings


def test_phase5_mtc_warning_surfaces_dropped_hypotheses(valid_phase5_output):
    from orchestrator.orchestrator import _extract_warnings

    out = copy.deepcopy(valid_phase5_output)
    out["multiple_testing_correction"]["hypotheses_surviving_correction"] = ["H1", "H2"]
    warnings = _extract_warnings(5, out)
    assert any("MTC" in w and "H3" in w and "H4" in w for w in warnings), warnings


def test_phase4_partial_status_advances_but_logs_warning(
    tmp_path,
    monkeypatch,
    valid_phase1_output,
    valid_phase2_output,
    valid_phase3_output,
    valid_phase4_output,
):
    orch = DataAnalystOrchestrator(
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "outputs",
        verbose=False,
    )
    out4 = copy.deepcopy(valid_phase4_output)
    out4["status"] = "PARTIAL"
    out4["phase_5_handoff"]["notes"] = "Did not profile events.platform — missing in extract."

    monkeypatch.setattr(
        "agents.phase1_requirements.run", lambda p: FakeResult(valid_phase1_output)
    )
    monkeypatch.setattr(
        "agents.phase2_extraction.run", lambda p: FakeResult(valid_phase2_output)
    )
    monkeypatch.setattr(
        "agents.phase3_cleaning.run", lambda p: FakeResult(valid_phase3_output)
    )
    monkeypatch.setattr("agents.phase4_eda.run", lambda p: FakeResult(out4))

    result = orch.run(
        objective="x",
        data_source_description="y",
        stakeholder_type="z",
        phases_to_run=[1, 2, 3, 4],
    )

    assert result.blocked_phase is None
    # Phase 4 should have been advanced past despite PARTIAL.
    assert result.phase_outputs[4]["status"] == "PARTIAL"
    p4_entries = [
        p for p in result.pipeline_state_log["pipeline_state"]["phases"]
        if p["phase_number"] == 4
    ]
    assert p4_entries and p4_entries[-1]["status"] == "COMPLETE"
