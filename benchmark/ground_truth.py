"""Ground-truth statistical analysis of the Telco Customer Churn dataset.

This is the *answer key* for the benchmark. It runs a rigorous pandas/scipy
analysis directly on the real data — the kind of analysis a competent senior
analyst would do — so we can score what JUNIOR-A, JUNIOR-B and the AGENTIC
pipeline each produce against an objective truth.

Output: benchmark/results/ground_truth.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA = Path(__file__).resolve().parent / "data" / "Telco-Customer-Churn.csv"
OUT = Path(__file__).resolve().parent / "results" / "ground_truth.json"

CATEGORICALS = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]
NUMERICS = ["tenure", "MonthlyCharges", "TotalCharges"]


def cramers_v(confusion: np.ndarray) -> float:
    """Bias-corrected Cramer's V effect size for a contingency table."""
    chi2 = stats.chi2_contingency(confusion)[0]
    n = confusion.sum()
    phi2 = chi2 / n
    r, k = confusion.shape
    phi2corr = max(0.0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rcorr = r - (r - 1) ** 2 / (n - 1)
    kcorr = k - (k - 1) ** 2 / (n - 1)
    denom = min(kcorr - 1, rcorr - 1)
    return float(np.sqrt(phi2corr / denom)) if denom > 0 else 0.0


def cohens_d(a: pd.Series, b: pd.Series) -> float:
    """Cohen's d for the difference in means of two groups."""
    na, nb = len(a), len(b)
    pooled = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2) / (na + nb - 2))
    return float((a.mean() - b.mean()) / pooled) if pooled else 0.0


def effect_label(v: float) -> str:
    """Cohen's qualitative bands for Cramer's V (roughly)."""
    if v < 0.10:
        return "negligible"
    if v < 0.20:
        return "small"
    if v < 0.35:
        return "medium"
    return "large"


def main() -> None:
    df = pd.read_csv(DATA)
    n_rows = len(df)

    # --- Data quality: TotalCharges is object-typed; blank strings for tenure=0
    raw_total = df["TotalCharges"]
    blank_mask = raw_total.astype(str).str.strip() == ""
    n_blank_total = int(blank_mask.sum())
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce")
    coerced_nulls = int(df["TotalCharges"].isna().sum())
    # Confirm the quirk: every blank TotalCharges row has tenure == 0
    blank_all_tenure0 = bool((df.loc[blank_mask, "tenure"] == 0).all()) if n_blank_total else None

    dq = {
        "n_rows": n_rows,
        "n_cols": df.shape[1],
        "duplicate_customerID": int(df["customerID"].duplicated().sum()),
        "explicit_nulls_by_col": {c: int(df[c].isna().sum()) for c in df.columns if df[c].isna().sum() > 0},
        "TotalCharges_blank_strings": n_blank_total,
        "TotalCharges_blanks_all_have_tenure_0": blank_all_tenure0,
        "TotalCharges_stored_as": "object/string (needs coercion to numeric)",
        "SeniorCitizen_encoded_as": "int 0/1 (not Yes/No like other binaries)",
    }

    churn = (df["Churn"] == "Yes")
    overall_rate = float(churn.mean())

    # --- Categorical drivers: churn rate per level + chi-square + Cramer's V
    cat_results = []
    for col in CATEGORICALS:
        ct = pd.crosstab(df[col], df["Churn"])
        chi2, p, dof, _ = stats.chi2_contingency(ct)
        v = cramers_v(ct.values)
        rates = (df.groupby(col)["Churn"].apply(lambda s: (s == "Yes").mean())).sort_values(ascending=False)
        levels = {str(k): round(float(val), 4) for k, val in rates.items()}
        spread = float(rates.max() - rates.min())
        cat_results.append({
            "variable": col,
            "chi2": round(float(chi2), 2),
            "p_value": float(p),
            "cramers_v": round(v, 4),
            "effect_size": effect_label(v),
            "churn_rate_by_level": levels,
            "max_min_spread": round(spread, 4),
            "highest_risk_level": str(rates.index[0]),
            "highest_risk_rate": round(float(rates.iloc[0]), 4),
        })
    cat_results.sort(key=lambda r: r["cramers_v"], reverse=True)

    # --- Numeric drivers: group means + Welch t-test + Cohen's d + point-biserial
    num_results = []
    for col in NUMERICS:
        churned = df.loc[churn, col].dropna()
        stayed = df.loc[~churn, col].dropna()
        t, p = stats.ttest_ind(churned, stayed, equal_var=False)
        d = cohens_d(churned, stayed)
        valid = df[[col, "Churn"]].dropna()
        rpb, rpb_p = stats.pointbiserialr((valid["Churn"] == "Yes").astype(int), valid[col])
        num_results.append({
            "variable": col,
            "mean_churned": round(float(churned.mean()), 2),
            "mean_retained": round(float(stayed.mean()), 2),
            "welch_t": round(float(t), 2),
            "p_value": float(p),
            "cohens_d": round(float(d), 4),
            "point_biserial_r": round(float(rpb), 4),
            "direction": "higher value -> more churn" if rpb > 0 else "higher value -> less churn",
        })
    num_results.sort(key=lambda r: abs(r["cohens_d"]), reverse=True)

    # --- Tenure bands (the single strongest retention signal)
    bands = pd.cut(df["tenure"], [-1, 6, 12, 24, 48, 72],
                   labels=["0-6", "7-12", "13-24", "25-48", "49-72"])
    tenure_band_rate = {str(k): round(float(v), 4)
                        for k, v in df.groupby(bands, observed=True)["Churn"]
                        .apply(lambda s: (s == "Yes").mean()).items()}

    # --- Ranked driver list (the headline answer key)
    ranked = []
    for r in cat_results:
        ranked.append({"driver": r["variable"], "type": "categorical",
                       "effect_size_metric": "cramers_v", "effect_size": r["cramers_v"],
                       "strength": r["effect_size"]})
    for r in num_results:
        v = abs(r["cohens_d"])
        strength = "large" if v >= 0.8 else "medium" if v >= 0.5 else "small" if v >= 0.2 else "negligible"
        ranked.append({"driver": r["variable"], "type": "numeric",
                       "effect_size_metric": "cohens_d", "effect_size": v, "strength": strength})
    ranked.sort(key=lambda r: r["effect_size"], reverse=True)

    result = {
        "dataset": "IBM Telco Customer Churn",
        "source": "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv",
        "business_question": "What are the top drivers of customer churn, and which "
                             "interventions would most reduce it?",
        "data_quality": dq,
        "overall_churn_rate": round(overall_rate, 4),
        "churn_count": int(churn.sum()),
        "class_balance": {"Yes": int(churn.sum()), "No": int((~churn).sum())},
        "ranked_drivers": ranked,
        "top_drivers_summary": [r["driver"] for r in ranked[:8]],
        "categorical_analysis": cat_results,
        "numeric_analysis": num_results,
        "tenure_band_churn_rate": tenure_band_rate,
        "key_facts_for_scoring": [
            f"Overall churn rate is {overall_rate:.1%}.",
            f"Contract type is the single strongest categorical driver "
            f"(Cramer's V={cat_results[0]['cramers_v'] if cat_results[0]['variable']=='Contract' else next(r['cramers_v'] for r in cat_results if r['variable']=='Contract')}).",
            "Month-to-month contracts churn at ~43%; two-year contracts at ~3%.",
            "Tenure is the strongest numeric driver — short-tenure customers churn far more "
            f"(0-6 months: {tenure_band_rate.get('0-6')}).",
            "Fiber-optic internet customers churn much more than DSL or no-internet.",
            "Electronic-check payment has the highest churn of any payment method.",
            "Lack of OnlineSecurity and TechSupport are strongly associated with churn.",
            f"TotalCharges has {n_blank_total} blank-string values (all tenure=0 new customers) "
            "and is stored as text — a real data-quality trap.",
            "gender has negligible effect on churn and is a distractor variable.",
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2))
    print(f"Wrote {OUT}")
    print(f"\nOverall churn rate: {overall_rate:.2%}  ({churn.sum()}/{n_rows})")
    print(f"TotalCharges blank strings: {n_blank_total} (all tenure=0: {blank_all_tenure0})")
    print("\nTop 8 drivers by effect size:")
    for r in ranked[:8]:
        print(f"  {r['driver']:18s} {r['effect_size_metric']}={r['effect_size']:.3f}  ({r['strength']})")


if __name__ == "__main__":
    main()
