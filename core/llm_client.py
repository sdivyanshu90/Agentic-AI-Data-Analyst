"""Gemini client wrapper.

CLAUDE.md mandates extended thinking on every call. Gemini 2.5 Pro has
a `thinking_config` analogue. We expose a single `call_llm()` entry point
plus `extract_json_output()` for defensive parsing of model responses.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-pro")
DEFAULT_THINKING_BUDGET = int(os.environ.get("THINKING_BUDGET_TOKENS", "4096"))
DEFAULT_MAX_TOKENS = int(os.environ.get("MAX_TOKENS_PER_CALL", "8192"))
# Code-execution phases need far more output room: the final turn carries a
# large analytical JSON *plus* the extended-thinking budget, after several
# tool round-trips. 8192 truncates it to an empty response.
DEFAULT_CODE_MAX_TOKENS = int(os.environ.get("CODE_MAX_TOKENS_PER_CALL", "24576"))


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: dict | None = None


@dataclass
class CodeLLMResponse:
    """Result of a code-execution-enabled call.

    `transcript` records every Python snippet the model ran and what it
    produced — the audit trail proving the figures were computed, not guessed.
    """
    text: str
    model: str
    usage: dict | None
    transcript: list  # list of {code, output, error, ok}

    @property
    def code_calls(self) -> int:
        return len(self.transcript)


_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to .env or export it before running."
        )
    from google import genai

    _client = genai.Client(api_key=api_key)
    return _client


_TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


def _is_transient(exc: Exception) -> bool:
    """True for failures worth retrying: 429/5xx API errors and transport-level
    drops (server disconnected, reset connections) that surface from httpx
    beneath the google-genai SDK rather than as genai error types."""
    from google.genai import errors as genai_errors

    if isinstance(exc, (genai_errors.ServerError, genai_errors.ClientError)):
        status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        return status in _TRANSIENT_STATUSES
    try:
        import httpx

        if isinstance(exc, httpx.HTTPError):
            return True
    except ImportError:  # pragma: no cover
        pass
    return isinstance(exc, (ConnectionError, TimeoutError))


def call_llm(
    system_prompt: str,
    user_message: str,
    *,
    model: str = DEFAULT_MODEL,
    thinking_budget: int = DEFAULT_THINKING_BUDGET,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    json_output: bool = True,
    max_attempts: int = 14,
) -> LLMResponse:
    """Call the LLM with extended thinking enabled.

    Returns the raw text body. For JSON-producing phases (1–7) we set
    `response_mime_type='application/json'` so the model is constrained.

    Transient API failures (429 / 5xx) are retried up to `max_attempts` times
    with exponential backoff. Gemini occasionally returns 503 UNAVAILABLE
    under high demand; the SDK's built-in retry doesn't always cover that.
    """
    from google.genai import types

    client = _get_client()

    config_kwargs = {
        "system_instruction": system_prompt,
        "max_output_tokens": max_tokens,
        "thinking_config": types.ThinkingConfig(thinking_budget=thinking_budget),
    }
    if json_output:
        config_kwargs["response_mime_type"] = "application/json"
    config = types.GenerateContentConfig(**config_kwargs)

    response = _generate_with_retry(
        client, model, user_message, config, max_attempts, label="call_llm"
    )
    return LLMResponse(
        text=response.text or "", model=model, usage=_extract_usage(response)
    )


def _generate_with_retry(client, model, contents, config, max_attempts, *, label):
    """Run `generate_content`, retrying transient 429/5xx with exponential backoff.

    Gemini occasionally returns 503 UNAVAILABLE under high demand; the SDK's
    built-in retry doesn't always cover that. Shared by `call_llm` and
    `call_llm_with_code`.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as exc:
            last_exc = exc
            if not _is_transient(exc) or attempt >= max_attempts:
                raise
            delay = min(60, 2 ** attempt) + (attempt * 0.5)
            print(
                f"  [llm_client] {label} attempt {attempt}/{max_attempts} got "
                f"{type(exc).__name__}: {exc}; retrying in {delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
    raise RuntimeError(f"{label} exhausted retries: {last_exc}")  # pragma: no cover


def _extract_usage(response) -> dict | None:
    """Pull a plain-dict token-usage summary off a Gemini response, if present."""
    meta = getattr(response, "usage_metadata", None)
    if meta is None:
        return None
    return {
        "prompt_token_count": getattr(meta, "prompt_token_count", None),
        "candidates_token_count": getattr(meta, "candidates_token_count", None),
        "thoughts_token_count": getattr(meta, "thoughts_token_count", None),
        "total_token_count": getattr(meta, "total_token_count", None),
    }


def call_llm_with_code(
    system_prompt: str,
    user_message: str,
    dataset_path: str,
    *,
    model: str = DEFAULT_MODEL,
    thinking_budget: int = DEFAULT_THINKING_BUDGET,
    max_tokens: int = DEFAULT_CODE_MAX_TOKENS,
    max_code_calls: int = 12,
    max_attempts: int = 14,
) -> CodeLLMResponse:
    """Call the LLM with a `run_python` tool bound to a real dataset.

    This is what makes the pipeline *compute* instead of *estimate*. Gemini
    automatic function calling drives the loop: the model writes pandas, the
    SDK runs our `run_python` closure against the real CSV, feeds stdout back,
    and repeats (up to `max_code_calls`) until the model emits its final answer.

    Tool use stays in mode AUTO: the model iterates with `run_python` as much
    as it needs, then ends the loop naturally by emitting its final answer.
    Forcing mode ANY was tried and rejected — it cannot yield free text, so
    once computation is done the model pads with no-op placeholder calls.

    Extended thinking stays enabled. `response_mime_type` is NOT set — it is
    incompatible with tool use — so the final answer is free text the caller
    parses with `extract_json_output`.
    """
    from google.genai import types

    from core.data_tools import make_run_python

    client = _get_client()
    transcript: list[dict] = []
    # Defined in core.data_tools (no PEP-563 annotations) so the SDK can
    # introspect the tool's real types for automatic function calling.
    run_python, _executor = make_run_python(dataset_path, transcript)

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=max_tokens,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
        tools=[run_python],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            maximum_remote_calls=max_code_calls,
        ),
    )

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        transcript.clear()  # keep only the successful run's transcript
        try:
            response = _generate_with_retry(
                client, model, user_message, config,
                max_attempts=1, label="call_llm_with_code",
            )
            break
        except Exception as exc:  # transient — _generate_with_retry re-raises
            last_exc = exc
            if not _is_transient(exc) or attempt >= max_attempts:
                raise
            delay = min(60, 2 ** attempt) + (attempt * 0.5)
            print(
                f"  [llm_client] call_llm_with_code attempt {attempt}/"
                f"{max_attempts} got {type(exc).__name__}: {exc}; retrying in "
                f"{delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
    else:  # pragma: no cover — defensive
        raise RuntimeError(f"call_llm_with_code exhausted retries: {last_exc}")

    return CodeLLMResponse(
        text=response.text or "",
        model=model,
        usage=_extract_usage(response),
        transcript=list(transcript),
    )


_FENCE_RE = re.compile(r"^```(?:json|xml)?\s*\n?|\n?```\s*$", re.IGNORECASE | re.MULTILINE)


def extract_json_output(response_text: str) -> dict:
    """Parse JSON out of a model response, tolerating fences and stray thinking blocks."""
    if not response_text:
        raise ValueError("Empty response from model")

    text = response_text.strip()

    if "</thinking>" in text:
        text = text.split("</thinking>", 1)[-1].strip()

    text = _FENCE_RE.sub("", text).strip()

    if not text.startswith("{") and not text.startswith("["):
        first_brace = text.find("{")
        first_bracket = text.find("[")
        candidates = [i for i in (first_brace, first_bracket) if i >= 0]
        if not candidates:
            raise ValueError(f"No JSON object found in response: {response_text[:200]!r}")
        text = text[min(candidates):]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        last_close = max(text.rfind("}"), text.rfind("]"))
        if last_close > 0:
            return json.loads(text[: last_close + 1])
        raise
