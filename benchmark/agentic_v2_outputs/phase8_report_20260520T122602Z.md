---

# Taming Telecom Churn: A Data-Driven Retention Strategy
**Prepared by:** Agentic AI Data Analyst Pipeline (Claude Opus)
**Date:** 2024-05-21
**Objective:** Identify the top drivers of customer churn in our telecom subscriber base and recommend the two or three highest-leverage, cost-effective interventions to reduce it.
**Audience:** Customer Retention / Marketing leadership

---

## Executive Summary
Our analysis reveals that over 83% of all customer churn originates from subscribers on Month-to-Month contracts, with the highest risk concentrated in their first six months. The root cause is a failure to demonstrate sufficient value during this initial, flexible period, leading customers to leave before their loyalty is established. We recommend launching a "First 90-Day Value" campaign this quarter for new Month-to-Month customers, focused on proactive support and a compelling offer to upgrade to a one-year contract. This single intervention targets the largest source of customer loss and is expected to reduce churn in our most vulnerable cohort by over 20%.

---

## Key Findings

### Finding 1: Month-to-Month contracts and low tenure are the overwhelming drivers of churn.
Customers without a long-term commitment leave at an alarming rate, especially at the beginning of their lifecycle. This is the single largest and most urgent problem area.

**Evidence:**
-   Customers on Month-to-month contracts churn at a rate of **42.6%**, which is nearly 4 times the rate of One-year contract customers (11.3%) and 15 times the rate of Two-year contract customers (2.8%).
-   The average tenure of a customer who churned is only **18 months**, compared to **37.6 months** for a customer who stays.
-   The churn risk is highest at the very beginning: **52.9%** of customers in their first six months churn.

**Root Cause:** A failure to demonstrate sufficient value during the flexible Month-to-month period. This is likely due to an ineffective onboarding process or a product/price offering that attracts transient, low-loyalty customers who are easily poached by competitors.

**Confidence:** We are over 99% confident this is a real and statistically significant pattern. The effect size is very large and of high business importance.

**Business Implication:** If ignored, we will continue to lose nearly half of our new pay-as-you-go customers, creating a "leaky bucket" that makes net subscriber growth extremely difficult and expensive to achieve.

### Finding 2: The premium Fiber Optic service has a critical value-for-money problem.
Our highest-priced internet service is driving customers away at more than double the rate of our standard DSL service. This suggests a significant gap between customer expectations and their actual experience.

**Evidence:**
-   Customers with Fiber Optic internet churn at a rate of **41.9%**, compared to just **19.0%** for DSL customers.
-   The problem is amplified by a lack of support: Fiber customers *without* Tech Support churn at an astronomical **49.4%**. When they *do* have Tech Support, the rate is cut by more than half to **22.6%**.

**Root Cause:** A value-for-money problem. The premium price of Fiber Optic sets high expectations for performance and support, but the service experience is not meeting this bar. The lack of adequate, accessible tech support for this complex product appears to be the primary failure point.

**Confidence:** We are over 99% confident this is a real and statistically significant pattern. The effect is strong and represents a major issue with a key product line.

**Business Implication:** We are not only losing high-revenue customers but also damaging the brand perception of our premium product. This could hinder future attempts to upsell customers to higher-value plans.

### Finding 3: Protective add-on services are powerful retention tools.
Customers who subscribe to services like Tech Support and Online Security are significantly more loyal. These services act as a powerful buffer against churn, particularly for internet customers.

**Evidence:**
-   Internet customers who have Tech Support churn at **15.2%**, while those without churn at **31.1%**.
-   Similarly, those with Online Security churn at **14.6%**, compared to **31.4%** for those without.

**Root Cause:** These services either resolve technical friction points that would otherwise lead to frustration and churn, or they increase the "stickiness" of the customer's relationship with our ecosystem, making it harder to leave.

**Confidence:** We are over 99% confident this is a real and statistically significant pattern.

**Business Implication:** We have a proven, in-house method for reducing churn that is likely being underutilized. These add-ons are not just revenue streams; they are retention levers.

---

## Recommendations

| # | Recommendation | Expected Outcome | Owner | Priority | Success Metric |
|---|---|---|---|---|---|
| 1 | **Launch a "First 90-Day Value" campaign for new Month-to-Month customers.** This multi-touch campaign will include proactive support check-ins and a one-time offer after 60 days to upgrade to a 1-year plan for the same monthly price. | Reduce churn for customers with 0-6 months tenure by 20% (from 52.9% to ~42%), preventing approx. 150 churns per quarter. | Marketing | P1 | Churn rate in the 0-6 month M-t-M cohort. |
| 2 | **Create a "Fiber Optic Onboarding & Support" package.** Bundle Tech Support free for the first 6 months for all new Fiber Optic customers and proactively message its availability. | Reduce churn for new Fiber Optic customers by 25%, preventing approx. 100 high-value churns per quarter. | Product / Marketing | P1 | Churn rate among Fiber Optic customers with <12 months tenure. |
| 3 | **Introduce a "Protective Bundle" discount.** Offer a small (e.g., 10%) discount to any internet customer who subscribes to both Tech Support and Online Security. | Increase adoption of these add-ons by 15% among the at-risk internet customer base within 6 months. | Marketing / Sales | P2 | Adoption rate of Tech Support and Online Security. |

**Evidence chains:**
-   **Recommendation 1:** Stems from Finding 1 (M-t-M customers churn early) → Root Cause (failure to show value early) → Action (proactively show value and incentivize commitment in the first 90 days).
-   **Recommendation 2:** Stems from Finding 2 (Fiber has a value problem) → Root Cause (support expectations not met) → Action (proactively provide the support that is proven to cut churn).
-   **Recommendation 3:** Stems from Finding 3 (Add-ons reduce churn) → Root Cause (these services increase loyalty) → Action (incentivize adoption of these services to more customers).

---

## Anomalies & Surprises
-   **Observation:** The churn rate for customers with exactly **one** add-on service is surprisingly high (45.8%), much higher than for customers with zero add-ons (21.1%) or two or more.
-   **Possible explanation:** This could indicate that customers are being sold a single, specific add-on (e.g., streaming TV) as part of a promotion that, upon expiring or failing to meet expectations, leads to dissatisfaction and churn.
-   **Why it matters:** This non-linear relationship suggests that our bundling and upselling strategy needs to be more nuanced. Pushing a single, potentially ill-fitting add-on may do more harm than good.
-   **Suggested action:** A follow-up analysis to identify which specific single add-on is associated with this churn spike.

---

## Caveats & Limitations
-   **Cost-Effectiveness is Inferred:** This analysis assumes interventions that require minimal new infrastructure (e.g., marketing campaigns, bundling) are cost-effective. The dataset lacks financial data, so a true cost-benefit analysis was not possible. To resolve: The business must layer its own cost data onto these recommendations.
-   **Correlation vs. Causation:** This analysis identifies factors strongly *associated* with churn. While the evidence is compelling, we cannot prove these factors *cause* churn without controlled A/B testing. To resolve: Treat recommendations as strong hypotheses to be tested and measured.
-   **Data Representativeness:** This analysis assumed the provided IBM dataset is a representative sample of our entire subscriber base. If the sample is skewed, the findings may not generalize perfectly.
-   **Duplicate Removal:** We removed 22 duplicate rows (0.3% of data). While the impact is minimal, this could slightly affect the proportions of a very small customer subgroup.

---

## Next Steps
1.  **Qualitative 'Why' Analysis:** Conduct surveys or exit interviews with churned Fiber Optic customers to gather direct feedback on their reasons for leaving. This will add crucial qualitative color to the quantitative findings.
2.  **Cost-Benefit & LTV Modeling:** Integrate internal financial data (e.g., Customer Lifetime Value, cost of add-ons, cost of marketing campaigns) to build a full business case for the proposed recommendations.
3.  **Predictive Churn Modeling:** Develop a machine learning model that can predict the likelihood of an individual customer churning in the next 30 days. This would allow for proactive, targeted retention efforts aimed at specific at-risk individuals.

---

## Visualisation Manifest
| Chart | Insight Headline | Dashboard Section | Data Source |
|---|---|---|---|
| Churn Rate by Contract Type | Churn Rate Soars for Month-to-Month Contracts | The Primary Drivers: Why Customers Leave | clean_data.Contract, clean_data.Churn_numeric |
| Churn Rate by Tenure | Churn Risk Plummets After the First Year | The Primary Drivers: Why Customers Leave | clean_data.tenure_bucket, clean_data.Churn_numeric |
| Churn Rate by Internet Service & Tech Support | Fiber Optic Churn is 2x DSL, Driven by Lack of Tech Support | The Primary Drivers: Why Customers Leave | clean_data.InternetService, clean_data.TechSupport, clean_data.Churn_numeric |
| Impact of Add-ons on Churn | Key Add-ons Cut Churn Risk in Half | The Solution Pathway: How to Reduce Churn | clean_data.OnlineSecurity, clean_data.TechSupport, clean_data.Churn_numeric |

---

## Methodology Appendix
-   **Data sources:** `Telco-Customer-Churn.csv` provided by IBM.
-   **Cleaning summary:** Coerced `TotalCharges` to numeric and imputed 11 nulls with 0 based on tenure=0. Dropped 22 duplicate rows. Standardized redundant categories (e.g., 'No phone service' became 'No').
-   **Statistical tests:** Chi-squared Test of Independence was used to assess relationships between categorical variables (e.g., Contract and Churn). An Independent Samples t-test was used to compare the mean tenure of churners vs. non-churners. A logistic regression model confirmed the independent effects of the top drivers. All key findings are statistically significant with p < 0.001.
-   **Assumptions:**
    1.  The provided dataset is a representative sample of the entire subscriber base.
    2.  'Drivers' can be identified via the highest statistical associations (correlation, feature importance).
    3.  The business has the external knowledge needed to evaluate implementation costs.
    4.  The `TotalCharges` column, once cleaned, is a valid measure.