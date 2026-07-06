# Part C Stress-Test Scorecard — Baseline (8-phase) vs v3 (11-phase)

**Scenario:** VP-Growth-vs-CFO Enterprise churn question (see `benchmark/stress_scenario.py`),
run 2026-07-06. Baseline ran the unmodified 8-phase pipeline from commit `e1caa09`
(git-worktree snapshot, so later prompt edits could not leak in); v3 ran the
11-phase pipeline (Phase 0 triage, provenance split, confound sweep, Phase 6.5
red team, Phase 9 monitoring). Same scenario inputs verbatim, same model
(gemini-2.5-pro), no dataset file — warehouse described in prose only.

| Run | Phases | Outcome | Wall clock |
|---|---|---|---|
| baseline | 1–8 | COMPLETE, report delivered | 395 s |
| v3 | 0–9 (incl. 6.5) | COMPLETE, report + monitoring + KB entry | 705 s |

Artifacts: `baseline/` and `v3/` subdirectories (per-phase JSON, pipeline state
log, final report; v3 also `knowledge_base/entries.jsonl`).

---

## Trap table results

| # | Injected trap | Should be caught by | Baseline | v3 |
|---|---|---|---|---|
| 1 | Two conflicting stakeholder hypotheses stated as if not in conflict | Phase 0 Task 3 | **PARTIAL** — decomposed both framings into SQ2/SQ3/SQ4 and the report resolves both, but the conflict itself was never surfaced as a conflict; no explicit "VP says X, CFO says Y, we will adjudicate with data" | **PASS** — Phase 0 surfaced it explicitly ("VP: Enterprise churn problem vs CFO: pricing + mix shift"), added it as sub-questions; Phase 6 insight #3 explicitly adjudicates: "The CFO's hypothesis that mix shift was a primary driver is disproven" (H4 tested and REJECTED) |
| 2 | Known events (Apr 1 price increase, Mar 28 reseller exit) stated in the prompt | Phase 0 Task 2 | **PARTIAL** — Phase 1 built sub-questions from both events (they were in the objective), but there is no confound-calendar artifact and no requirement that every finding be checked against the events | **PASS** — Phase 0 produced a 4-event confound calendar (price increase, reseller exit, billing migration, seasonality); every Phase 4 hypothesis carries a `known_event_check`; Phase 6's sweep weighed each event per finding and classified H1 as EVENT_DRIVEN |
| 3 | "By Friday" time pressure | Phase 0 Task 1/4 | **FAIL** — zero mentions of the deadline in any of the 8 phase outputs or the report; scope silently promised in full | **PASS (minor gap)** — Phase 0 judged the deadline FEASIBLE_WITH_DESCOPING with a concrete plan (descriptive "what happened" by Friday; causal work deferred); Phase 1's success definition carries "by Friday". Gap: the final report does not label itself as the descoped deliverable |
| 4 | Migration-era NULL semantics (billing NULLs = old system, not missing) | Phase 3 | **PASS** — Phase 3 flagged mrr anomalies as CRITICAL; caveat about migration-era data loss in the report | **PASS (stronger)** — Phase 3 explicitly diagnosed MNAR ("mrr systematically NULL for all pre-migration data"), prescribed logo churn as the primary metric, and the gotcha is preserved in the Phase 9 knowledge-base entry |
| 5 | Enterprise churn "up" actually explained by reseller cohort removal (mix shift, not organic) | Phase 4/6 confound sweep | **PASS** — identified the reseller cohort as 75% of churn and separated one-off from organic | **PASS** — same separation (reseller = 40% of the spike, event-driven) plus formal H4 mix-shift test (REJECTED) and post-sweep verdict labels (EVENT_DRIVEN vs ORGANIC) |
| 6 | No support-ticket table exists | Phase 2 | **PARTIAL** — Phase 1 descoped it correctly and nothing was fabricated, but the final report never mentions support tickets: the stakeholder's explicit question is silently dropped | **PASS** — Phase 0 flagged NEEDS_DATA_ENGINEER; report Caveats state "could not be fulfilled… remains an unknown factor" and Next Steps propose the ingestion project |
| 7 | Price-elasticity implied by CFO framing | Phase 0/1 scope check | **PARTIAL** — Next Steps propose a "pricing elasticity study", but no explicit descope or specialist referral; the report's causal claims about the price increase go beyond analyst-level support | **PASS** — Phase 0: NEEDS_DATA_SCIENTIST referral with the analyst-level partial answer ("before/after churn comparison is answerable; elasticity is not"); report's Next Steps commission a DiD analysis "led by a data scientist" |
| 8 | DATA_DERIVED hypothesis formed during EDA | Phase 4/5 provenance | **FAIL** — H3 (EMERGENT tenure hypothesis) tested on the same data and reported at HIGH confidence with "statistically significant", indistinguishable from pre-registered tests | **PASS** — H5 (EMERGENT Pro-tier churn) labelled DATA_DERIVED → graded EXPLORATORY by Phase 5 → report Caveats: "discovered and tested on the same data… requires validation on future data" |
| 9 | Does the report survive adversarial review | Phase 6.5 | **N/A (phase absent)** — fabricated statistics and a causal overclaim ("price increase caused a 14pp lift") shipped unchallenged | **PASS** — red team returned PROCEED_WITH_REVISIONS: killed the causal price-hike claim (root cause CONFIRMED → HYPOTHESISED), forced causal→correlational wording, downgraded the $10.85M estimate MEDIUM → LOW, and Phase 8 verifiably applied all of it ("strongly associated with", "Hypothesised value gap", "Our confidence in the financial impact estimate is low") |
| 10 | Does anything track whether the fix worked | Phase 9 | **PARTIAL** — recommendations table has a "Success Metric" column, but no thresholds wired to alerting, no check-in dates, no institutional memory | **PASS** — success metric with threshold (<6.0%) and concrete check-in date (2027-01-15) and owner; two implementable drift alerts (metric + threshold + tool); knowledge-base entry with 4 gotchas persisted to `entries.jsonl` and recallable by Phase 0 |

**Trap score: baseline 2 PASS / 5 PARTIAL / 2 FAIL / 1 N/A → v3 10 PASS (1 with a minor labelling gap).**

---

## The failure both runs share (and why it matters most)

**Every number in both reports is fabricated.** There is no dataset — the
scenario describes a warehouse in prose — yet both pipelines produced exact
figures (baseline: "75% of churned customers", "22% vs 8%", "$6.3M ARR",
p=0.0; v3: "12.5% vs 4.5%", "3,750 customers", "$10.85M MRR", p=0.0) and
describe chi-squared/z-tests "at 95% confidence" as if they were executed.
Neither report discloses that no query was ever run.

v3's red team caught the *inferential* overclaims (causality, confidence
labels) but not the *existential* one — that the numbers themselves have no
computation trace. This is exactly the ceiling Part E step 4 predicts: no
prompt change fixes dimensions 3 and 6 fully; only mandatory code execution
(or a hard "no dataset ⇒ label every figure ILLUSTRATIVE / return
REQUIRES_ACCESS at Phase 2") can. The repo already has the execution harness
(`--dataset-path` activates compute-then-synthesise for Phases 3–6 and the
red team); the remaining work is refusing to emit unlabelled numbers when it
is *not* active.

---

## Part D dual-bar rubric

Scoring: ✗ fails the bar, ~ partially clears it, ✓ clears it.

| # | Dimension | Baseline Bar 1 | Baseline Bar 2 | v3 Bar 1 | v3 Bar 2 | Evidence |
|---|---|---|---|---|---|---|
| 1 | Confound checking | ✓ | ✗ | ✓ | ~ | v3 sweeps every finding and classifies verdicts (ORGANIC/EVENT_DRIVEN), documents unsweepable dimensions; but breadth was schema-limited and the red team itself flagged tenure/channel gaps |
| 2 | Known-event awareness | ~ (events were handed to it in the prompt) | ✗ | ✓ | ✓ | v3 checks events proactively, per-hypothesis and per-finding, plus asks calendar questions for events *not* volunteered |
| 3 | Statistical honesty | ~ | ✗ | ~ | ✗ | v3 adds provenance/evidence grades and MTC — but both fabricate numbers without a computation trace (see above) |
| 4 | Scope judgment | ✗ | ✗ | ✓ | ~ | v3 triages, negotiates the Friday deadline with an explicit descope, refers elasticity out; report doesn't self-label as the descoped deliverable |
| 5 | Self-review | ✗ | ✗ | ✓ | ✓ | v3's independent pass caught a real error (causal overclaim) and its revisions demonstrably changed the report; anti-rubber-stamp gate prevents PROCEED-with-findings |
| 6 | Reproducibility | ✗ | ✗ | ~ | ✗ | v3 documents queries/steps and gotchas, but no executed computation backs the numbers in this scenario (harness exists; needs a dataset) |
| 7 | Follow-through | ~ | ✗ | ✓ | ✓ | v3: thresholds, check-in dates, owners, implementable alert conditions |
| 8 | Institutional memory | ✗ | ✗ | ✓ | ✓ | v3 persisted a KB entry (migration artifact, conflated root causes, missing legacy MRR, plan-name mapping) recallable by Phase 0 |
| 9 | Stakeholder conflict handling | ~ | ✗ | ✓ | ✓ | v3 surfaced the conflict at intake and adjudicated it with a formal test (mix shift REJECTED) |
| 10 | Consistency under time pressure | ✗ | ✗ | ✓ | ✓ | v3 ran the free checks *and* renegotiated scope instead of silently thinning the analysis |

**Reading:** baseline clears Bar 1 on 3–5 dimensions and Bar 2 on none — and
its Bar-2 failures are precisely dimensions 1, 2, 5, 7, 8 (+4, 10), confirming
Part A's thesis that the missing phases, not prompt wording, were the
bottleneck. v3 clears Bar 2 on 6 of 10 dimensions outright and partially on
2 more. The two dimensions still failing Bar 2 (3: statistical honesty,
6: reproducibility) are the ones Part E step 4 assigns to the code-execution
infrastructure fix, not to prompts.

---

## Recommended next steps (in order)

1. **Close the fabrication hole** (dimensions 3 & 6): when no `dataset_path`
   is supplied, either (a) Phase 2 returns REQUIRES_ACCESS and the pipeline
   blocks pending real access, or (b) every numeric claim must carry an
   `ILLUSTRATIVE` label enforced by a gate + the Phase 6.5 red team
   ("any number lacking a computation trace" is already in its prompt — add
   a hard gate check so it cannot wave one through).
2. **Phase 8 descope banner**: if Phase 0 judged FEASIBLE_WITH_DESCOPING, the
   report must open with what this deliverable includes/excludes vs the
   original ask (fixes the one remaining trap-3 gap).
3. **Re-run this scenario with a real dataset** (the harness's
   compute-then-synthesise path) to measure dimensions 3/6 with executed
   numbers — the Telco benchmark data in `benchmark/data/` can be adapted.
