"""Generate the SHARED dataset description handed to every analyst.

Fairness rule: this description contains only *univariate* profiling — the
kind of `df.info()` / `df.describe()` / `value_counts()` output any analyst
(junior included) produces in the first five minutes. It deliberately does
NOT contain any churn-by-segment breakdown, chi-square result, or effect
size — those are the analysis, i.e. the thing being benchmarked.

Output: benchmark/results/data_description.txt   (the shared input string)
        benchmark/results/profile.json            (structured, for scripts)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data" / "Telco-Customer-Churn.csv"
RESULTS = Path(__file__).resolve().parent / "results"

BUSINESS_QUESTION = (
    "What are the top drivers of customer churn in our telecom subscriber base, "
    "and which two or three interventions would most cost-effectively reduce it?"
)
STAKEHOLDER = "Customer Retention / Marketing leadership (medium technical tolerance)"


def build() -> tuple[str, dict]:
    df = pd.read_csv(DATA)
    n = len(df)
    overall_churn = float((df["Churn"] == "Yes").mean())

    lines = [
        "DATASET: IBM Telco Customer Churn (real, public dataset).",
        "SOURCE: github.com/IBM/telco-customer-churn-on-icp4d  (Telco-Customer-Churn.csv)",
        f"SHAPE: {n} rows x {df.shape[1]} columns. One row per telecom customer.",
        f"TARGET: 'Churn' (Yes/No) — overall churn rate in the file is {overall_churn:.1%}.",
        "",
        "COLUMN DICTIONARY (univariate profile only — raw CSV dtypes):",
    ]

    profile_cols = []
    for col in df.columns:
        s = df[col]
        raw_dtype = str(s.dtype)
        nulls = int(s.isna().sum())
        nunique = int(s.nunique(dropna=True))
        entry = {"name": col, "raw_dtype": raw_dtype, "explicit_nulls": nulls,
                 "distinct": nunique}
        if raw_dtype == "object":
            vc = s.value_counts(dropna=False)
            if nunique <= 8:
                vals = ", ".join(f"{k!r}:{v}" for k, v in vc.items())
                desc = f"categorical [{nunique}]: {vals}"
            else:
                desc = f"high-cardinality text [{nunique} distinct] (e.g. identifier)"
            entry["sample_values"] = [str(k) for k in vc.index[:8]]
        else:
            desc = (f"numeric: min={s.min()}, max={s.max()}, "
                    f"mean={s.mean():.2f}, median={s.median()}")
            entry.update({"min": float(s.min()), "max": float(s.max()),
                          "mean": float(s.mean())})
        entry["description"] = desc
        profile_cols.append(entry)
        lines.append(f"  - {col} ({raw_dtype}, nulls={nulls}): {desc}")

    lines += [
        "",
        "NOTES KNOWN AT HANDOFF (from basic profiling, no analysis done yet):",
        "  - 'SeniorCitizen' is encoded as integer 0/1, unlike the other Yes/No binaries.",
        "  - 'TotalCharges' is stored as a TEXT column in the raw CSV, not numeric — "
        "it must be coerced before any numeric work.",
        "  - 'customerID' is a unique identifier and is not an analytical feature.",
        "  - No analysis of what drives churn has been done yet. That is the task.",
        "",
        f"BUSINESS QUESTION: {BUSINESS_QUESTION}",
        f"STAKEHOLDER: {STAKEHOLDER}",
        "CONSTRAINTS: Python + pandas available; dataset fits in memory; no PII "
        "beyond the opaque customerID; deliver within one analysis cycle.",
    ]

    description = "\n".join(lines)
    profile = {
        "dataset": "IBM Telco Customer Churn",
        "n_rows": n,
        "n_cols": df.shape[1],
        "overall_churn_rate": overall_churn,
        "business_question": BUSINESS_QUESTION,
        "stakeholder": STAKEHOLDER,
        "columns": profile_cols,
    }
    return description, profile


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    description, profile = build()
    (RESULTS / "data_description.txt").write_text(description)
    (RESULTS / "profile.json").write_text(json.dumps(profile, indent=2))
    print(f"Wrote {RESULTS / 'data_description.txt'} ({len(description)} chars)")
    print(f"Wrote {RESULTS / 'profile.json'}")
    print("\n" + "=" * 70)
    print(description)


if __name__ == "__main__":
    main()
