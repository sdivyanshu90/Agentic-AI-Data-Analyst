"""Shared phase-agent runner.

Every phase agent does the same thing: load its system prompt from PROMPT.md,
wrap the context packet, call the model, parse the JSON.

The analytical phases (3-6) are **code-capable**. When the mission brief
carries a real `dataset_path` they run as TWO calls instead of one:

  1. COMPUTE  — a call whose only job is to execute pandas/scipy against the
                real file via the `run_python` tool and print real figures.
  2. SYNTHESISE — the normal phase call, but with those computed figures
                injected into the context packet as `computed_evidence`, so
                the structured JSON is grounded in executed numbers.

Splitting the two is what makes it reliable: a single call that must *both*
drive a tool loop *and* emit a large structured JSON tends to skip the tool
under the weight of an elaborate phase prompt. Each call here has one job.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from core.context_packet import format_user_message
from core.llm_client import call_llm, call_llm_with_code, extract_json_output
from core.prompts import load_prompt

# Synthesis (step 2) for analytical phases carries a large JSON output plus the
# injected evidence — give it more room than the 8192 reasoning default.
_SYNTHESIS_MAX_TOKENS = 16384

# Forced computations in the COMPUTE step. Each run_python call can be a long
# multi-result script, so a handful is plenty for a thorough analytical phase.
_COMPUTE_CODE_CALLS = 6

# Mode AUTO occasionally lets the model answer without running code at all.
# When that happens the COMPUTE step is re-issued with a hardened prompt,
# up to this many total attempts, before the phase proceeds regardless.
_COMPUTE_MAX_ATTEMPTS = 4

_COMPUTE_SYSTEM = (
    "You are a meticulous data analyst with a Python code-execution tool "
    "(`run_python`). Your ONLY job in this turn is to COMPUTE. Use `run_python` "
    "to calculate — against the REAL dataset — every figure the phase "
    "specification below will need: column profiles, null counts and dtypes, "
    "group/segment rates, distributions, correlations, statistical tests, "
    "p-values, effect sizes, segment sizes, whatever is relevant. `print()` "
    "every result clearly and labelled. Be thorough and accurate; another "
    "analyst will write the structured report from the numbers you compute. "
    "Do NOT write JSON or prose conclusions now — just compute and print. "
    "You MUST call `run_python`: a reply containing no code execution is a "
    "failure. Never substitute the prose data description or prior knowledge "
    "for actually running pandas against the file — your first action must be "
    "a `run_python` call."
)

# Prepended to the COMPUTE message on a retry when the model answered in text
# without ever executing code — mode AUTO permits that, and a phase grounded
# in zero executed code is exactly the failure v2 exists to eliminate.
_RECOMPUTE_PREFIX = (
    "⚠️ CORRECTION: your previous attempt produced a text answer WITHOUT "
    "executing any code. That is rejected. You MUST call the `run_python` "
    "tool to compute figures from the real dataset — your very first action "
    "now must be a `run_python` call, not prose.\n\n"
)


@dataclass
class PhaseRunResult:
    output: dict[str, Any]
    raw_text: str
    usage: dict | None = None
    # Executed-code audit trail — populated for code-capable phases that ran
    # against a real dataset. Each entry: {code, output, error, ok}.
    transcript: list | None = None
    code_calls: int = 0


def _dataset_path(context_packet: dict) -> str | None:
    """Return the real dataset path from the mission brief, if one was set."""
    brief = context_packet.get("mission_brief")
    if isinstance(brief, dict):
        return brief.get("dataset_path") or None
    return None


def _evidence_block(phase_number: int, phase_name: str, transcript: list) -> str:
    """Render the executed-code transcript as a factual-evidence block."""
    parts = [
        f"These figures were COMPUTED by executing Python against the REAL "
        f"dataset to support Phase {phase_number} ({phase_name}). They are the "
        f"authoritative factual basis for your output — every number you "
        f"report must match these computed results; do not estimate or "
        f"override them.",
    ]
    n = 0
    for entry in transcript or []:
        if not entry.get("ok"):
            continue
        n += 1
        parts.append(f"\n--- computation {n} ---")
        parts.append("CODE:\n" + (entry.get("code") or "").strip())
        parts.append("OUTPUT:\n" + (entry.get("output") or "").strip())
    if n == 0:
        parts.append("\n(No successful computations were produced.)")
    return "\n".join(parts)


def _compute_message(context_packet: dict, phase_number: int,
                     phase_spec: str, dataset_path: str) -> str:
    """User message for the COMPUTE step."""
    return (
        "<context_packet>\n"
        f"{json.dumps(context_packet, indent=2, default=str)}\n"
        "</context_packet>\n\n"
        "<phase_specification>\n"
        f"You are computing the figures needed for Phase {phase_number}. The "
        "analyst who will write that phase works to this specification:\n\n"
        f"{phase_spec}\n"
        "</phase_specification>\n\n"
        f"The real dataset is at {dataset_path} (loaded as `df` inside "
        "`run_python`). Use `run_python` now to COMPUTE every figure the Phase "
        f"{phase_number} tasks above require. Print each result clearly "
        "labelled. Do not write the phase JSON — only compute."
    )


def _parse_or_retry(resp, phase_number, phase_name, transcript, code_calls):
    """Parse a phase response into a PhaseRunResult, degrading to NEEDS_RETRY."""
    try:
        output = extract_json_output(resp.text)
        if not isinstance(output, dict):
            raise ValueError(f"non-object JSON: {type(output).__name__}")
    except (ValueError, json.JSONDecodeError) as exc:
        return PhaseRunResult(
            output={
                "phase": phase_number,
                "phase_name": phase_name,
                "status": "NEEDS_RETRY",
                "parse_error": f"Could not parse Phase {phase_number} output: {exc}",
            },
            raw_text=resp.text or "",
            usage=resp.usage,
            transcript=transcript,
            code_calls=code_calls,
        )
    output.setdefault("phase", phase_number)
    output.setdefault("phase_name", phase_name)
    return PhaseRunResult(
        output=output, raw_text=resp.text or "", usage=resp.usage,
        transcript=transcript, code_calls=code_calls,
    )


def run_phase(
    phase_number: int,
    phase_name: str,
    context_packet: dict,
    *,
    code_capable: bool = False,
) -> PhaseRunResult:
    """Run one phase agent against the context packet.

    If `code_capable` and a real `dataset_path` is present, runs the two-step
    compute-then-synthesise flow; otherwise a single reasoning call (the
    original behaviour, fully backward compatible).
    """
    system_prompt = load_prompt(phase_number)
    dataset_path = _dataset_path(context_packet) if code_capable else None

    if not dataset_path:
        user_message = format_user_message(context_packet, phase_number)
        resp = call_llm(system_prompt, user_message, json_output=True)
        return _parse_or_retry(resp, phase_number, phase_name, None, 0)

    # --- Step 1: COMPUTE real figures by executing code -------------------
    # Tool use is mode AUTO: the dedicated compute-only system prompt below
    # already mandates `run_python`, and the model iterates as much as it
    # needs then stops. (Forcing mode ANY was tried and rejected — it pads
    # the transcript with no-op placeholder calls once computation is done.)
    compute_user = _compute_message(
        context_packet, phase_number, system_prompt, dataset_path
    )
    # Mode AUTO lets the model answer in text without ever calling the tool.
    # If it skips computation, re-issue with a hardened instruction — up to
    # _COMPUTE_MAX_ATTEMPTS times — so the phase is grounded in executed
    # code, not estimation. (Pure AUTO: no forced tool use, no padding.)
    code_resp = call_llm_with_code(
        _COMPUTE_SYSTEM, compute_user, dataset_path,
        max_code_calls=_COMPUTE_CODE_CALLS,
    )
    for attempt in range(2, _COMPUTE_MAX_ATTEMPTS + 1):
        if code_resp.code_calls > 0:
            break
        print(
            f"  [phase {phase_number}] COMPUTE step ran no code — retrying "
            f"with hardened prompt ({attempt}/{_COMPUTE_MAX_ATTEMPTS})",
            flush=True,
        )
        code_resp = call_llm_with_code(
            _COMPUTE_SYSTEM, _RECOMPUTE_PREFIX + compute_user, dataset_path,
            max_code_calls=_COMPUTE_CODE_CALLS,
        )
    transcript = code_resp.transcript
    code_calls = code_resp.code_calls

    # --- Step 2: SYNTHESISE the phase JSON grounded in the evidence -------
    enriched = dict(context_packet)
    enriched["computed_evidence"] = _evidence_block(
        phase_number, phase_name, transcript
    )
    user_message = format_user_message(enriched, phase_number)
    resp = call_llm(
        system_prompt, user_message, json_output=True,
        max_tokens=_SYNTHESIS_MAX_TOKENS,
    )
    return _parse_or_retry(resp, phase_number, phase_name, transcript, code_calls)
