# Benchmark Report — Junior Data Analyst vs. Agentic AI Data Analyst

**Date:** 2026-07-06 (v3 re-evaluation; supersedes the 2026-05-20 report)
**Dataset:** IBM Telco Customer Churn — real, public, real-world use case
(7,043 customers × 21 columns, including a genuine data-quality trap)
**Task:** "What are the top drivers of customer churn, and which 2–3 interventions
would most cost-effectively reduce it?"
**Model (all LLM conditions):** `gemini-2.5-pro`, extended thinking enabled.

---

## 1. What was tested

Five "analysts" were given the **same dataset and the same business question**, then
their deliverables were scored against an objective answer key.

| Condition | What it is | Computes its numbers? | Wall-clock |
|---|---|---|---|
| **JUNIOR-B** | Naive `pandas` script — group-by churn rates, ranked by raw spread, generic recommendations. Rote junior EDA. | ✅ (own script) | < 1 s |
| **JUNIOR-A** | Single-shot LLM — one Gemini call, "act as a junior data analyst, analyse this." | ❌ (asserts from memory) | 39 s |
| **AGENTIC-v1** | The original 8-phase pipeline, *reasoning only* — no code execution. | ❌ (asserts from memory) | 809 s |
| **AGENTIC-v2** | 8-phase pipeline **+ real code execution**: phases 3–6 run pandas/scipy against the CSV via a `run_python` tool (compute-then-synthesise). | ✅ (4 executed blocks) | 713 s |
| **AGENTIC-v3** | The **11-phase senior-analyst pipeline** + code execution: Phase 0 intake triage & confound calendar, hypothesis provenance / evidence grades (4/5), systematic confound sweep + sensitivity analysis (6), **Phase 6.5 independent red-team review**, Phase 9 monitoring & knowledge base. | ✅ (11 executed blocks) | 3,257 s across three review rounds¹ |

¹ v3 was **BLOCKED twice by its own red-team reviewer** and resumed with the
required revisions each time (see §3 — this is the pipeline's headline feature,
not a failure). A run the reviewer passes first time costs ≈ 1,700 s.

**Fairness controls**
- All conditions received an identical input: a *univariate-only* data dictionary
  (`results/data_description.txt`) — column types, value counts, ranges. It contains
  **no churn-by-segment breakdown**; none of the answer was leaked.
- All LLM conditions use the same model and per-call thinking budget. The only
  variable is orchestration (and, for v2/v3, tool access to the real file).

**The answer key** (`ground_truth.py` → `results/ground_truth.json`) was computed
directly from the raw CSV with `pandas`/`scipy`: overall churn 26.5%; chi-square +
Cramér's V for every categorical; Welch t-test + Cohen's d for every numeric.
True drivers: tenure (d = 0.85), Contract (V = 0.41), OnlineSecurity (V = 0.35),
TechSupport (V = 0.34), InternetService (V = 0.32), PaymentMethod (V = 0.30);
`gender` is a distractor (V ≈ 0.00). Data-quality trap: `TotalCharges` stored as
**text** with **11 blank strings**, all tenure-0 new customers.

---

## 2. Scorecard

Seven dimensions, 0–10. Primary scores are a **calibrated manual assessment**
(every claim checked against the deliverables, the executed-code transcripts, and
the answer key). **Re-anchoring note:** unlike the May report, full marks on
statistical-rigour and data-quality now require a *computation trace* — describing
the right test is worth less than running it. Under this stricter anchor,
AGENTIC-v1's published 8.9 becomes 8.1; junior scores are unchanged.

| Dimension | JUNIOR-B | JUNIOR-A | AGENTIC-v1 | AGENTIC-v2 | AGENTIC-v3 |
|---|:--:|:--:|:--:|:--:|:--:|
| Driver coverage & correctness | 5 | 8 | 9 | 8 | 9 |
| Statistical rigour | 1 | 2 | 6² | 9 | 9 |
| Data-quality awareness | 0 | 0 | 7² | 9 | 10 |
| Confounding & root-cause depth | 1 | 4 | 8 | 8 | 10 |
| Caveat honesty & confidence calibration | 4 | 1 | 9 | 8 | 10 |
| Actionability of recommendations | 4 | 9 | 9 | 9 | 10 |
| Traceability & communication | 6 | 9 | 9 | 9 | 10 |
| **Overall (mean)** | **3.0** | **4.7** | **8.1** | **8.6** | **9.7** |
| *LLM-judge cross-check* | *4.1* | *5.1* | *10.0³* | *7.7* | *8.9* |
| *Numbers matching ground truth (regex scan)* | *7/8* | *7/8* | *8/8* | *7/8* | *7/8* |
| *Computation trace for those numbers* | *own script* | *none* | *none* | *4 blocks* | *11 blocks* |

² v1 named the right tests and the right fixes but executed nothing — its correct
figures are memorised (Telco is a famous dataset), not derived. On a private
dataset they would be guesses.
³ The v1 judge score is a halo artifact (see §6).

**Verdict: AGENTIC-v3 9.7 > v2 8.6 > v1 8.1 ≫ JUNIOR-A 4.7 > JUNIOR-B 3.0.**
The v1→v2 gain is *epistemic* (numbers become computed facts instead of recalled
claims). The v2→v3 gain is *judgment*: an independent reviewer caught two real
statistical errors that v2 shipped uncaught, and the final deliverable's
confidence labels survived adversarial review instead of merely sounding rigorous.

---

## 3. What the red team caught — the v3 story

The single most important result of this re-evaluation: **on real data, the
Phase 6.5 red-team reviewer twice refused to let the analysis ship, and both
times it was right.**

**Round 1 — BLOCKED.** The Phase 6 logistic regression ranked `TotalCharges`
(odds ratio 2.10) as the **#2 churn driver** — a textbook multicollinearity
artifact: `TotalCharges ≈ tenure × MonthlyCharges`, and tenure's protective
effect flips the sign of its collinear partner. v2 shipped exactly this class of
model unreviewed ("logistic regression confirmed the independent effects of the
top drivers"). The reviewer ordered: rebuild the model without `TotalCharges`;
check the Phase 0 marketing-campaign confound against the early-life-churn root
cause; downgrade over-graded evidence; add a self-selection caveat to the
Tech-Support impact estimate.

**Round 2 — BLOCKED again, on new findings.** After the rebuild, the reviewer
attacked the *revised* analysis: H1's headline finding rested on p = 0.032 which
**fails multiple-testing correction** with an odds-ratio CI of [1.16, 26.99];
the M2M-Fiber root cause ignored a simpler price-based alternative; Electronic
Check churn might be a **non-causal demographic proxy**, not "payment friction".

**Round 3 — PROCEED_WITH_REVISIONS.** With cumulative revisions applied (and a
review protocol stating that BLOCK is reserved for unapplied revisions or new
critical flaws), the reviewer verified the fixes, still flagged two residual
overclaims (one insight downgraded HIGH → MEDIUM), and let it ship. The final
report demonstrably contains every ordered change: Finding 3's confidence is
MEDIUM with the mix-shift explanation ("high early-life churn is primarily an
artifact of most new customers being on month-to-month contracts"), Finding 2
uses the conservative multivariate odds ratio (1.36) and carries the proxy
caveat, and the caveats section discloses self-selection bias, the unmeasured
service-quality confound, and the single-dataset exploratory nature of all
findings.

Two supporting mechanisms earned their keep during the loop:
- The **provenance anti-drift gate** rejected Phase 5's attempt to honour a
  downgrade by *relabelling* H2 as DATA_DERIVED (rewriting history) instead of
  downgrading its evidence grade — the honest path.
- The **resume mechanism** (`user_clarifications` + `resume_outputs`) let each
  round re-run only the phases a revision touched, with the reviewer's orders
  binding in every downstream context packet.

Phase 0 also did its job on a dataset with no stated events: it proactively asked
three change-calendar questions (pricing changes? outages? campaigns?) — and the
round-1 reviewer used exactly that unresolved campaign confound to block the
early-life-churn conclusion.

---

## 4. Where the gaps open — condensed

**Reasoning → computing (v1 → v2).** v1's report cites Cramér's V = 0.409 and
"11 blanks imputed" without ever touching the file — correct only because Telco
is memorised. v2/v3's transcripts show the actual pandas/scipy runs (overall
churn 26.54%, M2M 42.7%, e-check 45.3%, the 11 tenure-0 blanks found and
investigated before imputation). On a private dataset, v1's numbers would be
fabrications; v2/v3's would still be facts.

**Computing → judging (v2 → v3).** v2 ran real statistics but graded its own
homework: the collinear regression, the un-swept campaign confound, and the
missing self-selection caveat all shipped. v3's independent reviewer — a separate
agent with an adversarial system prompt and code access — caught all three, plus
the marginal-significance overclaim in the revised analysis. The quality gates
enforce *completeness*; the red team enforces *correctness of judgment*. They are
different failure modes and needed different mechanisms.

**Closing the loop (v3 only).** v3 is the only condition whose deliverable
extends past the report: 4 success metrics with owners and concrete check-in
dates (2026-09-06 / 2026-10-06), 4 implementable drift alerts, and a
knowledge-base entry whose recorded gotchas are precisely the traps this run hit
— TotalCharges type coercion, tenure×TotalCharges multicollinearity, the
early-life mix-shift trap, add-on self-selection bias, and the unmeasured
service-quality confound. A future run on a related question recalls these at
Phase 0 instead of rediscovering them.

**Where the juniors remain competitive.** Actionability and polish: JUNIOR-A's
memo scores 9 on both — a modern LLM is already a fluent junior analyst on the
surface deliverable. Every agentic gain is in the rigour underneath.

---

## 5. Verification — did the pipeline actually work on real data?

- All 11 phases COMPLETE in the final leg; every quality gate ultimately passed
  (6 gate-retries across the three legs, each with an enriched failure reason —
  e.g. truncated Phase 6 output caught by the P1-coverage cross-check).
- **11 executed code blocks** across the legs (transcripts in
  `agentic_v3_outputs/phase*_transcript_*.json`), grounding the cleaning
  decisions, hypothesis tests, confound sweep, and the rebuilt regression.
- Headline figures match ground truth (M2M 42.7%, two-year 2.8%, fiber 41.9%,
  e-check 45.3%, 11 TotalCharges blanks; 7/8 on the regex scan — the miss is the
  overall-churn phrasing, not an error).
- Red-team verdict PROCEED_WITH_REVISIONS recorded in
  `results/agentic_v3_phase_outputs.json`; the three-round history in
  `results/agentic_v3_meta.json`; the knowledge-base entry in
  `results/v3_knowledge/entries.jsonl`.

---

## 6. Threats to validity — read before quoting these numbers

1. **Memorisation confound — now partially controlled.** Telco is heavily
   memorised; in v1 that inflated apparent rigour. v2/v3's executed-code
   transcripts replace recall with derivation for the figures they compute.
   Residual risk: phases whose compute step ran no code (mode AUTO permits it;
   the harness retries up to 4×, but adherence varies by phase and leg) may
   still lean on recall. The transcript files show exactly which figures are
   proven.
2. **LLM-judge noise.** The judge gave v1 a flat 10.0 (halo from a long,
   confident, rubric-shaped report), v2 a 7.7 (docking appendix-documented
   data-quality work), and v3 an 8.9 with statistical-rigour 4 — punishing v3
   for keeping p-values in the appendix of an executive report *after the red
   team deliberately made its claims more conservative*. Honesty reads as
   weakness to a rubric-matching judge. The manual scorecard corrects this;
   the judge is a directional cross-check only.
3. **Reviewer strictness and convergence.** The red team blocked twice; round 2
   raised new, legitimate issues about the revised analysis. Left unmanaged this
   could loop. The round-3 resume added an explicit review protocol (BLOCK only
   for unapplied revisions or new critical flaws) — the analogue of a real
   team's review-round norms. Operators should expect 1–3 rounds and budget for
   it, or cap rounds and downgrade a repeat-BLOCK to PROCEED_WITH_REVISIONS
   with full disclosure.
4. **n = 1 per condition.** One dataset, one run each. Magnitudes are
   indicative, not statistically robust. The v3 review loop is itself
   stochastic — a luckier first pass would have shipped in one round.
5. **Cost & latency.** JUNIOR-A: 1 call / 39 s. v1: ~8 calls / 809 s.
   v2: ~16 calls / 713 s. v3: ~30–40 calls / 3,257 s including two review-blocks
   (≈ 1,700 s if the reviewer passes first time) — roughly **40–80× JUNIOR-A's
   latency** for +5.0 points of calibrated quality. The pipeline is justified
   when the decision must be defensible; for a throwaway look-up, Phase 0's own
   triage will route to a quick answer instead.
6. Minor: the report byline still reads "Claude Opus" — a hardcoded string in
   `PROMPT.md`, cosmetic only.

---

## 7. Conclusion

On a real, third-party dataset, the upgraded pipeline's calibrated score rises
from **8.1 (v1) → 8.6 (v2) → 9.7 (v3)** against junior baselines of 3.0/4.7 —
and the *composition* of the gain matters more than its size. v2 fixed the
epistemics: every headline number now has an executed-code trace. v3 fixed the
judgment: an independent adversarial reviewer twice stopped real statistical
errors — a collinearity-inverted driver ranking and a marginal finding dressed
as confirmed — that the v2 pipeline, with identical statistical machinery,
shipped without a second look. The final v3 report is *less* confident than
v2's and *more* correct, which is precisely the trade a senior analyst is paid
to make. The remaining frontier is consistency of the compute step (no phase
should ever ship an un-executed figure) and review-loop convergence policy —
both operational, neither requiring a smarter model.

---

## 8. Reproduce

```bash
# answer key + shared input
python3 benchmark/ground_truth.py
python3 benchmark/dataset_profile.py

# baselines
python3 benchmark/junior_b_pandas.py
python3 benchmark/junior_a_llm.py           # 1 Gemini call

# pipeline conditions
python3 benchmark/run_agentic.py            # v1: 8-phase, reasoning only
python3 benchmark/run_agentic_v2.py         # v2: 8-phase + code execution
python3 benchmark/run_agentic_v3.py         # v3: 11-phase + code execution
python3 benchmark/resume_agentic_v3.py      # v3: resume after a red-team BLOCK
                                            #     (edit REQUIRED_REVISIONS to match
                                            #      the verdict in your run's state log)

# scoring
python3 benchmark/score.py                  # juniors + v1 -> results/scores.json
python3 benchmark/score_v2.py               # v2 -> results/scores_v2.json
python3 benchmark/score_v3.py               # v3 -> results/scores_v3.json (incl. process audit)
```

All inputs, deliverables, scores, per-phase outputs, executed-code transcripts,
pipeline state logs, and the knowledge-base entry are under `benchmark/results/`,
`benchmark/agentic_v3_outputs/`, and `benchmark/agentic_v3_logs/`.
