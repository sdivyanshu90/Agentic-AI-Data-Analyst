# Agentic AI Data Analyst

An 11-phase agentic data-analyst pipeline. The Master Orchestrator coordinates
eleven specialist agents that pass full structured-JSON context packets between
each other and gate every phase against an explicit quality contract. The
pipeline targets a senior-analyst / analytics-lead bar: it triages before it
analyses, red-teams itself before it reports, and closes the loop with
monitoring and institutional memory after it delivers.

Provider: **Google Gemini 2.5 Pro** (extended thinking enabled by default).

## Status

| Phase | Agent | Status |
|---|---|---|
| 0 | Intake Triage & Context Calendar Check | ✅ Implemented |
| 1 | Stakeholder Requirement Gathering | ✅ Implemented |
| 2 | Data Identification & Extraction | ✅ Implemented |
| 3 | Data Quality & Cleaning | ✅ Implemented |
| 4 | Exploratory Data Analysis (hypothesis provenance) | ✅ Implemented |
| 5 | Hypothesis Testing & Validation (evidence grades) | ✅ Implemented |
| 6 | Advanced Analysis & Root Cause (confound sweep + sensitivity) | ✅ Implemented |
| 6.5 | Independent Red-Team Peer Review | ✅ Implemented |
| 7 | Visualisation & Dashboard Design | ✅ Implemented |
| 8 | Storytelling, Reporting & Handoff | ✅ Implemented |
| 9 | Impact Tracking & Monitoring Handoff | ✅ Implemented |

All 11 phase agents are implemented and the orchestrator runs the full
pipeline end to end. Core scaffolding — context packets, quality gates
(all 11), retry, pipeline state log, JSON schemas, prompt loader,
knowledge-base persistence — is complete and tested.

Pipeline flow and special routing:

```
Phase 0 triage ──QUICK_LOOKUP──▶ quick answer (pipeline skipped)
     │ FULL_PIPELINE
     ▼
1 → 2 → 3 → 4 → 5 → 6 → 6.5 ──BLOCK──▶ halt + surface required revisions
                          │ PROCEED[_WITH_REVISIONS]
                          ▼
                      7 → 8 → 9 ──▶ knowledge_base/entries.jsonl
                                     (recalled by Phase 0 next run)
```

## Setup

```bash
python3 -m pip install -r requirements.txt
echo 'GEMINI_API_KEY=your-key-here' > .env
```

## Run

```bash
# Live (requires GEMINI_API_KEY) — full 11-phase pipeline by default
python3 orchestrator/orchestrator.py \
  --objective "Analyse Q3 churn in our SaaS product" \
  --data-description "PostgreSQL DB: users, events, subscriptions" \
  --stakeholder "product team" \
  --business-domain "SaaS" \
  --tools "SQL + Python" \
  --privacy "PII must be anonymised"

# Run a subset of phases (e.g. the legacy 8-phase pipeline)
python3 orchestrator/orchestrator.py ... --phases 1,2,3,4,5,6,7,8

# Dry run — no API call, exercises the orchestrator with a canned Phase 1 output
python3 examples/sample_run/run_example.py --dry-run
```

## Tests

```bash
python3 -m pytest tests/ -v
```

238 tests covering: Phase 0–9 quality gates (every distinct failure clause
+ cross-phase invariants: Phase 0 known-event check never skipped, Phase 2
P1 coverage, Phase 4 hypothesis IDs and provenance labels, Phase 5
Phase-4-handoff coverage, MTC-when-n>3 and the DATA_DERIVED-without-holdout
⇒ EXPLORATORY guard, Phase 6 P1-question coverage, root-cause chain
integrity, confound-sweep and sensitivity-analysis requirements, Phase 6.5
anti-rubber-stamp verdict consistency, Phase 7 anti-pattern audit and
accessibility review, Phase 8 sub-question coverage and self-check gate,
Phase 9 concrete check-in dates and knowledge-base entry), JSON-schema
validation for every phase output + mission brief + pipeline state,
context-packet construction (incl. knowledge-base recall), JSON extraction
from model output, the Phase 8 agent's report/JSON-summary split, pipeline
state append-only semantics, retry context, PROMPT.md section extraction
across all 12 sections, and orchestrator interrupts (Phase 0 QUICK_LOOKUP
skip, Phase 3 row-loss user-confirm, Phase 4 PARTIAL pass-through, Phase 5
MTC + UNDERPOWERED warning, Phase 6 Simpson's paradox + HYPOTHESISED
root-cause escalation, Phase 6.5 red-team BLOCK, Phase 9 knowledge-base
persistence).

## Architecture invariants

See `CLAUDE.md` for the full rule set. Hard rules enforced in code:

1. Context packets are never truncated — all prior phase JSON travels forward.
2. Every phase passes through `check_gate` before advancing.
3. Failed gates trigger a retry with enriched context (max 3 per phase).
4. The pipeline state log is append-only.
5. Extended thinking is always on (`thinking_config` on every LLM call).
6. PROMPT.md is the source of truth for every agent's system prompt; the
   loader extracts each `<system>...</system>` block at call time.
7. The Phase 0 known-event confound check is never skipped — deadline
   pressure changes scope, never rigour.
8. DATA_DERIVED hypotheses without holdout validation are graded
   EXPLORATORY and presented as such all the way into the report.
9. A Phase 6.5 BLOCK verdict halts the pipeline before Phase 7.

## Project layout

```
core/             llm_client, prompts, context_packet, quality_gates,
                  pipeline_state, retry, code_executor, data_tools
agents/           phase0, phase1–phase8, phase65_redteam, phase9_monitoring
orchestrator/     orchestrator.py — P0 (triage/quick-answer route) → 1 → 2 →
                  3 (row-loss interrupt) → 4 → 5 (MTC/UNDERPOWERED warnings)
                  → 6 (Simpson's paradox warning) → 6.5 (red-team GO/NO-GO)
                  → 7 (anti-pattern/accessibility warnings) → 8 (final
                  Markdown report) → 9 (monitoring + knowledge base) → log
schemas/          mission_brief, pipeline_state_log,
                  phase_outputs/{phase0, phase1..8, phase6_5, phase9}
tests/            quality gates, schemas, context packet, prompts, state log
examples/         sample_run with --dry-run; orders_dataset end-to-end demo
knowledge_base/   entries.jsonl — Phase 9 institutional memory (created at runtime)
benchmark/        junior-analyst benchmark + Part C stress-test harness
```
