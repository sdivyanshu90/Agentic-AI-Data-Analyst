"""JUNIOR-B baseline: a naive junior-analyst pandas script.

This deliberately represents *rote EDA*: load the data, group-by churn rates,
rank by raw spread, eyeball the numbers, write a couple of generic
recommendations. It does NOT do significance testing, effect sizes,
confounding checks, or a real data-quality pass — that shallowness is the
point of the baseline.

Output: benchmark/results/junior_b_output.md
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data" / "Telco-Customer-Churn.csv"
OUT = Path(__file__).resolve().parent / "results" / "junior_b_output.md"

CATEGORICALS = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]
NUMERICS = ["tenure", "MonthlyCharges", "TotalCharges"]


def main() -> None:
    df = pd.read_csv(DATA)
    # Junior move: TotalCharges won't convert, just coerce and move on.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    out = ["# Churn Analysis — Junior Analyst (pandas EDA)", ""]
    out.append(f"Dataset: {len(df)} rows. Overall churn rate: "
               f"{(df['Churn'] == 'Yes').mean():.1%}.")
    out.append("")

    # Churn rate by each categorical, ranked by spread.
    out.append("## Churn rate by category")
    rows = []
    for col in CATEGORICALS:
        rates = df.groupby(col)["Churn"].apply(lambda s: (s == "Yes").mean())
        spread = rates.max() - rates.min()
        rows.append((col, spread, rates))
    rows.sort(key=lambda r: r[1], reverse=True)

    for col, spread, rates in rows:
        levels = ", ".join(f"{k}={v:.1%}" for k, v in rates.sort_values(ascending=False).items())
        out.append(f"- **{col}** (spread {spread:.1%}): {levels}")
    out.append("")

    # Numeric averages by churn group.
    out.append("## Numeric averages by churn group")
    for col in NUMERICS:
        g = df.groupby("Churn")[col].mean()
        out.append(f"- {col}: churned avg = {g.get('Yes', float('nan')):.1f}, "
                   f"retained avg = {g.get('No', float('nan')):.1f}")
    out.append("")

    # "Top drivers" = whatever has the biggest spread.
    out.append("## Top drivers (by churn-rate spread)")
    for col, spread, _ in rows[:5]:
        out.append(f"1. {col} — spread of {spread:.1%}")
    out.append("")

    # Generic recommendations.
    out.append("## Recommendations")
    out.append("- Target the high-churn segments above with retention offers / discounts.")
    out.append("- Focus on month-to-month customers since they churn the most.")
    out.append("- Improve onboarding for new customers (low tenure churns more).")
    out.append("")
    out.append("_Note: ranked purely by churn-rate spread; no significance "
               "testing or effect sizes computed._")

    text = "\n".join(out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"Wrote {OUT}")
    print("\n" + text)


if __name__ == "__main__":
    main()
