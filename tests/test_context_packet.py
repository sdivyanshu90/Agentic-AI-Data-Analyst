"""Context packet construction and JSON-extraction tests."""
from __future__ import annotations

import json

import pytest

from core.context_packet import build_context_packet, format_user_message
from core.llm_client import extract_json_output


def test_build_context_packet_contains_required_keys(sample_mission_brief):
    packet = build_context_packet(
        mission_brief=sample_mission_brief,
        prior_outputs={1: {"phase": 1, "sub_questions": []}},
        pipeline_state={"current_phase": 1, "phases": []},
    )
    assert packet["mission_brief"] is sample_mission_brief
    assert packet["prior_outputs"][1]["phase"] == 1
    assert "pipeline_state" in packet


def test_build_context_packet_includes_retry_context(sample_mission_brief):
    packet = build_context_packet(
        mission_brief=sample_mission_brief,
        prior_outputs={},
        pipeline_state={},
        retry_context={"attempt": 2, "specific_instruction": "fix X"},
    )
    assert packet["retry_context"]["attempt"] == 2


def test_format_user_message_wraps_in_context_packet(sample_mission_brief):
    packet = build_context_packet(
        mission_brief=sample_mission_brief,
        prior_outputs={},
        pipeline_state={},
    )
    msg = format_user_message(packet, phase_number=1)
    assert "<context_packet>" in msg
    assert "</context_packet>" in msg
    assert "Phase 1 Agent" in msg


# ---------- extract_json_output ----------


def test_extract_json_strips_markdown_fences():
    raw = "```json\n{\"a\": 1, \"b\": 2}\n```"
    assert extract_json_output(raw) == {"a": 1, "b": 2}


def test_extract_json_handles_thinking_block():
    raw = "<thinking>some plan</thinking>\n{\"x\": true}"
    assert extract_json_output(raw) == {"x": True}


def test_extract_json_finds_object_after_prose():
    raw = "Here is the answer:\n{\"phase\": 1}"
    assert extract_json_output(raw) == {"phase": 1}


def test_extract_json_raises_on_empty():
    with pytest.raises(ValueError):
        extract_json_output("")


def test_extract_json_roundtrips_complex_object(valid_phase1_output):
    raw = "```json\n" + json.dumps(valid_phase1_output) + "\n```"
    parsed = extract_json_output(raw)
    assert parsed["phase"] == 1
    assert len(parsed["sub_questions"]) == len(valid_phase1_output["sub_questions"])
