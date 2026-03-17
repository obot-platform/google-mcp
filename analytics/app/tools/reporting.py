"""Reporting API tools: run_report."""

import json
import logging
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from app.auth import _get_access_token
from app.ga_clients import DATA_V1BETA, auth_headers, property_name

logger = logging.getLogger(__name__)


def _clean(obj: Any) -> Any:
    """Recursively drop None values so the GA API doesn't reject the body."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_clean(i) for i in obj]
    return obj


def register_reporting_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="ga_run_report",
        annotations={
            "title": "Run a GA Analytics Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def ga_run_report(
        property_id: str,
        date_ranges: list[dict],
        dimensions: list[dict],
        metrics: list[dict],
        dimension_filter: dict | None = None,
        metric_filter: dict | None = None,
        order_bys: list[dict] | None = None,
        limit: int = 10000,
        offset: int = 0,
        currency_code: str | None = None,
        return_property_quota: bool = False,
    ) -> str:
        """Runs a Google Analytics report for a GA4 property.

        Args:
            property_id: GA property ID (numeric or "properties/NNN").
            date_ranges: List of date range dicts, e.g.:
                [{"startDate": "30daysAgo", "endDate": "today"}]
            dimensions: List of dimension dicts, e.g.:
                [{"name": "sessionSource"}, {"name": "sessionMedium"}]
            metrics: List of metric dicts, e.g.:
                [{"name": "sessions"}, {"name": "activeUsers"}]
            dimension_filter: Optional FilterExpression dict for dimensions.
            metric_filter: Optional FilterExpression dict for metrics.
            order_bys: Optional list of OrderBy dicts.
            limit: Maximum rows to return (default 10000).
            offset: Row offset for pagination (default 0).
            currency_code: Optional ISO 4217 currency code (e.g. "USD").
            return_property_quota: Whether to include quota info in response.

        Returns:
            str: JSON object with dimensionHeaders, metricHeaders, rows,
                 rowCount, and optionally propertyQuota.
        """
        try:
            access_token = _get_access_token()
            prop = property_name(property_id)
            body = _clean({
                "dateRanges": date_ranges,
                "dimensions": dimensions,
                "metrics": metrics,
                "dimensionFilter": dimension_filter,
                "metricFilter": metric_filter,
                "orderBys": order_bys,
                "limit": limit,
                "offset": offset,
                "currencyCode": currency_code,
                "returnPropertyQuota": return_property_quota,
            })
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=60.0
            ) as client:
                resp = await client.post(
                    f"{DATA_V1BETA}/{prop}:runReport", json=body
                )
                resp.raise_for_status()
                return json.dumps(resp.json(), indent=2)
        except httpx.HTTPStatusError as e:
            logger.exception("ga_run_report failed: HTTP %s — %s", e.response.status_code, e.response.text)
            raise ToolError(f"Google API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception("ga_run_report failed")
            raise ToolError(f"ga_run_report failed: {e}")
