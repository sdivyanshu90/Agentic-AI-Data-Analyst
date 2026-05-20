"""Tests for core.llm_client — transient-retry, usage parsing, and the
code-execution call path. The Gemini client is mocked; no network calls."""
from __future__ import annotations

import pytest
from google.genai import errors as genai_errors

import core.llm_client as llm


class _Usage:
    prompt_token_count = 100
    candidates_token_count = 50
    thoughts_token_count = 25
    total_token_count = 175


class _Resp:
    def __init__(self, text="{\"ok\": true}", usage=True):
        self.text = text
        self.usage_metadata = _Usage() if usage else None


class _Models:
    """Fake `client.models` whose generate_content follows a scripted plan."""

    def __init__(self, plan):
        self._plan = list(plan)
        self.calls = 0

    def generate_content(self, *, model, contents, config):
        self.calls += 1
        item = self._plan.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _Client:
    def __init__(self, plan):
        self.models = _Models(plan)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda *_: None)


@pytest.fixture
def csv(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("a,b\n1,2\n3,4\n")
    return p


def _install(monkeypatch, plan):
    client = _Client(plan)
    monkeypatch.setattr(llm, "_client", client)
    return client


# --- _extract_usage -------------------------------------------------------

def test_extract_usage_returns_dict():
    u = llm._extract_usage(_Resp())
    assert u["total_token_count"] == 175 and u["thoughts_token_count"] == 25


def test_extract_usage_none_when_absent():
    assert llm._extract_usage(_Resp(usage=False)) is None


# --- call_llm -------------------------------------------------------------

def test_call_llm_happy_path(monkeypatch):
    _install(monkeypatch, [_Resp(text="hello")])
    resp = llm.call_llm("sys", "user")
    assert isinstance(resp, llm.LLMResponse)
    assert resp.text == "hello"
    assert resp.usage["total_token_count"] == 175


def test_call_llm_retries_transient_then_succeeds(monkeypatch):
    err = genai_errors.ServerError(503, {"error": {"message": "busy"}})
    client = _install(monkeypatch, [err, err, _Resp(text="recovered")])
    resp = llm.call_llm("sys", "user", max_attempts=5)
    assert resp.text == "recovered"
    assert client.models.calls == 3


def test_call_llm_reraises_non_transient(monkeypatch):
    err = genai_errors.ClientError(400, {"error": {"message": "bad request"}})
    _install(monkeypatch, [err])
    with pytest.raises(genai_errors.ClientError):
        llm.call_llm("sys", "user")


def test_call_llm_gives_up_after_max_attempts(monkeypatch):
    err = genai_errors.ServerError(503, {"error": {"message": "busy"}})
    _install(monkeypatch, [err, err])
    with pytest.raises(genai_errors.ServerError):
        llm.call_llm("sys", "user", max_attempts=2)


# --- call_llm_with_code ---------------------------------------------------

def test_call_llm_with_code_returns_code_response(monkeypatch, csv):
    _install(monkeypatch, [_Resp(text="{\"phase\": 4}")])
    resp = llm.call_llm_with_code("sys", "user", str(csv))
    assert isinstance(resp, llm.CodeLLMResponse)
    assert resp.text == "{\"phase\": 4}"
    assert resp.transcript == [] and resp.code_calls == 0
    assert resp.usage["total_token_count"] == 175


def test_call_llm_with_code_retries_transient(monkeypatch, csv):
    err = genai_errors.ServerError(503, {"error": {"message": "busy"}})
    client = _install(monkeypatch, [err, _Resp(text="ok")])
    resp = llm.call_llm_with_code("sys", "user", str(csv), max_attempts=4)
    assert resp.text == "ok"
    assert client.models.calls == 2


def test_call_llm_with_code_missing_dataset_raises(monkeypatch, tmp_path):
    _install(monkeypatch, [_Resp()])
    with pytest.raises(FileNotFoundError):
        llm.call_llm_with_code("sys", "user", str(tmp_path / "nope.csv"))
