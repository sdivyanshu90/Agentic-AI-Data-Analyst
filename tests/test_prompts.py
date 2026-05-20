"""Prompt loader extracts complete <system>...</system> blocks from PROMPT.md."""
from __future__ import annotations

import pytest

from core.prompts import load_prompt


@pytest.mark.parametrize("phase", [1, 2, 3, 4, 5, 6, 7, 8])
def test_phase_prompts_extract_complete_system_block(phase):
    prompt = load_prompt(phase)
    assert prompt.startswith("<system>")
    assert prompt.rstrip().endswith("</system>")
    assert "<output_format>" in prompt, f"Phase {phase} prompt is truncated before <output_format>"


def test_phase_1_prompt_contains_task_list():
    prompt = load_prompt(1)
    for task in ("STAKEHOLDER DECODING", "SUB-QUESTION DECOMPOSITION", "SUCCESS DEFINITION"):
        assert task in prompt, f"Phase 1 prompt missing TASK: {task}"


def test_orchestrator_prompt_contains_quality_gates():
    prompt = load_prompt("orchestrator")
    assert prompt.startswith("<system>")
    assert "<quality_gates>" in prompt


def test_unknown_section_raises():
    with pytest.raises(KeyError):
        load_prompt(99)
