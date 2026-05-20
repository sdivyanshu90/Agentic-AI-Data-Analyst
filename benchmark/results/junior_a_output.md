Here is the analysis of the Telco Customer Churn dataset.

***

### **Analysis of Customer Churn Drivers**

**To:** Customer Retention & Marketing Leadership
**From:** Junior Data Analyst
**Date:** October 26, 2023
**Subject:** Key Drivers of Customer Churn and Recommendations for Retention

#### **1. Executive Summary**

This analysis identifies the primary factors driving customer churn based on the provided dataset of 7,043 customers. The overall churn rate is **26.5%**. Our findings show that churn is not random; it is concentrated among specific customer segments defined by their contract, tenure, and service choices.

**Key Findings:**
*   **Contract Type is the #1 Driver:** Customers on **Month-to-Month** contracts are significantly more likely to churn (**42.7% churn rate**) compared to those on One-Year (11.3%) or Two-Year (2.8%) contracts.
*   **New Customers are at Highest Risk:** Customers with a short tenure (0-12 months) have a very high churn rate, which drops dramatically as their relationship with us lengthens.
*   **Service Configuration Matters:** Customers with **Fiber Optic** internet service churn at a much higher rate (41.9%) than those with DSL (19.0%). This is especially true for fiber customers who lack key support services like **Tech Support** and **Online Security**.

**Top Recommendations:**
Based on these drivers, we recommend focusing on three cost-effective interventions:
1.  **Incentivize Annual Contracts:** Actively convert Month-to-Month customers to longer-term contracts with targeted discounts or service upgrades.
2.  **Launch an Early-Tenure Onboarding Program:** Focus retention efforts on customers in their first 12 months with proactive support and value reinforcement.
3.  **Bundle Protective Services for Fiber Customers:** Reduce the friction and perceived risk of the premium Fiber Optic service by bundling support add-ons like `TechSupport` or `OnlineSecurity`.

---

#### **2. Analysis of Key Churn Drivers**

We analyzed how churn rates vary across different customer segments. The factors below show the largest impact on a customer's likelihood to leave.

##### **Driver 1: Contract Type**
A customer's contract type is the single strongest predictor of churn. Customers on flexible, Month-to-Month plans churn at an alarming rate, while those on longer contracts are extremely loyal.

| Contract Type | Churn Rate |
| :--- | :--- |
| **Month-to-Month** | **42.7%** |
| One Year | 11.3% |
| Two Year | 2.8% |
| *Overall Average* | *26.5%* |

This suggests that a lack of commitment is a major risk factor. These customers are likely more sensitive to price changes, service issues, and competitor offers.

##### **Driver 2: Customer Tenure**
New customers are significantly more likely to churn. The first year is a critical period for building loyalty. After 24 months, customer churn drops to well below the company average.

| Tenure (Months) | Churn Rate |
| :--- | :--- |
| **0 - 12** | **47.9%** |
| 13 - 24 | 29.8% |
| 25 - 48 | 16.9% |
| 49+ | 9.0% |

This highlights the importance of the initial customer experience. If a customer is not fully onboarded or doesn't see immediate value, they are likely to leave quickly.

##### **Driver 3: Internet Service & Support Add-ons**
The type of internet service and the adoption of related support services create a clear divide in churn behavior.

*   **Fiber Optic Service:** While a premium offering, customers with Fiber Optic service churn at a rate of **41.9%**, more than double the rate for DSL customers (**19.0%**). This may be due to higher prices, perceived service instability, or attracting a less loyal customer segment.

*   **Lack of Support Services:** For customers with internet, not having key support services drastically increases their churn risk. This is a clear indicator of an unmet need for security and technical assistance.

| Service Add-on | Churn Rate (With the service) | Churn Rate (Without the service) |
| :--- | :--- | :--- |
| **Online Security** | 14.6% | **42.0%** |
| **Tech Support** | 15.2% | **41.6%** |

Customers who do not subscribe to these services are nearly three times as likely to churn.

##### **Other Notable Factors:**
*   **Payment Method:** Customers using **Electronic Check** as their payment method have a significantly higher churn rate (**45.3%**) compared to those using automatic methods like credit card (15.2%) or bank transfer (16.7%). This may indicate payment friction or a less "locked-in" customer mindset.
*   **Monthly Charges:** Customers with higher monthly bills (over $70) tend to have a higher churn rate, which aligns with the finding that high-priced Fiber Optic plans are a risk factor.

---

#### **3. Recommendations for Action**

The data points to clear, actionable strategies to reduce churn by focusing on the most at-risk customer segments.

##### **Recommendation 1: Drive Long-Term Contract Adoption**
*   **Action:** Launch a targeted marketing campaign for Month-to-Month customers, offering a compelling incentive (e.g., one month free, a permanent $10/month discount, or a free premium add-on like Streaming TV) to upgrade to a One-Year or Two-Year contract.
*   **Impact:** This directly addresses the single largest driver of churn. Even a small conversion rate in this segment of 3,875 customers will significantly reduce the overall churn number. This is more cost-effective than acquiring new customers.

##### **Recommendation 2: Implement a "First Year Care" Program**
*   **Action:** Create a proactive onboarding program for all new customers. This could include a 30-day "wellness check" call, educational emails on how to use their services, and a special offer at the 6-month mark to reinforce value.
*   **Impact:** This targets the high-risk 0-12 month tenure group. By improving their initial experience and demonstrating value early, we can significantly lower the high churn rate in this critical period and build a foundation for long-term loyalty.

##### **Recommendation 3: De-risk the Fiber Optic Experience**
*   **Action:** For new and existing Fiber Optic customers, create a "Total Protection" bundle that includes **Tech Support** and **Online Security** at a highly discounted rate (or free for the first year). Position it as an essential part of the premium fiber experience.
*   **Impact:** This addresses the high churn rate within our premium customer segment. By bundling these sticky, value-add services, we increase the product's value proposition, reduce technical friction points, and make the service harder to leave.