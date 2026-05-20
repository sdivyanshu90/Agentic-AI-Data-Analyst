"""Tests for core.code_executor — the sandboxed dataset executor."""
from __future__ import annotations

import textwrap

import pytest

from core.code_executor import DatasetCodeExecutor, _safety_check


@pytest.fixture
def csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("a,b,group\n1,10,x\n2,20,y\n3,30,x\n4,40,y\n")
    return p


@pytest.fixture
def ex(csv):
    return DatasetCodeExecutor(csv, timeout=15)


# --- happy path -----------------------------------------------------------

def test_runs_code_and_captures_stdout(ex):
    r = ex.run("print(df.shape)")
    assert r.ok
    assert "(4, 3)" in r.output
    assert r.error == ""


def test_dataframe_is_preloaded_as_df(ex):
    r = ex.run("print(df['a'].sum())")
    assert r.ok and r.output.strip() == "10"


def test_pandas_numpy_scipy_in_scope(ex):
    r = ex.run("print(type(pd).__name__, type(np).__name__, stats is not None)")
    assert r.ok
    assert "module module True" in r.output


def test_groupby_real_computation(ex):
    r = ex.run("print(df.groupby('group')['b'].mean().to_dict())")
    assert r.ok
    assert "'x': 20.0" in r.output and "'y': 30.0" in r.output


def test_run_count_increments(ex):
    assert ex.run_count == 0
    ex.run("print(1)")
    ex.run("print(2)")
    assert ex.run_count == 2


# --- error handling -------------------------------------------------------

def test_runtime_error_is_captured_not_raised(ex):
    r = ex.run("print(df['missing_column'])")
    assert not r.ok
    assert "KeyError" in r.error


def test_syntax_error_is_rejected(ex):
    r = ex.run("print(")
    assert not r.ok
    assert "SyntaxError" in r.error


def test_empty_code_is_rejected(ex):
    r = ex.run("   ")
    assert not r.ok and "Empty" in r.error


def test_code_with_no_output_warns(ex):
    r = ex.run("x = 1 + 1")
    assert r.ok
    assert "print()" in r.error


def test_timeout_is_enforced(csv):
    ex = DatasetCodeExecutor(csv, timeout=2)
    r = ex.run("while True:\n    pass")
    assert not r.ok
    assert "timed out" in r.error.lower()


# --- sandbox safety -------------------------------------------------------

@pytest.mark.parametrize("bad", [
    "import os",
    "import subprocess",
    "from socket import socket",
    "import shutil",
    "import requests",
])
def test_banned_imports_rejected(ex, bad):
    r = ex.run(bad + "\nprint(1)")
    assert not r.ok
    assert "Disallowed import" in r.error


@pytest.mark.parametrize("bad", [
    "eval('1+1')",
    "exec('x=1')",
    "open('/tmp/x', 'w')",
    "__import__('os')",
])
def test_banned_calls_rejected(ex, bad):
    r = ex.run(bad)
    assert not r.ok
    assert "Disallowed call" in r.error


def test_attribute_escape_rejected(ex):
    # even if `os` were smuggled in, .system() is blocked
    r = ex.run("df.system('ls')")
    assert not r.ok
    assert "Disallowed call" in r.error


def test_safe_pandas_eval_not_blocked(ex):
    # df.eval / df.query are method calls, not the eval builtin — allowed
    assert _safety_check("print(df.eval('a + b'))") is None
    r = ex.run("print(df.eval('a + b').tolist())")
    assert r.ok
    assert "[11, 22, 33, 44]" in r.output


# --- construction ---------------------------------------------------------

def test_missing_dataset_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        DatasetCodeExecutor(tmp_path / "nope.csv")


def test_output_is_truncated(csv):
    ex = DatasetCodeExecutor(csv, max_output=100)
    r = ex.run("print('z' * 5000)")
    assert r.ok
    assert len(r.output) < 300
    assert "truncated" in r.output
