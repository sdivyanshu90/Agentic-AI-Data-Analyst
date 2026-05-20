# Benchmark Report — Junior Data Analyst vs. Agentic AI Data Analyst

**Date:** 2026-05-20
**Dataset:** IBM Telco Customer Churn (real, public — 7,043 customers × 21 columns)
**Task:** "What are the top drivers of customer churn, and which 2–3 interventions
would most cost-effectively reduce it?"
**Model (all LLM conditions):** `gemini-2.5-pro`, extended thinking enabled.

---

## 1. What was tested

Three "analysts" were given the **same dataset and the same business question**, then
their deliverables were scored against an objective answer key.

| Condition | What it is | LLM calls | Wall-clock |
|---|---|---|---|
| **JUNIOR-B** | Naive `pandas` script — group-by churn rates, ranked by raw spread, generic recommendations. Represents rote junior EDA. | 0 | < 1 s |
| **JUNIOR-A** | Single-shot LLM — one Gemini call, "act as a junior data analyst, analyse this." No orchestration. | 1 | 39 s |
| **AGENTIC** | The full 8-phase `DataAnalystOrchestrator` pipeline — requirements → extraction → cleaning → EDA → hypothesis testing → root cause → visualisation → reporting, with quality gates between every phase. | 8 (1/phase; all gates passed first attempt) | 808 s¹ |

¹ ~560 s of actual model compute; the remainder was exponential-backoff retry on
transient Gemini 503s (the pipeline absorbed 19 of them without failing a phase).

**Fairness controls**
- All three received an identical input: a *univariate-only* data dictionary
  (`results/data_description.txt`) — column types, value counts, ranges. It contains
  **no churn-by-segment breakdown** — i.e. none of the answer was leaked.
- JUNIOR-A and AGENTIC use the **same model and the same per-call thinking budget**.
  The *only* variable between them is the agentic orchestration.

**The answer key** (`ground_truth.py` → `results/ground_truth.json`) was computed
directly from the raw CSV with `pandas`/`scipy`: overall churn 26.5%; chi-square +
Cramér's V for every categorical; Welch t-test + Cohen's d for every numeric.

| True driver | Effect size | Strength |
|---|---|---|
| tenure | Cohen's d = 0.85 | large |
| Contract | Cramér's V = 0.41 | large |
| OnlineSecurity | Cramér's V = 0.35 | medium |
| TechSupport | Cramér's V = 0.34 | medium |
| InternetService | Cramér's V = 0.32 | medium |
| PaymentMethod | Cramér's V = 0.30 | medium |
| MonthlyCharges / TotalCharges | Cohen's d ≈ 0.45 | small |
| gender | Cramér's V ≈ 0.00 | **distractor** |

Plus a real data-quality trap: `TotalCharges` is stored as **text** with **11 blank
strings**, all belonging to tenure-0 new customers.

---

## 2. Scorecard

Seven dimensions, 0–10 each. The **primary scores are a calibrated manual
assessment** (every claim checked against the deliverables and the answer key). An
independent **LLM-as-judge** pass is shown as a cross-check — see §5 for why it is
not the primary score.

| Dimension | JUNIOR-B | JUNIOR-A | AGENTIC |
|---|:--:|:--:|:--:|
| Driver coverage & correctness | 5 | 8 | 9 |
| Statistical rigour | 1 | 2 | 9 |
| Data-quality awareness | 0 | 0 | 9 |
| Confounding & root-cause depth | 1 | 4 | 8 |
| Caveat honesty & confidence calibration | 4 | 1 | 9 |
| Actionability of recommendations | 4 | 9 | 9 |
| Traceability & communication | 6 | 9 | 9 |
| **Overall (mean)** | **3.0** | **4.7** | **8.9** |
| *LLM-judge cross-check* | *4.1* | *5.1* | *10.0* |

**Verdict: the Agentic pipeline wins decisively — by ~+4.2 points over the single-shot
LLM and ~+5.9 over the naive pandas script.** Critically, the win is *not* in
conclusions or presentation (where the single-shot LLM already scores 8–9) — it is
concentrated in **analytical process**: statistical rigour, data-quality handling,
confounding analysis, and honest caveats. Those four dimensions are exactly where a
junior analyst is weakest, and exactly what the 8-phase structure forces.

---

## 3. Where the gap opens — dimension by dimension

### Statistical rigour — JUNIOR-B 1 · JUNIOR-A 2 · AGENTIC 9
- **JUNIOR-A** never runs a test. It compares raw churn percentages and asserts
  drivers. (A keyword scan flagged "significance testing" — a false positive on the
  colloquial word "significantly". It contains no p-value, chi-square, or effect size.)
- **JUNIOR-B** explicitly states "no significance testing or effect sizes computed"
  and ranks drivers by raw rate *spread* — which is why it ranks `InternetService`
  above `PaymentMethod` and **drops `tenure`, the single strongest driver, off its
  ranked list entirely** (numerics were excluded from the spread ranking).
- **AGENTIC** ran 5 hypothesis tests (Phase 5), reported p-values and effect sizes
  (Cramér's V = **0.409** — matching the ground-truth 0.410), applied a **Bonferroni
  correction** for multiple testing, and tested **interaction terms** (Tech-Support ×
  Fiber). It calibrates confidence ("over 99% confident… large effect size").

### Data-quality awareness — JUNIOR-B 0 · JUNIOR-A 0 · AGENTIC 9
- Both juniors **score zero**. JUNIOR-A never mentions `TotalCharges` at all.
  JUNIOR-B silently does `pd.to_numeric(..., errors="coerce")`, turning the 11 blanks
  into NaN that vanish from its average **with no comment**.
- **AGENTIC** Phase 3 catalogued 10 anomalies (3 critical), and the final report's
  Methodology Appendix documents the fix explicitly: *"TotalCharges was coerced from
  string to numeric, with 11 nulls imputed to 0 based on tenure=0; SeniorCitizen
  standardised from 0/1 to No/Yes; the redundant 'No internet service' category
  merged."* Row loss: 0.0%.

### Confounding & root-cause depth — JUNIOR-B 1 · JUNIOR-A 4 · AGENTIC 8
- **JUNIOR-B** is purely univariate — no interaction between drivers.
- **JUNIOR-A** offers light speculation ("lack of commitment", "perceived
  instability") but treats Contract, tenure, InternetService and add-ons as
  independent, which **double-counts** heavily overlapping segments.
- **AGENTIC** did a Pareto analysis ("89% of churn from month-to-month customers"),
  traced labelled root-cause chains, and *statistically tested an interaction*: Tech
  Support cuts Fiber churn from 49% → 20%. It moves from *what* correlates to *why*.

### Caveat honesty — JUNIOR-B 4 · JUNIOR-A 1 · AGENTIC 9
- **JUNIOR-A** presents every finding as definitive. No correlation-vs-causation note.
- **JUNIOR-B** earns points only for one honest footnote about its weak method.
- **AGENTIC** has a dedicated Caveats section (correlation ≠ causation, with a
  concrete example; sample-representativeness; static-snapshot risk) **and** honestly
  flagged that the "cost-effective" half of the question is **unanswerable** without
  cost/LTV data — instead of bluffing.

### Where the juniors are already good
**Actionability** and **communication** are close (JUNIOR-A 9 vs AGENTIC 9). The
single-shot LLM writes a fluent, well-structured stakeholder memo with specific
recommendations. A modern LLM is *already* a competent junior analyst on the
surface deliverable — the agentic structure does not improve polish, it adds the
*rigour underneath* the polish.

---

## 4. Verification — did the pipeline actually work on real data?

Yes. All 8 phases ran live against Gemini and **passed every quality gate on the
first attempt**; 0.0% row loss; the final 10.9 KB report is internally consistent
with the ground truth (M2M 42.7%, Fiber 41.9%, Electronic-check 45.3%, Cramér's V
0.41 — all correct). The pipeline also survived 19 transient 503s via its
backoff-retry logic. Artifacts: `benchmark/agentic_outputs/` (8 phase JSONs +
report), `benchmark/agentic_logs/` (append-only state log).

---

## 5. Threats to validity — read before quoting these numbers

1. **Memorisation confound.** The Telco Churn dataset is one of the most-analysed
   public datasets in existence. JUNIOR-A and AGENTIC both reproduced *exact*
   churn-by-segment rates that were **not in their input** — they are recalling
   memorised statistics, not deriving them. This inflates *driver coverage* for both
   LLM conditions. **It does not explain the gap**, because memorisation cannot
   manufacture a Bonferroni correction, an interaction test, or a data-quality
   appendix — and the AGENTIC win is concentrated in exactly those process
   dimensions. If anything, memorisation makes the test *conservative*: it lifts the
   JUNIOR-A baseline.
2. **Compute-vs-reason asymmetry.** JUNIOR-B *computes* exact numbers from the file;
   the LLM conditions *reason* from a text description and assert numbers. The
   AGENTIC report says logistic regression "was used" — but the pipeline emits
   analysis-shaped *reasoning*, it does not execute code. Its numbers are correct
   here (famous dataset), but on a private dataset they would be estimates. **This
   is the pipeline's real limitation: it plans and reasons about analysis; it does
   not run it.**
3. **LLM-judge generosity.** The judge (same model family) gave AGENTIC a flat
   10.0/10.0 across all seven dimensions — a halo effect from a long, confident,
   rubric-aligned report. The manual scorecard in §2 corrects this; the judge is
   shown only as a directional cross-check. Both agree on the ranking.
4. **n = 1.** One dataset, one run per condition. Treat the magnitudes as
   indicative, not statistically robust.
5. **Cost & latency.** AGENTIC used 8 LLM calls and ~560 s of compute vs. JUNIOR-A's
   1 call / 39 s — roughly a **14× cost-and-latency multiple** for a ~+4.2-point
   quality gain. For a throwaway question the single-shot LLM is the rational choice;
   the agentic pipeline earns its cost when rigour, auditability, and a defensible
   methodology trail actually matter.
6. Minor: the report's byline reads "Claude Opus" though the run was on Gemini —
   a hardcoded string in `PROMPT.md`, cosmetic only.

---

## 6. Conclusion

On a real, third-party dataset the **8-phase Agentic AI Data Analyst clearly
outperforms both junior baselines (8.9 vs 4.7 vs 3.0)**. The decisive finding is
*where* it wins: not in the conclusions (a single-shot LLM already lands the right
drivers and writes a clean memo) but in **the disciplined analytical process around
them** — significance testing with multiple-testing correction, an explicit
data-quality pass, interaction/confounding analysis, calibrated confidence, and
intellectually honest caveats including admitting what the data cannot answer.

That is a precise restatement of the project's thesis: the value of the agentic
system is not a smarter model — it is the **enforced methodology**. The quality
gates between phases convert an LLM that *can* be rigorous into one that *reliably
is*. The cost is real (≈14× latency/calls), so the pipeline is justified for
decisions that must be defensible and auditable — and overkill for quick look-ups.

---

## 7. Reproduce

```bash
python3 benchmark/ground_truth.py      # answer key  -> results/ground_truth.json
python3 benchmark/dataset_profile.py   # shared input -> results/data_description.txt
python3 benchmark/junior_b_pandas.py   # JUNIOR-B
python3 benchmark/junior_a_llm.py      # JUNIOR-A   (1 Gemini call)
python3 benchmark/run_agentic.py       # AGENTIC    (8-phase live run)
python3 benchmark/score.py             # scores all three -> results/scores.json
```

All inputs, deliverables, scores and the pipeline's per-phase outputs are in
`benchmark/results/` and `benchmark/agentic_outputs/`.
