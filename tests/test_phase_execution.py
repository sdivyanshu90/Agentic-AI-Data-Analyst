"""Tests for the code-execution wiring: format_user_message, run_phase,
and dataset_path threading through the orchestrator's mission brief."""
from __future__ import annotations

import pytest

import core.phase_execution as pe
from core.context_packet import format_user_message
from core.llm_client import CodeLLMResponse, LLMResponse
from orchestrator.orchestrator import DataAnalystOrchestrator


# --- format_user_message --------------------------------------------------

def test_format_user_message_no_code_block_by_default():
    msg = format_user_message({"mission_brief": {}}, 4)
    assert "<code_execution>" not in msg
    assert "<context_packet>" in msg


def test_format_user_message_includes_code_block_when_dataset_given():
    msg = format_user_message({"mission_brief": {}}, 4, dataset_path="/data/x.csv")
    assert "<code_execution>" in msg
    assert "/data/x.csv" in msg
    assert "run_python" in msg


# --- run_phase: reasoning vs code paths -----------------------------------

@pytest.fixture
def patched(monkeypatch):
    """Stub load_prompt + both LLM entry points; record which was used."""
    calls = {"plain": 0, "code": 0}
    monkeypatch.setattr(pe, "load_prompt", lambda phase: f"<system>P{phase}</system>")

    def fake_call_llm(system, user, **kw):
        calls["plain"] += 1
        calls["last_plain_user"] = user
        return LLMResponse(text='{"status": "COMPLETE"}', model="m", usage={"t": 1})

    def fake_call_llm_with_code(system, user, dataset_path, **kw):
        calls["code"] += 1
        return CodeLLMResponse(
            text='{"status": "COMPLETE"}', model="m", usage={"t": 2},
            transcript=[{"code": "print(df.shape)", "output": "(7043, 21)",
                         "error": "", "ok": True}],
        )

    monkeypatch.setattr(pe, "call_llm", fake_call_llm)
    monkeypatch.setattr(pe, "call_llm_with_code", fake_call_llm_with_code)
    return calls


def test_run_phase_uses_plain_call_when_no_dataset(patched):
    packet = {"mission_brief": {"objective": "x"}}
    result = pe.run_phase(4, "EDA", packet, code_capable=True)
    assert patched["plain"] == 1 and patched["code"] == 0
    assert result.transcript is None and result.code_calls == 0
    assert result.output["phase"] == 4 and result.output["phase_name"] == "EDA"


def test_run_phase_uses_code_call_when_dataset_present(patched):
    """Code path is two-step: a compute call (code) then a synthesis call (plain)."""
    packet = {"mission_brief": {"objective": "x", "dataset_path": "/d.csv"}}
    result = pe.run_phase(5, "Hypothesis", packet, code_capable=True)
    assert patched["plain"] == 1 and patched["code"] == 1
    assert result.code_calls == 1
    assert result.transcript[0]["output"] == "(7043, 21)"
    assert result.output["phase"] == 5


def test_run_phase_not_code_capable_ignores_dataset(patched):
    packet = {"mission_brief": {"dataset_path": "/d.csv"}}
    pe.run_phase(1, "Requirements", packet, code_capable=False)
    assert patched["plain"] == 1 and patched["code"] == 0


def test_synthesis_call_receives_computed_evidence(patched):
    """The step-2 synthesis call must see the executed-code output."""
    packet = {"mission_brief": {"objective": "x", "dataset_path": "/d.csv"}}
    pe.run_phase(4, "EDA", packet, code_capable=True)
    synth_user = patched["last_plain_user"]
    assert "computed_evidence" in synth_user
    assert "(7043, 21)" in synth_user  # the executed-code output is carried in


def test_compute_step_no_retry_when_code_executed(patched):
    """If the model runs code on the first compute call, no retry is issued."""
    packet = {"mission_brief": {"objective": "x", "dataset_path": "/d.csv"}}
    pe.run_phase(3, "Cleaning", packet, code_capable=True)
    assert patched["code"] == 1  # single compute call


def test_compute_step_retries_when_model_skips_the_tool(monkeypatch):
    """Mode AUTO lets the model answer without code; run_phase retries once."""
    monkeypatch.setattr(pe, "load_prompt", lambda phase: f"<system>P{phase}</system>")
    monkeypatch.setattr(
        pe, "call_llm",
        lambda s, u, **kw: LLMResponse(text='{"status": "COMPLETE"}',
                                       model="m", usage=None),
    )
    compute_users: list[str] = []

    def fake_code(system, user, dataset_path, **kw):
        compute_users.append(user)
        if len(compute_users) == 1:  # first attempt: model produced no code
            return CodeLLMResponse(text="my answer", model="m", usage=None,
                                   transcript=[])
        return CodeLLMResponse(  # retry: model actually executes code
            text="", model="m", usage=None,
            transcript=[{"code": "print(df.shape)", "output": "(7043, 21)",
                         "error": "", "ok": True}],
        )

    monkeypatch.setattr(pe, "call_llm_with_code", fake_code)
    packet = {"mission_brief": {"objective": "x", "dataset_path": "/d.csv"}}
    result = pe.run_phase(3, "Cleaning", packet, code_capable=True)

    assert len(compute_users) == 2  # retried exactly once
    assert pe._RECOMPUTE_PREFIX not in compute_users[0]
    assert pe._RECOMPUTE_PREFIX in compute_users[1]  # retry hardened the message
    assert result.code_calls == 1  # the retry's transcript is the one kept


def test_compute_step_gives_up_after_max_attempts(monkeypatch):
    """If the model never runs code, COMPUTE retries up to the cap then proceeds."""
    monkeypatch.setattr(pe, "load_prompt", lambda phase: f"<system>P{phase}</system>")
    monkeypatch.setattr(
        pe, "call_llm",
        lambda s, u, **kw: LLMResponse(text='{"status": "COMPLETE"}',
                                       model="m", usage=None),
    )
    attempts: list[str] = []

    def fake_code(system, user, dataset_path, **kw):  # never runs code
        attempts.append(user)
        return CodeLLMResponse(text="my answer", model="m", usage=None,
                               transcript=[])

    monkeypatch.setattr(pe, "call_llm_with_code", fake_code)
    packet = {"mission_brief": {"objective": "x", "dataset_path": "/d.csv"}}
    result = pe.run_phase(3, "Cleaning", packet, code_capable=True)

    assert len(attempts) == pe._COMPUTE_MAX_ATTEMPTS  # tried the full cap
    assert result.code_calls == 0  # proceeds anyway; evidence block stays empty
    assert result.output["status"] == "COMPLETE"  # synthesis still runs


def test_evidence_block_includes_code_and_output():
    transcript = [{"code": "print(df.shape)", "output": "(7043, 21)",
                   "error": "", "ok": True}]
    block = pe._evidence_block(4, "EDA", transcript)
    assert "print(df.shape)" in block and "(7043, 21)" in block
    assert "COMPUTED" in block


def test_evidence_block_handles_no_successful_runs():
    block = pe._evidence_block(4, "EDA", [{"code": "x", "output": "",
                                           "error": "boom", "ok": False}])
    assert "No successful computations" in block


def test_run_phase_injects_phase_identity(patched):
    packet = {"mission_brief": {}}
    out = pe.run_phase(3, "Cleaning", packet, code_capable=True).output
    assert out["phase"] == 3 and out["phase_name"] == "Cleaning"


def test_run_phase_empty_response_yields_needs_retry(monkeypatch):
    """A truncated/empty model response must not crash — it becomes NEEDS_RETRY."""
    monkeypatch.setattr(pe, "load_prompt", lambda phase: "<system>x</system>")
    monkeypatch.setattr(
        pe, "call_llm",
        lambda s, u, **kw: LLMResponse(text="", model="m", usage=None),
    )
    result = pe.run_phase(4, "EDA", {"mission_brief": {}}, code_capable=True)
    assert result.output["status"] == "NEEDS_RETRY"
    assert "parse_error" in result.output
    assert result.output["phase"] == 4


# --- orchestrator threads dataset_path ------------------------------------

def test_build_mission_brief_omits_dataset_path_by_default():
    orch = DataAnalystOrchestrator(verbose=False)
    brief = orch.build_mission_brief(
        objective="o", data_source_description="d", stakeholder_type="s",
    )
    assert "dataset_path" not in brief["mission_brief"]


def test_build_mission_brief_includes_dataset_path_when_set():
    orch = DataAnalystOrchestrator(verbose=False)
    brief = orch.build_mission_brief(
        objective="o", data_source_description="d", stakeholder_type="s",
        dataset_path="/data/telco.csv",
    )
    assert brief["mission_brief"]["dataset_path"] == "/data/telco.csv"


def test_orchestrator_starts_with_empty_transcripts():
    orch = DataAnalystOrchestrator(verbose=False)
    assert orch.execution_transcripts == {}
