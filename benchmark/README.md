# Benchmark — Junior Data Analyst vs. Agentic AI Data Analyst

A 3-way benchmark on a **real public dataset** (IBM Telco Customer Churn, 7,043
customers), comparing the 8-phase Agentic pipeline against two junior-analyst
baselines, scored against a `pandas`/`scipy` answer key.

**➡ Read [`BENCHMARK_REPORT.md`](BENCHMARK_REPORT.md) for the full results.**

Headline: **AGENTIC 8.9 / 10** · JUNIOR-A (single-shot LLM) 4.7 · JUNIOR-B (naive
pandas) 3.0. The agentic win is concentrated in *analytical process* — statistical
rigour, data-quality handling, confounding analysis, honest caveats.

## Files

| Path | What |
|---|---|
| `data/Telco-Customer-Churn.csv` | The real dataset (downloaded from GitHub) |
| `ground_truth.py` | Computes the statistical answer key |
| `dataset_profile.py` | Builds the shared, answer-free input description |
| `junior_b_pandas.py` | JUNIOR-B baseline — naive pandas EDA |
| `junior_a_llm.py` | JUNIOR-A baseline — single Gemini call |
| `run_agentic.py` | AGENTIC condition — full 8-phase pipeline |
| `score.py` | Deterministic scan + LLM-as-judge scoring |
| `results/` | All inputs, deliverables, scores |
| `agentic_outputs/`, `agentic_logs/` | The pipeline's per-phase JSON + state log |

## Reproduce

```bash
pip install -r ../requirements.txt pandas scipy   # scipy/pandas are benchmark-only
python3 ground_truth.py && python3 dataset_profile.py
python3 junior_b_pandas.py && python3 junior_a_llm.py && python3 run_agentic.py
python3 score.py
```

Requires `GEMINI_API_KEY` in `../.env` for the two LLM conditions.
