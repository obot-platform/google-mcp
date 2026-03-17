"""Reporting API tools: custom dimensions and metrics metadata."""

import json
import logging

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from app.auth import _get_access_token
from app.ga_clients import DATA_V1BETA, auth_headers, property_name

logger = logging.getLogger(__name__)


def register_metadata_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="ga_get_custom_dimensions_and_metrics",
        annotations={
            "title": "Get GA Custom Dimensions and Metrics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def ga_get_custom_dimensions_and_metrics(
        property_id: str,
    ) -> str:
        """Returns custom dimensions and metrics defined for a GA4 property.

        Fetches the property's reporting metadata and filters to only the
        custom (non-standard) dimensions and metrics.

        Args:
            property_id: GA property ID (numeric or "properties/NNN").

        Returns:
            str: JSON object with two keys:
                - customDimensions: list of dimension metadata objects
                - customMetrics: list of metric metadata objects
            Each object has apiName, uiName, description, and category fields.
        """
        try:
            access_token = _get_access_token()
            prop = property_name(property_id)
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                resp = await client.get(f"{DATA_V1BETA}/{prop}/metadata")
                resp.raise_for_status()
                data = resp.json()

            custom_dimensions = [
                d for d in data.get("dimensions", [])
                if d.get("customDefinition", False)
            ]
            custom_metrics = [
                m for m in data.get("metrics", [])
                if m.get("customDefinition", False)
            ]
            return json.dumps(
                {"customDimensions": custom_dimensions, "customMetrics": custom_metrics},
                indent=2,
            )
        except httpx.HTTPStatusError as e:
            logger.exception("ga_get_custom_dimensions_and_metrics failed: HTTP %s — %s", e.response.status_code, e.response.text)
            raise ToolError(f"Google API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception("ga_get_custom_dimensions_and_metrics failed")
            raise ToolError(f"ga_get_custom_dimensions_and_metrics failed: {e}")
