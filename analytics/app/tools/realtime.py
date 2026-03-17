"""Reporting API tools: run_realtime_report."""

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


def register_realtime_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="ga_run_realtime_report",
        annotations={
            "title": "Run a GA Realtime Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def ga_run_realtime_report(
        property_id: str,
        dimensions: list[dict],
        metrics: list[dict],
        dimension_filter: dict | None = None,
        metric_filter: dict | None = None,
        order_bys: list[dict] | None = None,
        limit: int = 10000,
        return_property_quota: bool = False,
    ) -> str:
        """Runs a Google Analytics realtime report for a GA4 property.

        Returns data for the last 30 minutes of activity.

        Args:
            property_id: GA property ID (numeric or "properties/NNN").
            dimensions: List of dimension dicts, e.g.:
                [{"name": "city"}, {"name": "deviceCategory"}]
            metrics: List of metric dicts, e.g.:
                [{"name": "activeUsers"}]
            dimension_filter: Optional FilterExpression dict for dimensions.
            metric_filter: Optional FilterExpression dict for metrics.
            order_bys: Optional list of OrderBy dicts.
            limit: Maximum rows to return (default 10000).
            return_property_quota: Whether to include quota info in response.

        Returns:
            str: JSON object with dimensionHeaders, metricHeaders, rows,
                 rowCount, and optionally propertyQuota.
        """
        try:
            access_token = _get_access_token()
            prop = property_name(property_id)
            body = _clean({
                "dimensions": dimensions,
                "metrics": metrics,
                "dimensionFilter": dimension_filter,
                "metricFilter": metric_filter,
                "orderBys": order_bys,
                "limit": limit,
                "returnPropertyQuota": return_property_quota,
            })
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                resp = await client.post(
                    f"{DATA_V1BETA}/{prop}:runRealtimeReport", json=body
                )
                resp.raise_for_status()
                return json.dumps(resp.json(), indent=2)
        except httpx.HTTPStatusError as e:
            logger.exception("ga_run_realtime_report failed: HTTP %s — %s", e.response.status_code, e.response.text)
            raise ToolError(f"Google API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception("ga_run_realtime_report failed")
            raise ToolError(f"ga_run_realtime_report failed: {e}")
