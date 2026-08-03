"""
AWS Cost Explorer integration.

Expected credentials dict:
{
    "aws_access_key_id": "...",
    "aws_secret_access_key": "...",
    "region_name": "us-east-1"   # optional, Cost Explorer is a global service but boto3 needs a region
}

The IAM user/role only needs the AWS-managed read-only policy:
  "ce:GetCostAndUsage", "ce:GetCostForecast"
"""
from datetime import date, timedelta

import boto3


def _month_bounds():
    today = date.today()
    start = today.replace(day=1)
    return start.isoformat(), (today + timedelta(days=1)).isoformat()


def get_mtd_cost(credentials: dict) -> float:
    """Returns total unblended cost month-to-date, in USD."""
    client = boto3.client(
        "ce",
        aws_access_key_id=credentials["aws_access_key_id"],
        aws_secret_access_key=credentials["aws_secret_access_key"],
        region_name=credentials.get("region_name", "us-east-1"),
    )
    start, end = _month_bounds()
    resp = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    results = resp.get("ResultsByTime", [])
    if not results:
        return 0.0
    return float(results[0]["Total"]["UnblendedCost"]["Amount"])


def get_forecasted_month_end_cost(credentials: dict) -> float:
    """Returns AWS's own forecast for total spend by end of the current month."""
    client = boto3.client(
        "ce",
        aws_access_key_id=credentials["aws_access_key_id"],
        aws_secret_access_key=credentials["aws_secret_access_key"],
        region_name=credentials.get("region_name", "us-east-1"),
    )
    today = date.today()
    start = today.isoformat()
    # first day of next month
    if today.month == 12:
        end = date(today.year + 1, 1, 1).isoformat()
    else:
        end = date(today.year, today.month + 1, 1).isoformat()

    if start == end:
        return 0.0

    resp = client.get_cost_forecast(
        TimePeriod={"Start": start, "End": end},
        Metric="UNBLENDED_COST",
        Granularity="MONTHLY",
    )
    return float(resp.get("Total", {}).get("Amount", 0.0))


def get_cost_by_service(credentials: dict, top_n: int = 5) -> list:
    """Returns [(service_name, cost), ...] sorted descending, for the top N cost drivers MTD."""
    client = boto3.client(
        "ce",
        aws_access_key_id=credentials["aws_access_key_id"],
        aws_secret_access_key=credentials["aws_secret_access_key"],
        region_name=credentials.get("region_name", "us-east-1"),
    )
    start, end = _month_bounds()
    resp = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    results = resp.get("ResultsByTime", [])
    if not results:
        return []
    groups = results[0].get("Groups", [])
    rows = [
        (g["Keys"][0], float(g["Metrics"]["UnblendedCost"]["Amount"]))
        for g in groups
    ]
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:top_n]
