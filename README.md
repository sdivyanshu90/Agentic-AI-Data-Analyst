# Agentic AI Data Analyst

An 8-phase agentic data-analyst pipeline. The Master Orchestrator coordinates
eight specialist agents that pass full structured-JSON context packets between
each other and gate every phase against an explicit quality contract.

Provider: **Google Gemini 2.5 Pro** (extended thinking enabled by default).

## Status

| Phase | Agent | Status |
|---|---|---|
| 1 | Stakeholder Requirement Gathering | ✅ Implemented |
| 2 | Data Identification & Extraction | ✅ Implemented |
| 3 | Data Quality & Cleaning | ✅ Implemented |
| 4 | Exploratory Data Analysis | ✅ Implemented |
| 5 | Hypothesis Testing & Validation | ✅ Implemented |
| 6 | Advanced Analysis & Root Cause | ✅ Implemented |
| 7 | Visualisation & Dashboard Design | ✅ Implemented |
| 8 | Storytelling, Reporting & Handoff | ✅ Implemented |

All 8 phase agents are implemented and the orchestrator runs the full
pipeline end to end. Core scaffolding — context packets, quality gates
(all 8), retry, pipeline state log, JSON schemas, prompt loader — is
complete and tested.

## Setup

```bash
python3 -m pip install -r requirements.txt
echo 'GEMINI_API_KEY=your-key-here' > .env
```

## Run

```bash
# Live (requires GEMINI_API_KEY)
python3 orchestrator/orchestrator.py \
  --objective "Analyse Q3 churn in our SaaS product" \
  --data-description "PostgreSQL DB: users, events, subscriptions" \
  --stakeholder "product team" \
  --business-domain "SaaS" \
  --tools "SQL + Python" \
  --privacy "PII must be anonymised"

# Dry run — no API call, exercises the orchestrator with a canned Phase 1 output
python3 examples/sample_run/run_example.py --dry-run
```

## Tests

```bash
python3 -m pytest tests/ -v
```

152 tests covering: Phase 1–8 quality gates (every distinct failure clause
+ cross-phase invariants: Phase 2 P1 coverage, Phase 4 hypothesis IDs,
Phase 5 Phase-4-handoff coverage and MTC-when-n>3, Phase 6 P1-question
coverage and root-cause chain integrity, Phase 7 anti-pattern audit and
accessibility review, Phase 8 sub-question coverage and self-check gate),
JSON-schema validation for every phase output + mission brief + pipeline
state, context-packet construction, JSON extraction from model output
(markdown fences, `<thinking>` blocks, prose prefix), the Phase 8 agent's
report/JSON-summary split, pipeline state append-only semantics, retry
context, PROMPT.md section extraction across all 9 sections, and
orchestrator interrupts (Phase 3 row-loss user-confirm, Phase 4 PARTIAL
status pass-through, Phase 5 MTC + UNDERPOWERED warning, Phase 6 Simpson's
paradox + HYPOTHESISED root-cause escalation).

## Architecture invariants

See `CLAUDE.md` for the full rule set. Hard rules enforced in code:

1. Context packets are never truncated — all prior phase JSON travels forward.
2. Every phase passes through `check_gate` before advancing.
3. Failed gates trigger a retry with enriched context (max 3 per phase).
4. The pipeline state log is append-only.
5. Extended thinking is always on (`thinking_config` on every LLM call).
6. PROMPT.md is the source of truth for every agent's system prompt; the
   loader extracts each `<system>...</system>` block at call time.

## Project layout

```
core/             llm_client, prompts, context_packet, quality_gates,
                  pipeline_state, retry
agents/           phase1–phase8, all implemented
orchestrator/     orchestrator.py — P1 → 2 → 3 (row-loss interrupt) → 4 → 5
                  (MTC/UNDERPOWERED warnings) → 6 (Simpson's paradox warning)
                  → 7 (anti-pattern/accessibility warnings) → 8 (final
                  Markdown report) → log
schemas/          mission_brief, pipeline_state_log, phase_outputs/{phase1..8}
tests/            quality gates, schemas, context packet, prompts, state log
examples/         sample_run with --dry-run; orders_dataset end-to-end demo
```
