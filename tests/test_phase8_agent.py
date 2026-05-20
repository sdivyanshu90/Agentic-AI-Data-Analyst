"""Unit tests for the Phase 8 agent's response-parsing logic.

These exercise `_split_report_and_summary` directly — no API calls — because
splitting a mixed Markdown + JSON response is the riskiest part of Phase 8.
"""
from __future__ import annotations

import json

import pytest

from agents.phase8_reporting import _split_report_and_summary

_SUMMARY = {
    "phase_8_summary": {
        "status": "COMPLETE",
        "sub_questions_answered": ["SQ1"],
        "quality_gate_checks_passed": 9,
        "quality_gate_checks_failed": 0,
    }
}


def test_split_handles_fenced_json_block():
    report_md = "# Report\n\n## Executive Summary\nChurn rose 8 points."
    raw = f"{report_md}\n\n---\n\n```json\n{json.dumps(_SUMMARY, indent=2)}\n```"
    report, summary = _split_report_and_summary(raw)
    assert "Executive Summary" in report
    assert "```" not in report
    assert not report.rstrip().endswith("-")
    assert summary["phase_8_summary"]["status"] == "COMPLETE"


def test_split_handles_unfenced_json_fallback():
    report_md = "# Report\n\nBody text."
    raw = f"{report_md}\n\n{json.dumps(_SUMMARY)}"
    report, summary = _split_report_and_summary(raw)
    assert report.strip() == report_md
    assert summary["phase_8_summary"]["sub_questions_answered"] == ["SQ1"]


def test_split_picks_last_json_block_when_multiple():
    # A ```json example inside the report body must not be mistaken for the
    # real summary block at the end.
    decoy = '```json\n{"example": true}\n```'
    raw = f"# Report\n\n{decoy}\n\n```json\n{json.dumps(_SUMMARY)}\n```"
    report, summary = _split_report_and_summary(raw)
    assert "phase_8_summary" in summary
    assert summary["phase_8_summary"]["quality_gate_checks_failed"] == 0


def test_split_raises_on_empty_response():
    with pytest.raises(ValueError):
        _split_report_and_summary("")


def test_split_raises_when_no_summary_present():
    with pytest.raises(ValueError):
        _split_report_and_summary("# Report\n\nJust prose, no JSON summary.")
