# CLAUDE.md — Agentic AI Data Analyst Pipeline
## Claude Code Project Memory · Claude Opus 4 · 8-Phase Agentic System

---

## Project Overview

This project is a fully agentic, multi-phase Data Analyst pipeline where Claude Opus acts as **every role** a junior data analyst performs — from stakeholder requirement gathering through to final report delivery. It is not a single prompt; it is an orchestrated system of 9 Claude instances (1 Orchestrator + 8 Phase Agents) that pass structured context packets between each other and iterate autonomously.

**Model:** `claude-opus-4-6`
**Thinking:** Extended thinking enabled on all agents (`budget_tokens: 4096`)
**Source of truth for all prompts:** `PROMPT.md` in project root

---

## Repository Structure

```
/
├── CLAUDE.md                        ← You are here
├── PROMPT.md                        ← All 9 system prompts (master source)
├── orchestrator/
│   └── orchestrator.py              ← Master Orchestrator logic
├── agents/
│   ├── phase1_requirements.py       ← Stakeholder Requirement Gathering
│   ├── phase2_extraction.py         ← Data Identification & Extraction
│   ├── phase3_cleaning.py           ← Data Quality & Cleaning
│   ├── phase4_eda.py                ← Exploratory Data Analysis
│   ├── phase5_hypothesis.py         ← Hypothesis Testing & Validation
│   ├── phase6_advanced.py           ← Advanced Analysis & Root Cause
│   ├── phase7_visualisation.py      ← Visualisation & Dashboard Design
│   └── phase8_reporting.py          ← Storytelling, Reporting & Handoff
├── core/
│   ├── context_packet.py            ← Context packet builder & validator
│   ├── quality_gates.py             ← Per-phase quality gate logic
│   ├── pipeline_state.py            ← PIPELINE STATE LOG manager
│   └── retry.py                     ← Retry logic with enriched context
├── schemas/
│   ├── mission_brief.json           ← Mission brief JSON schema
│   ├── phase_outputs/               ← One JSON schema per phase output
│   └── pipeline_state_log.json      ← Pipeline state log schema
├── tests/
│   ├── test_quality_gates.py
│   ├── test_context_packet.py
│   └── test_phase_outputs.py        ← Validates each phase JSON against schema
├── examples/
│   └── sample_run/                  ← End-to-end example with dummy data
└── requirements.txt
```

---

## The 8-Phase Pipeline at a Glance

| # | Phase | Agent Role | Key Output |
|---|---|---|---|
| 1 | Stakeholder Requirement Gathering | Business + Data Analyst hybrid | Mission Brief + Sub-questions + KPIs |
| 2 | Data Identification & Extraction | Data Engineer + Analyst | Schema, SQL queries, Data Dictionary |
| 3 | Data Quality & Cleaning | Detail-obsessed QA Analyst | Change Log, Clean Schema, Validation Report |
| 4 | Exploratory Data Analysis | Investigative Detective Analyst | EDA findings, Viz Specs, Hypotheses |
| 5 | Hypothesis Testing & Validation | Statistical Conscience | Test results, p-values, Effect sizes |
| 6 | Advanced Analysis & Root Cause | Senior Analyst Mentor | Root Cause Chains, Impact Quantification |
| 7 | Visualisation & Dashboard Design | BI + Accessibility Expert | Dashboard Architecture, Chart Specs |
| 8 | Storytelling, Reporting & Handoff | Executive Communicator | Final Markdown Report + JSON Summary |

**Orchestrator** sits above all 8 phases: routes context, enforces quality gates, manages retries (max 3 per phase), maintains the PIPELINE STATE LOG.

---

## How to Run the Pipeline

### Quickstart
```bash
pip install -r requirements.txt
python orchestrator/orchestrator.py \
  --objective "Analyse Q3 churn in our SaaS product" \
  --data-description "PostgreSQL DB with users, events, subscriptions tables" \
  --stakeholder "product team" \
  --output-format report
```

### Programmatic invocation
```python
from orchestrator.orchestrator import DataAnalystOrchestrator

pipeline = DataAnalystOrchestrator(
    model="claude-opus-4-6",
    thinking_budget=4096,
    max_retries_per_phase=3
)

result = pipeline.run(
    objective="Analyse Q3 churn in our SaaS product",
    data_description="PostgreSQL DB: users, events, subscriptions",
    stakeholder_type="product team",
    constraints={"tools": "SQL + Python", "privacy": "PII must be anonymised"}
)

print(result.final_report)          # Markdown report
print(result.pipeline_state_log)    # Full audit trail JSON
```

---

## Core Architecture Rules

### 1. Context Packet — Never Truncate

Every agent call receives a **full context packet**. Never summarise or abbreviate prior phase outputs when passing them forward. Pass structured JSON in full.

```python
# core/context_packet.py
def build_context_packet(mission_brief, all_phase_outputs, pipeline_state_log):
    return {
        "mission_brief": mission_brief,           # verbatim from Phase 1
        "prior_outputs": all_phase_outputs,        # ALL phases completed so far
        "pipeline_state": pipeline_state_log       # full Orchestrator log
    }
```

The user message passed to every phase agent is:
```python
user_message = f"""
<context_packet>
{json.dumps(context_packet, indent=2)}
</context_packet>

You are Phase {phase_number} Agent. Execute your tasks against the context
packet above. Produce your structured JSON output exactly as specified in
your system prompt's <output_format> section.
"""
```

### 2. Extended Thinking — Always On

All Claude API calls in this project must enable extended thinking:
```python
def call_claude(system_prompt, user_message):
    return anthropic.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        thinking={"type": "enabled", "budget_tokens": 4096},
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
```

Never disable thinking for any phase. Phases with `<extended_thinking_instruction>` blocks in PROMPT.md rely on it for hypothesis validation, root cause reasoning, and quality self-checks.

### 3. Quality Gates — Block Before Advancing

Each phase has a quality gate defined in `core/quality_gates.py`. The Orchestrator **must** pass the output through its gate before advancing to the next phase.

```python
# core/quality_gates.py
GATES = {
    1: lambda out: (
        "objective" in out["mission_brief"] and
        len(out["sub_questions"]) >= 3 and
        out["success_definition"] != ""
    ),
    2: lambda out: (
        any(s["availability"] == "CONFIRMED" for s in out["data_source_map"]) and
        len(out["governance_flags"]) >= 0  # must be present even if empty
    ),
    3: lambda out: (
        out["validation_suite"]["null_check"] == "PASSED" and
        len(out["change_log"]) > 0 and
        out["validation_suite"]["row_loss_pct"] < 20.0
    ),
    4: lambda out: (
        len(out["hypotheses"]) >= 2 and
        all("reasoning" in h for h in out["hypotheses"])
    ),
    5: lambda out: (
        all(t["p_value"] is not None for t in out["tests_conducted"]) and
        all(t["result"] in ["SUPPORTED","REJECTED","INCONCLUSIVE"]
            for t in out["tests_conducted"])
    ),
    6: lambda out: (
        len(out["root_cause_chains"]) > 0 and
        len(out["insight_ranking"]) > 0
    ),
    7: lambda out: (
        len(out["visualisation_specs"]) > 0 and
        out["accessibility_review"]["colourblind_safe"] is True
    ),
    8: lambda out: (
        len(out["phase_8_summary"]["sub_questions_answered"]) > 0 and
        out["phase_8_summary"]["quality_gate_checks_failed"] == 0
    ),
}

def check_gate(phase_number, output):
    return GATES[phase_number](output)
```

### 4. Retry Logic — Enrich, Never Repeat

If a quality gate fails, retry with an **enriched context** that includes the failure reason. Never retry with identical input.

```python
# core/retry.py
def retry_with_enriched_context(phase, failed_output, gate_result, context_packet):
    enriched = context_packet.copy()
    enriched["retry_context"] = {
        "attempt": failed_output.get("attempt_count", 1) + 1,
        "previous_output": failed_output,
        "quality_gate_failure_reason": gate_result.failure_reason,
        "specific_instruction": f"Your previous output failed the quality gate "
                                f"because: {gate_result.failure_reason}. "
                                f"Fix this specific issue and re-run all tasks."
    }
    return enriched
```

Max retries per phase: **3**. After 3 failures, the Orchestrator surfaces the blocker to the user.

### 5. Pipeline State Log — Append Only

The `PIPELINE STATE LOG` is append-only. Never overwrite a previous phase entry.

```python
# core/pipeline_state.py
class PipelineStateLog:
    def append_phase(self, phase_number, phase_name, status,
                     key_decisions, reasoning_summary, output_summary,
                     quality_gate_passed):
        entry = {
            "phase_number": phase_number,
            "phase_name": phase_name,
            "status": status,
            "attempt_count": self._get_attempt_count(phase_number),
            "key_decisions": key_decisions,
            "reasoning_summary": reasoning_summary,
            "output_summary": output_summary,
            "quality_gate_passed": quality_gate_passed,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.state["phases"].append(entry)
        # NEVER modify existing entries
```

---

## Coding Conventions

### Output Parsing

Every phase agent returns JSON. Extract it defensively:
```python
def extract_json_output(response_text):
    # Claude may wrap JSON in markdown fences — strip them
    clean = re.sub(r"```json\n?|\n?```", "", response_text).strip()
    # Also handle <thinking> blocks — extract only content after them
    if "<thinking>" in clean:
        clean = clean.split("</thinking>")[-1].strip()
    return json.loads(clean)
```

### Reasoning Fields Are Mandatory

All phase output schemas include `reasoning` fields. If a parsed output is missing a reasoning field on a decision node, flag it as a quality gate failure — do not silently accept outputs that skip reasoning.

```python
def validate_reasoning_fields(phase_output, required_reasoning_paths):
    for path in required_reasoning_paths:
        value = get_nested(phase_output, path)
        if not value or value.strip() == "":
            raise QualityGateError(f"Missing reasoning at: {path}")
```

### Status Field Contract

Every phase output JSON must contain a `"status"` field. Valid values:
- `"COMPLETE"` — quality gate can evaluate
- `"NEEDS_RETRY"` — agent self-flagged; trigger retry immediately
- `"CLARIFICATION_NEEDED"` — pause pipeline, surface question to user
- `"PARTIAL"` — Phase 4 and 6 only; advance but flag incomplete items
- `"BLOCKED"` — Phase 2 only; missing data access blocks extraction

---

## Phase-Specific Notes

### Phase 1 — Requirement Gathering
- If `status == "CLARIFICATION_NEEDED"`, read `output["clarification_needed"]` and ask the user. Do not advance until answered.
- Sub-questions must be labelled P1/P2/P3. Only P1 questions are mandatory for downstream phases.
- The `downstream_phase_goals` block is the north star for all later agents — treat it as the project charter.

### Phase 2 — Data Extraction
- If schema is `INFERRED` (not confirmed), always add a `⚠️ SCHEMA INFERRED` warning in the Phase Transition Card shown to the user.
- SQL queries written here are pseudocode unless the user has provided actual table names. Label clearly.
- `governance_flags` with PII columns must be resolved before Phase 3 proceeds.

### Phase 3 — Data Cleaning
- Row loss > 20% must trigger a user confirmation before proceeding, even if quality gate passes.
- The `change_log` is the reproducibility record. It is appended to the Phase 8 Methodology Appendix verbatim.
- The `bias_audit` result flows directly into Phase 8's Caveats section — never omit it.

### Phase 4 — EDA
- Hypotheses formed here are passed as `phase_5_handoff.hypotheses_to_test` — preserve the exact H[n] ID format.
- `eda_visualisation_spec` entries are consumed verbatim by Phase 7 — do not transform them.
- If `status == "PARTIAL"`, list which variables were not profiled and why in the Transition Card.

### Phase 5 — Hypothesis Testing
- If `multiple_testing_correction.applied == true`, Phase 6 should only investigate hypotheses in `hypotheses_surviving_correction`.
- `statistical_caveats` array feeds Phase 8 Caveats section — preserve order.
- Never let Phase 8 present a finding as HIGH confidence if Phase 5 rated it MEDIUM or LOW.

### Phase 6 — Advanced Analysis
- `simpson_paradox_detected: true` must always escalate to the user via Transition Card with explicit warning.
- `root_cause_chains` where `root_cause.status == "HYPOTHESISED"` must be labelled as such in Phase 8 findings.
- `unanswered_subquestions` must appear in Phase 8 Next Steps section.

### Phase 7 — Visualisation
- Anti-pattern audit is non-optional. Any `anti_pattern_found` entry must have a corresponding `correction_applied`.
- Chart titles must be insight headlines (state the finding, not the category). Enforce this in Phase 8's visualisation manifest.
- `accessibility_review.wcag_contrast_met: false` blocks Phase 8 — fix the palette before advancing.

### Phase 8 — Reporting
- Run the 9-point self-check quality gate before generating any output. Failures are fixed inline.
- Tone calibration is driven by Phase 1's `stakeholder_profile.technical_tolerance`. Match it strictly.
- The JSON summary block at the end of Phase 8 output is the final entry in the PIPELINE STATE LOG.

---

## Phase Transition Card — Display Format

After every phase, display this to the user before advancing:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▶ PHASE [N] COMPLETE — [Phase Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT THE AGENT DID:
  [2–3 sentences]

KEY DECISIONS MADE:
  • [Decision + why]

OUTPUT SUMMARY:
  [1–2 sentences]

QUALITY GATE: ✓ PASSED / ✗ FAILED (reason)

ADVANCING TO: Phase [N+1] — [Next Phase Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-...         # Required
PIPELINE_LOG_DIR=./logs          # Where PIPELINE STATE LOGs are saved
PIPELINE_OUTPUT_DIR=./outputs    # Where final reports are written
MAX_RETRIES_PER_PHASE=3          # Default: 3
THINKING_BUDGET_TOKENS=4096      # Default: 4096
MAX_TOKENS_PER_CALL=8192         # Default: 8192
ROW_LOSS_ALERT_THRESHOLD=0.20    # Phase 3: alert user if >20% rows dropped
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test a single phase's quality gate
pytest tests/test_quality_gates.py::test_phase3_gate -v

# Run the full pipeline on example data (dry run — no live API calls)
python examples/sample_run/run_example.py --dry-run

# Validate all phase output JSON schemas
pytest tests/test_phase_outputs.py -v
```

### What to test for each phase

| Phase | Critical test | Why |
|---|---|---|
| 1 | `reasoning` present on all decisions | Audit trail requirement |
| 2 | No SQL query without a comment block | Reproducibility |
| 3 | `change_log` entry count ≥ cleaning decision count | Every change must be logged |
| 3 | `row_loss_pct` computed correctly | Data integrity |
| 4 | Every hypothesis has `expected_test_type` | Handoff to Phase 5 |
| 5 | p-values are floats, not strings | Parsing robustness |
| 5 | `multiple_testing_correction.applied` when n > 3 | Statistical rigour |
| 6 | Root cause chain has ≥ 3 links | SYMPTOM → PROXIMATE → ROOT minimum |
| 7 | All charts pass anti-pattern audit | Visualisation integrity |
| 8 | Every P1 sub-question appears in findings | Completeness gate |

---

## Key Invariants — Never Violate

These are hard rules. If code or prompts you write would break one, stop and find a different approach.

1. **Never truncate the context packet.** All prior phase JSON outputs travel forward in full.
2. **Never skip the quality gate.** Even if output looks correct — run the gate.
3. **Never advance past a BLOCKED status** without user input.
4. **Never present a finding as HIGH confidence** if Phase 5 rated it otherwise.
5. **Never drop rows in Phase 3** without a `change_log` entry and a documented reason.
6. **Never fabricate data.** If the dataset doesn't contain something, document the gap.
7. **Never let Phase 8 recommend something** that doesn't trace back through Phase 6 root cause.
8. **Never disable extended thinking.** It is core to reasoning quality across all phases.
9. **Never use a pie chart with >4 slices** in Phase 7 visualisation specs.
10. **Never overwrite a pipeline state log entry.** The log is append-only.

---

## Adding a New Phase

If a new phase is ever added between existing ones:
1. Add the system prompt to `PROMPT.md` in position
2. Re-number all downstream phase references in every affected prompt
3. Add a quality gate in `core/quality_gates.py`
4. Add a JSON schema in `schemas/phase_outputs/`
5. Update `orchestrator.py` phase routing
6. Update this `CLAUDE.md` with the new phase's notes
7. Add tests in `tests/test_quality_gates.py` and `tests/test_phase_outputs.py`
8. Update the pipeline diagram in `README.md`

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `JSONDecodeError` on phase output | `<thinking>` block not stripped | Use `extract_json_output()` in `core/context_packet.py` |
| Phase 3 quality gate fails on null check | Phase 2 schema had unconfirmed columns | Retry Phase 3 with explicit ACCEPT_AS_IS decision for unresolvable nulls |
| Phase 5 `p_value: null` | Agent returned inconclusive without running test | Enrich retry with: "You must run the test and return a numeric p-value, even if the result is INCONCLUSIVE" |
| Phase 8 confidence mismatch | Phase 8 over-stated a finding | Add Phase 5 `findings_summary` directly to Phase 8 context and instruct agent to cross-reference before writing |
| Row loss > 20% in Phase 3 | Aggressive null dropping | Ask user for guidance before re-running Phase 3 with softer imputation strategy |
| `CLARIFICATION_NEEDED` loop | User answer didn't resolve ambiguity | Extract the exact `clarification_needed` field and re-ask with that verbatim |

---

## Design Principles Reference

| Principle | Implementation |
|---|---|
| Every decision has explicit reasoning | `reasoning` field required in all phase schemas |
| Agents self-correct before escalating | `NEEDS_RETRY` status + retry logic |
| Context is cumulative, never truncated | Full JSON forwarded in every context packet |
| Confidence is calibrated, not inflated | Phase 5 → Phase 8 fidelity enforced in quality gate |
| GIGO prevention at source | Phase 3 validation suite + bias audit |
| Stakeholder-aware output | Phase 1 profile → Phase 8 tone calibration |
| Statistical rigour without overreach | Power analysis + multiple testing correction in Phase 5 |
| Every recommendation is traceable | Evidence chain requirement in Phase 8 |
| Analysis lifecycle is honest | Caveats, limitations, unanswered questions in Phase 8 |
| Extended thinking is mandatory | `thinking: {type: enabled}` on every API call |

---

*CLAUDE.md version 1.0 · Agentic AI Data Analyst · 8 phases · Claude Opus 4*
