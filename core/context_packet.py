"""Context packet construction.

Per CLAUDE.md invariant #1: NEVER truncate prior phase outputs when
passing context forward. This module builds the packet and wraps it
in the standard `<context_packet>` envelope every agent expects.
"""
from __future__ import annotations

import json
from typing import Any


def build_context_packet(
    mission_brief: dict,
    prior_outputs: dict,
    pipeline_state: dict,
    *,
    retry_context: dict | None = None,
    user_clarifications: list | None = None,
    knowledge_base: list | None = None,
) -> dict:
    """Assemble the packet passed to every phase agent.

    `prior_outputs` maps phase number (int or "phase_N" string) to that
    phase's full JSON output. Pass it forward verbatim — no truncation.

    `knowledge_base` carries entries persisted by Phase 9 in previous runs —
    institutional memory recalled for every agent (Phase 0 uses it for
    triage; later phases for known gotchas on related questions).
    """
    packet: dict[str, Any] = {
        "mission_brief": mission_brief,
        "prior_outputs": prior_outputs,
        "pipeline_state": pipeline_state,
    }
    if knowledge_base:
        packet["knowledge_base_recall"] = knowledge_base
    if user_clarifications:
        packet["user_clarifications"] = user_clarifications
    if retry_context is not None:
        packet["retry_context"] = retry_context
    return packet


def format_user_message(
    context_packet: dict,
    phase_number: int,
    *,
    dataset_path: str | None = None,
) -> str:
    """The user-role message wrapping the context packet for a phase agent.

    When `dataset_path` is given, a `<code_execution>` block instructs the
    agent to use its `run_python` tool to compute real figures from the actual
    file rather than estimating them from the prose data description.
    """
    code_block = ""
    if dataset_path:
        code_block = (
            "<code_execution>\n"
            "You have a `run_python` tool. The REAL dataset is the file at:\n"
            f"  {dataset_path}\n"
            "Inside `run_python` it is already loaded as a pandas DataFrame "
            "named `df` (pandas as `pd`, numpy as `np`, scipy.stats as `stats` "
            "in scope).\n\n"
            "RULES — these OVERRIDE any wording in your system prompt:\n"
            "1. You MUST call `run_python` at least once before answering. "
            "Wherever your system prompt says you may 'estimate', 'describe' "
            "or 'compute' a figure, you must COMPUTE it by running code. An "
            "answer containing any un-computed number is invalid.\n"
            "2. Every number in your JSON — null counts, dtypes, "
            "distributions, group rates, correlations, test statistics, "
            "p-values, effect sizes — must come from real executed output, "
            "never from estimation or prior knowledge. `print()` results so "
            "you can read them.\n"
            "3. `run_python` is STATELESS: each call runs in a fresh process, "
            "`df` is reloaded from the raw file every time, and variables do "
            "NOT persist between calls. Make every code block self-contained. "
            "To validate transformed/cleaned data, apply the transformations "
            "AND validate them inside the SAME code block — e.g. for a "
            "post-cleaning null check, build the cleaned frame and assert its "
            "null count in one block.\n"
            "4. Batch related computations to keep the number of calls low.\n"
            "Only once every figure is computed, produce your final JSON.\n"
            "</code_execution>\n\n"
        )
    return (
        "<context_packet>\n"
        f"{json.dumps(context_packet, indent=2, default=str)}\n"
        "</context_packet>\n\n"
        f"{code_block}"
        f"You are Phase {phase_number} Agent. Execute your tasks against the "
        "context packet above. Produce your structured JSON output exactly as "
        "specified in your system prompt's <output_format> section. Return ONLY "
        "the JSON object — no prose, no markdown fences."
    )
