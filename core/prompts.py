"""Load agent system prompts from PROMPT.md (the source of truth).

PROMPT.md sections follow the pattern `# PHASE N AGENT PROMPT` and
`# MASTER ORCHESTRATOR PROMPT`, with the actual system block fenced as
```xml ... ```. We extract the fenced block when present, else the
section body, and cache the result.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Union

PROMPT_FILE = Path(__file__).resolve().parents[1] / "PROMPT.md"

_SECTION_HEADERS: dict[Union[int, float, str], str] = {
    "orchestrator": "MASTER ORCHESTRATOR PROMPT",
    0: "PHASE 0 AGENT PROMPT",
    1: "PHASE 1 AGENT PROMPT",
    2: "PHASE 2 AGENT PROMPT",
    3: "PHASE 3 AGENT PROMPT",
    4: "PHASE 4 AGENT PROMPT",
    5: "PHASE 5 AGENT PROMPT",
    6: "PHASE 6 AGENT PROMPT",
    6.5: "PHASE 6.5 AGENT PROMPT",
    7: "PHASE 7 AGENT PROMPT",
    8: "PHASE 8 AGENT PROMPT",
    9: "PHASE 9 AGENT PROMPT",
}


def _read_prompt_file() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


@lru_cache(maxsize=16)
def load_prompt(phase: Union[int, float, str]) -> str:
    if phase not in _SECTION_HEADERS:
        raise KeyError(f"Unknown prompt section: {phase!r}")

    header = _SECTION_HEADERS[phase]
    text = _read_prompt_file()

    header_re = re.compile(rf"^# {re.escape(header)}\s*$", re.MULTILINE)
    match = header_re.search(text)
    if not match:
        raise ValueError(f"Header `# {header}` not found in PROMPT.md")

    start = match.end()
    next_header_re = re.compile(
        r"^# (?:PHASE \d+(?:\.\d+)? AGENT PROMPT|MASTER ORCHESTRATOR PROMPT)\s*$",
        re.MULTILINE,
    )
    next_match = next_header_re.search(text, pos=start)
    end = next_match.start() if next_match else len(text)

    section = text[start:end]

    # The system prompt itself is wrapped in <system>...</system>. That gives
    # us the cleanest extraction, since the surrounding markdown fences vary
    # (3 vs 4 backticks) and contain inner ```json output_format blocks.
    sys_match = re.search(r"<system>\s*\n?(.*?)</system>", section, re.DOTALL)
    if sys_match:
        return f"<system>\n{sys_match.group(1).rstrip()}\n</system>"

    # Fallback: pull the largest ```xml ... ``` block (handles 4-backtick fence too).
    fenced = re.search(r"````?xml\s*\n(.*?)\n````?\s*$", section, re.DOTALL | re.MULTILINE)
    if fenced:
        return fenced.group(1).strip()

    return section.strip()
