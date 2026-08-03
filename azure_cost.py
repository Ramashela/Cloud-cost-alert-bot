"""
Azure Cost Management integration.

Expected credentials dict:
{
    "tenant_id": "...",
    "client_id": "...",
    "client_secret": "...",
    "subscription_id": "..."
}

The service principal only needs the built-in "Cost Management Reader" role
on the subscription.
"""
from datetime import date, timedelta

from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient


def _credential(credentials: dict) -> ClientSecretCredential:
    return ClientSecretCredential(
        tenant_id=credentials["tenant_id"],
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
    )


def get_mtd_cost(credentials: dict) -> float:
    """Returns actual cost month-to-date, in the subscription's billing currency."""
    cred = _credential(credentials)
    client = CostManagementClient(cred)
    scope = f"/subscriptions/{credentials['subscription_id']}"

    today = date.today()
    start = today.replace(day=1)

    query = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "time_period": {"from_property": start.isoformat(), "to": today.isoformat()},
        "dataset": {
            "granularity": "None",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
        },
    }

    result = client.query.usage(scope, query)
    rows = result.rows or []
    if not rows:
        return 0.0
    # First column is typically the cost value for a totals-only query
    return float(rows[0][0])


def get_cost_by_service(credentials: dict, top_n: int = 5) -> list:
    """Returns [(service_name, cost), ...] sorted descending, for the top N cost drivers MTD."""
    cred = _credential(credentials)
    client = CostManagementClient(cred)
    scope = f"/subscriptions/{credentials['subscription_id']}"

    today = date.today()
    start = today.replace(day=1)

    query = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "time_period": {"from_property": start.isoformat(), "to": today.isoformat()},
        "dataset": {
            "granularity": "None",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": "ServiceName"}],
        },
    }

    result = client.query.usage(scope, query)
    columns = [c.name for c in result.columns]
    cost_idx = columns.index("Cost") if "Cost" in columns else 0
    service_idx = columns.index("ServiceName") if "ServiceName" in columns else 1

    rows = [(r[service_idx], float(r[cost_idx])) for r in (result.rows or [])]
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:top_n]
