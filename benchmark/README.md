# Benchmark — Junior Data Analyst vs. Agentic AI Data Analyst

A 5-way benchmark on a **real public dataset** (IBM Telco Customer Churn, 7,043
customers), comparing three generations of the Agentic pipeline against two
junior-analyst baselines, scored against a `pandas`/`scipy` answer key.

**➡ Read [`BENCHMARK_REPORT.md`](BENCHMARK_REPORT.md) for the full results.**

Headline (calibrated manual scores, 0–10): **AGENTIC-v3 (11-phase + code
execution) 9.7** · AGENTIC-v2 (8-phase + code execution) 8.6 · AGENTIC-v1
(8-phase, reasoning only) 8.1 · JUNIOR-A (single-shot LLM) 4.7 · JUNIOR-B
(naive pandas) 3.0.

The v1→v2 gain is epistemic — numbers become **computed facts with an
executed-code audit trail** instead of recalled claims. The v2→v3 gain is
judgment — the **Phase 6.5 red-team reviewer twice blocked the analysis on real
statistical errors** (a multicollinearity-inverted driver ranking; a marginal
p = 0.032 finding that fails multiple-testing correction presented as
confirmed) before letting a corrected, honestly-labelled report ship, and
Phase 9 closed the loop with drift alerts and a knowledge-base entry.

## Files

| Path | What |
|---|---|
| `data/Telco-Customer-Churn.csv` | The real dataset (downloaded from GitHub) |
| `ground_truth.py` | Computes the statistical answer key |
| `dataset_profile.py` | Builds the shared, answer-free input description |
| `junior_b_pandas.py` | JUNIOR-B baseline — naive pandas EDA |
| `junior_a_llm.py` | JUNIOR-A baseline — single Gemini call |
| `run_agentic.py` | AGENTIC-v1 — 8-phase pipeline, reasoning only |
| `run_agentic_v2.py` | AGENTIC-v2 — 8-phase pipeline + real code execution |
| `run_agentic_v3.py` | AGENTIC-v3 — 11-phase pipeline + real code execution |
| `resume_agentic_v3.py` | Resume a v3 run after a Phase 6.5 red-team BLOCK |
| `score.py` / `score_v2.py` / `score_v3.py` | Deterministic scan + numbers verification + LLM-as-judge (+ v3 process audit) |
| `run_stress.py`, `stress_scenario.py` | Part C stress-test harness (see `stress_results/SCORECARD.md`) |
| `results/` | All inputs, deliverables, scores, transcripts, knowledge base |
| `agentic*_outputs/`, `agentic*_logs/` | Per-phase JSON + append-only state logs per condition |

## Reproduce

```bash
pip install -r ../requirements.txt pandas scipy   # scipy/pandas are benchmark-only
python3 ground_truth.py && python3 dataset_profile.py
python3 junior_b_pandas.py && python3 junior_a_llm.py
python3 run_agentic.py && python3 run_agentic_v2.py && python3 run_agentic_v3.py
python3 score.py && python3 score_v2.py && python3 score_v3.py
```

Requires `GEMINI_API_KEY` in `../.env` for the LLM conditions. If the v3
red-team reviewer BLOCKs (expected — it is doing its job), copy its required
revisions from the newest `agentic_v3_logs/pipeline_state_*.json` into
`resume_agentic_v3.py` and run that to resume from the phase the revisions touch.
