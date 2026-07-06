"""Phase 8 Agent — Storytelling, Reporting & Stakeholder Handoff.

The final agent in the pipeline. Unlike Phases 1–7 — each of which returns a
single JSON object — Phase 8's deliverable is a **Markdown report** followed by
a machine-readable **JSON summary** block (see PROMPT.md `<output_format>`).

So this agent calls the LLM WITHOUT JSON-output mode, then splits the response
into:
  * `final_report`   — the Markdown report (the actual stakeholder deliverable)
  * `phase_8_summary` — the parsed JSON summary the Orchestrator's quality gate
                        and PIPELINE STATE LOG consume.

The returned `output` dict is shaped so `core.quality_gates.gate_phase_8` and
the orchestrator's transition-card helpers can read it directly.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from core.llm_client import call_llm
from core.prompts import load_prompt

PHASE_NUMBER = 8
PHASE_NAME = "Storytelling, Reporting & Handoff"

# Phase 8 reports run long — a full multi-section Markdown report plus the JSON
# summary easily exceeds the 8192-token default the JSON phases use. Give the
# model far more output room (overridable via env).
PHASE_8_MAX_TOKENS = int(os.environ.get("PHASE_8_MAX_TOKENS", "32768"))


@dataclass
class PhaseRunResult:
    output: dict[str, Any]
    raw_text: str
    usage: dict | None


def run(context_packet: dict) -> PhaseRunResult:
    """Execute Phase 8 against the given context packet."""
    system_prompt = load_prompt(PHASE_NUMBER)
    user_message = _format_phase8_message(context_packet)

    # json_output=False: Phase 8 returns Markdown + a fenced JSON block, not a
    # bare JSON object, so we must not constrain the response mime type.
    response = call_llm(
        system_prompt,
        user_message,
        json_output=False,
        max_tokens=PHASE_8_MAX_TOKENS,
    )

    try:
        report, summary_obj = _split_report_and_summary(response.text)
    except ValueError as exc:
        # A malformed or truncated response must not crash the pipeline. Return
        # a NEEDS_RETRY output so the orchestrator retries with enriched context
        # (and ultimately surfaces a clean PhaseBlockedError if it can't parse).
        return PhaseRunResult(
            output={
                "phase": PHASE_NUMBER,
                "phase_name": PHASE_NAME,
                "status": "NEEDS_RETRY",
                "final_report": "",
                "phase_8_summary": {},
                "parse_error": str(exc),
            },
            raw_text=response.text,
            usage=response.usage,
        )

    summary = summary_obj.get("phase_8_summary") or summary_obj

    output: dict[str, Any] = {
        "phase": PHASE_NUMBER,
        "phase_name": PHASE_NAME,
        # Surface a top-level status so the orchestrator can route retries.
        "status": summary.get("status") or "COMPLETE",
        "final_report": report,
        "phase_8_summary": summary,
    }
    return PhaseRunResult(output=output, raw_text=response.text, usage=response.usage)


def _format_phase8_message(context_packet: dict) -> str:
    """User-role message for Phase 8.

    Phase 8's contract differs from Phases 1–7: it must emit the Markdown
    report first, then the JSON summary in a single fenced ```json block — so
    we do NOT reuse `core.context_packet.format_user_message` (which demands a
    bare JSON object).
    """
    return (
        "<context_packet>\n"
        f"{json.dumps(context_packet, indent=2, default=str)}\n"
        "</context_packet>\n\n"
        "You are Phase 8 Agent — the final agent. Execute all eight tasks "
        "against the context packet above and run the 11-point self-check "
        "quality gate before finalising.\n\n"
        "Produce your response in exactly two parts, in this order:\n"
        "  1. The complete stakeholder report in Markdown, following the "
        "structure in your system prompt's <output_format> section.\n"
        "  2. Immediately after the report, the machine-readable JSON summary "
        "inside a single ```json fenced code block, with the top-level key "
        "`phase_8_summary`.\n\n"
        "Output nothing after the closing ``` of the JSON block."
    )


# --------------------------------------------------------------------------
# Response parsing
# --------------------------------------------------------------------------

_JSON_FENCE_RE = re.compile(
    r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```", re.DOTALL | re.IGNORECASE
)


def _split_report_and_summary(raw_text: str) -> tuple[str, dict]:
    """Split a Phase 8 response into (markdown_report, summary_json).

    Tolerates: fenced or unfenced JSON, the model stripping the fence, and
    trailing horizontal rules. Raises ValueError if no summary can be found.
    """
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Phase 8 returned an empty response")

    summary_obj: dict | None = None
    report = text

    # Preferred: a fenced ```json block containing phase_8_summary.
    for match in reversed(list(_JSON_FENCE_RE.finditer(text))):
        try:
            candidate = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "phase_8_summary" in candidate:
            summary_obj = candidate
            report = text[: match.start()]
            break

    # Fallback: an unfenced object — brace-match from the last phase_8_summary.
    if summary_obj is None:
        key_idx = text.rfind('"phase_8_summary"')
        if key_idx != -1:
            start = text.rfind("{", 0, key_idx)
            if start != -1:
                obj_text = _match_braces(text, start)
                if obj_text is not None:
                    try:
                        summary_obj = json.loads(obj_text)
                        report = text[:start]
                    except json.JSONDecodeError:
                        summary_obj = None

    if summary_obj is None:
        raise ValueError(
            "Phase 8 response did not contain a parseable phase_8_summary "
            f"JSON block. Response preview: {text[:300]!r}"
        )

    report = _tidy_report(report)
    return report, summary_obj


def _match_braces(text: str, start: int) -> str | None:
    """Return the substring of `text` for the brace-balanced object at `start`.

    Respects string literals and escape sequences so braces inside strings
    don't throw off the depth count.
    """
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _tidy_report(report: str) -> str:
    """Strip dangling fences / horizontal rules left after splitting off JSON."""
    report = report.rstrip()
    # Drop a trailing ```json (or ```) fence opener with nothing after it.
    report = re.sub(r"```(?:json)?\s*$", "", report).rstrip()
    # Drop a trailing markdown horizontal rule that preceded the JSON block.
    report = re.sub(r"(?:\n|^)-{3,}\s*$", "", report).rstrip()
    return report
