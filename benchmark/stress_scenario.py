"""Part C stress-test scenario — shared inputs for baseline and v3 runs.

Every element of this scenario is an injected trap mapped to a specific
phase that should catch it (see the audit spec, Part C). Keep the wording
verbatim — the traps only work if the pipeline has to notice them itself.
"""

OBJECTIVE = (
    "Our VP of Growth thinks we have a churn problem specifically in the "
    "Enterprise tier this quarter. Our CFO thinks it's actually a pricing "
    "problem across all tiers and Enterprise just looks worse because of mix "
    "shift. Figure out what's actually going on with Q2 and tell us what to "
    "do. Also, if you get a chance, check whether support ticket volume is "
    "driving any of this — I think support's been slower this quarter. We "
    "need this by Friday."
)

DATA_DESCRIPTION = (
    "Data's in the warehouse: users, events, subscriptions, and a billing "
    "table that our old system also wrote to before we migrated in April. "
    "No support ticket table available. We rolled out a 15% Enterprise "
    "price increase on April 1st. Also FYI, our biggest Enterprise reseller "
    "partner ended their contract March 28th."
)

STAKEHOLDER = "VP of Growth and CFO (executive leadership)"

BUSINESS_DOMAIN = "SaaS"

CONSTRAINTS = {
    "time": "Needed by Friday",
    "tools": "SQL + Python",
    "privacy": "",
}
