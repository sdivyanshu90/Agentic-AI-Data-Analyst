# Churn Analysis — Junior Analyst (pandas EDA)

Dataset: 7043 rows. Overall churn rate: 26.5%.

## Churn rate by category
- **Contract** (spread 39.9%): Month-to-month=42.7%, One year=11.3%, Two year=2.8%
- **InternetService** (spread 34.5%): Fiber optic=41.9%, DSL=19.0%, No=7.4%
- **OnlineSecurity** (spread 34.4%): No=41.8%, Yes=14.6%, No internet service=7.4%
- **TechSupport** (spread 34.2%): No=41.6%, Yes=15.2%, No internet service=7.4%
- **OnlineBackup** (spread 32.5%): No=39.9%, Yes=21.5%, No internet service=7.4%
- **DeviceProtection** (spread 31.7%): No=39.1%, Yes=22.5%, No internet service=7.4%
- **PaymentMethod** (spread 30.0%): Electronic check=45.3%, Mailed check=19.1%, Bank transfer (automatic)=16.7%, Credit card (automatic)=15.2%
- **StreamingMovies** (spread 26.3%): No=33.7%, Yes=29.9%, No internet service=7.4%
- **StreamingTV** (spread 26.1%): No=33.5%, Yes=30.1%, No internet service=7.4%
- **SeniorCitizen** (spread 18.1%): 1=41.7%, 0=23.6%
- **PaperlessBilling** (spread 17.2%): Yes=33.6%, No=16.3%
- **Dependents** (spread 15.8%): No=31.3%, Yes=15.5%
- **Partner** (spread 13.3%): No=33.0%, Yes=19.7%
- **MultipleLines** (spread 3.7%): Yes=28.6%, No=25.0%, No phone service=24.9%
- **PhoneService** (spread 1.8%): Yes=26.7%, No=24.9%
- **gender** (spread 0.8%): Female=26.9%, Male=26.2%

## Numeric averages by churn group
- tenure: churned avg = 18.0, retained avg = 37.6
- MonthlyCharges: churned avg = 74.4, retained avg = 61.3
- TotalCharges: churned avg = 1531.8, retained avg = 2555.3

## Top drivers (by churn-rate spread)
1. Contract — spread of 39.9%
1. InternetService — spread of 34.5%
1. OnlineSecurity — spread of 34.4%
1. TechSupport — spread of 34.2%
1. OnlineBackup — spread of 32.5%

## Recommendations
- Target the high-churn segments above with retention offers / discounts.
- Focus on month-to-month customers since they churn the most.
- Improve onboarding for new customers (low tenure churns more).

_Note: ranked purely by churn-rate spread; no significance testing or effect sizes computed._