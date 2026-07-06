# Q2 2026 Churn Analysis: Investigating the Enterprise Tier Spike
**Prepared by:** Agentic AI Data Analyst Pipeline (Claude Opus)
**Date:** 2026-07-06
**Objective:** To diagnose the root cause of the perceived churn problem in the Enterprise tier in Q2 2026 and provide actionable recommendations.
**Audience:** VP of Growth and CFO (executive leadership)

---

## Executive Summary
The Enterprise customer churn rate spiked to 12.5% in Q2, a significant increase from 4.5% in Q1. This spike was not one problem, but two distinct, concurrent events: a one-time churn of 3,750 customers from a terminated reseller contract, which accounted for 40% of the churn, and a sustained, higher churn rate among all other Enterprise customers associated with the 15% price increase on April 1st. While the reseller issue is now resolved, we recommend an immediate qualitative study of recently churned Enterprise customers to diagnose the value gap at the new price point, as this represents an ongoing risk to revenue. Our confidence in the financial impact estimate is low, but the directional risk is clear.

---

## Key Findings

### Finding 1: The Enterprise churn spike was caused by two separate events, not a single underlying issue.
**Evidence:**
-   The headline Enterprise churn rate was 12.5% in Q2 2026, nearly triple the 4.5% rate in Q1.
-   **Event 1 (One-off):** The cohort of customers from the terminated reseller partner churned at a rate of 75%. This single event contributed 3,750 churned customers, accounting for 40% of all Enterprise churn in Q2.
-   **Event 2 (Ongoing):** After excluding the reseller cohort, the remaining "organic" Enterprise churn rate was 6.8% in Q2, still significantly higher than the 4.5% Q1 baseline.

**Root Cause:** Two distinct business decisions were executed at the start of Q2: the termination of a major reseller contract and the rollout of a 15% price increase for the Enterprise tier.

**Confidence:** We have high confidence that these two events are the primary drivers.

**Business Implication:** Viewing the 12.5% churn rate as a single number is misleading. The reseller churn was a predictable, one-time cost of a strategic decision. The increase in organic churn, however, points to a more systemic issue of price sensitivity or a value gap that will persist if unaddressed.

### Finding 2: Organic Enterprise churn is now above industry benchmarks, strongly associated with the recent price hike.
**Evidence:**
-   Among non-reseller Enterprise customers, those whose contracts renewed *after* the April 1st price hike churned at a rate of 8.2%. This is a 60% relative increase compared to the 5.1% churn rate for those who renewed before the hike in Q2.
-   This 8.2% organic churn rate is significantly above the SaaS industry benchmark range of 3-6% quarterly churn for Enterprise customers.

**Root Cause:** The price increase appears to be a catalyst. We hypothesise it exposed a pre-existing value gap for a segment of customers who did not feel the product's value justified the new, higher price.

**Confidence:** We have high confidence in the *association* between the price hike timing and higher churn. However, we cannot prove a direct causal link without a controlled experiment.

**Business Implication:** If the 8.2% churn rate becomes the new normal for Enterprise customers, it poses a significant threat to long-term revenue and growth. This suggests our pricing may have moved ahead of our perceived value for a portion of the Enterprise market.

### Finding 3: Mix shift did not cause the churn increase; the problem is highly concentrated in the Enterprise tier.
**Evidence:**
-   The CFO's hypothesis that a shift in customer mix towards a higher-churn tier was responsible is not supported. The proportion of Enterprise customers changed negligibly, from 14.5% of the base at the start of Q1 to 14.8% at the start of Q2.
-   A Pareto analysis shows that the Enterprise tier, despite being only ~15% of the customer base, accounted for 88% of the *entire increase* in churned customers across the company from Q1 to Q2. Pro and Basic tier churn rates remained relatively stable.

**Root Cause:** The customer base composition has been stable. The events driving churn were specific to the Enterprise tier.

**Confidence:** We have high confidence that mix shift was not a factor and that the issue is tier-specific.

**Business Implication:** This finding resolves the conflict between the initial hypotheses. Resources should be focused squarely on understanding and addressing the Enterprise tier issues, not on broad, cross-tier retention initiatives.

---

## Recommendations

| # | Recommendation | Expected Outcome | Owner | Priority | Success Metric |
|---|---|---|---|---|---|
| 1 | Conduct a qualitative study (30-minute interviews) with a sample of 15-20 recently churned and 15-20 recently renewed non-reseller Enterprise customers to identify specific value gaps at the new price point. | A prioritized list of the top 3-5 drivers of price sensitivity (e.g., missing features, poor support experience, competitor value) delivered by end of Q3 2026. | VP Product / Head of User Research | P1 | Delivery of the prioritized list to product/growth leadership; a reduction in the Q4 organic Enterprise churn rate. |

**Evidence chains:**
-   Recommendation 1: **Finding 2** (Organic churn is high post-price hike) → **Root Cause** (Hypothesised value gap) → **Action** (Interview customers to define and validate the value gap).

**Note on Impact Quantification:** An initial estimate suggests that reducing the organic churn rate from 8.2% back to the 5.1% baseline could avoid substantial MRR loss. However, our confidence in any specific dollar amount is **LOW** because this estimate relies on several unverified assumptions. The primary value of this recommendation is strategic risk mitigation, not a guaranteed financial return.

---

## Anomalies & Surprises
-   **Observation:** The Pro tier churn rate also saw a statistically significant, though much smaller, increase from 6.1% in Q1 to 7.2% in Q2.
-   **Possible Explanation:** This was not linked to any known event. It could be an early sign of a competitor's actions or a second-order effect of our internal focus on the Enterprise tier (e.g., sales/support distraction).
-   **Why It Matters:** While not the main fire, it's smoke that needs watching. It could indicate a broader market shift or a brewing problem in our mid-market segment.
-   **Suggested Action:** No immediate action required. Task the Growth team with monitoring the Pro tier churn rate weekly through Q3. If the rate exceeds 7.5%, a separate diagnostic analysis should be triggered.

---

## Caveats & Limitations
-   **Correlation vs. Causation:** This analysis shows a strong *association* between the price increase and higher churn. As an observational study, it does not prove causation. Confounding factors not present in our data, such as customer tenure or product usage intensity, could also play a role.
-   **Data Gaps:**
    -   The request to investigate support ticket volume could not be fulfilled as this data is not in the warehouse. This remains an unknown factor.
    -   Historical MRR (pre-April 2026) is missing from the legacy billing system, so all historical comparisons were limited to customer counts (logo churn), not revenue churn.
-   **Exploratory Findings:** The noted increase in Pro tier churn is an exploratory finding. It was discovered and tested on the same data, and requires validation on future data (e.g., from Q3) to be considered conclusive.
-   **Key Assumption:** The analysis assumes that the definition and logging of a 'churn event' could be reliably reconciled between the old and new billing systems after our data cleaning corrections. If subtle differences remain, this could slightly alter the exact churn percentages.

---

## Next Steps
1.  **Causal Impact Analysis:** **To confirm the price hike's true effect,** commission a formal causal analysis (e.g., Difference-in-Differences) led by a data scientist. This would provide a more defensible estimate of price elasticity to inform future pricing decisions.
2.  **Pro Tier Deep-Dive:** **If Pro tier churn continues to rise,** the next step would be to enrich customer data with product analytics to determine if churn is correlated with the usage of specific features or user personas.
3.  **Support Data Integration:** **To answer the original question about support's impact,** initiate a data engineering project to ingest support ticket data from its source system into the data warehouse. This would unlock analysis on the operational drivers of retention.

---

## Visualisation Manifest
| Chart | Insight Headline | Dashboard Section | Data Source |
|---|---|---|---|
| Waterfall: Enterprise Churn Increased from Two Distinct Events in Q2 | Deconstructing the Enterprise Churn Spike | clean_schema_aggregates.quarter, is_reseller_cohort, churn_count |
| Grouped Bar: Enterprise Churn Rate Tripled to 12.5% in Q2, While Other Tiers Remained Stable | Deconstructing the Enterprise Churn Spike | clean_schema_aggregates.quarter, plan_tier, churn_rate |
| Bar Chart: Post-Hike 'Organic' Churn Rose to 8.2%, Exceeding Industry Benchmarks | Supporting Evidence & Context | clean_schema_aggregates.is_post_price_hike_renewal, churn_rate |
| 100% Stacked Area: Customer Mix Remained Stable, Disproving Mix-Shift Hypothesis | Supporting Evidence & Context | clean_schema_aggregates.month, plan_tier, active_customer_count |

---

## Methodology Appendix
-   **Data sources:** `subscriptions` (new system), `billing` (legacy system), `users`.
-   **Cleaning summary:** The two data sources were unified. Key cleaning steps included: deduplicating 2,329 subscription records, standardizing legacy plan names to current tiers, and correcting a 5,432-record data artifact where churn from the system migration was misattributed to April 1st instead of March 31st.
-   **Statistical tests:** Chi-squared Test of Independence (to compare churn across tiers), Two-Proportion Z-test (to compare churn between cohorts and time periods). All results were statistically significant at a Bonferroni-corrected alpha of 0.01.
-   **Assumptions:**
    1.  A reliable attribute existed to identify the terminated reseller's customer cohort.
    2.  The definition of 'churn' could be consistently applied across the old and new billing systems after data cleaning.
    3.  The primary metric of concern was customer count (logo churn).
    4.  Q2 was defined as April 1st to June 30th, 2026.