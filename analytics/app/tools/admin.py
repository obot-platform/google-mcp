"""Admin API tools: accounts, properties, ads links, annotations."""

import json
import logging

import httpx
from fastmcp import FastMCP

from app.auth import _get_access_token
from app.ga_clients import (
    ADMIN_V1ALPHA,
    ADMIN_V1BETA,
    auth_headers,
    property_name,
)

logger = logging.getLogger(__name__)


def register_admin_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="ga_get_account_summaries",
        annotations={
            "title": "Get GA Account Summaries",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def ga_get_account_summaries() -> str:
        """Retrieves all Google Analytics accounts and properties the user can access.

        Use this to discover property IDs before calling reporting or admin tools.
        Returns every account and its child GA4 properties with display names and IDs.

        Returns:
            str: JSON array of account summary objects, each containing:
                - name (str): Account resource name (e.g. "accounts/123")
                - displayName (str): Human-readable account name
                - propertySummaries (list): Each item has name, displayName,
                  propertyType, and parent fields
        """
        try:
            access_token = _get_access_token()
            results = []
            page_token = None
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                while True:
                    params = {}
                    if page_token:
                        params["pageToken"] = page_token
                    resp = await client.get(
                        f"{ADMIN_V1BETA}/accountSummaries", params=params
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    results.extend(data.get("accountSummaries", []))
                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.exception("ga_get_account_summaries failed")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="ga_get_property_details",
        annotations={
            "title": "Get GA Property Details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def ga_get_property_details(property_id: str) -> str:
        """Returns configuration details about a Google Analytics GA4 property.

        Args:
            property_id: The GA property ID. Accepted formats:
                - Numeric string (e.g. "123456789")
                - Resource name format (e.g. "properties/123456789")

        Returns:
            str: JSON object with property fields including name, displayName,
                 timeZone, currencyCode, industryCategory, createTime,
                 updateTime, parent, and serviceLevel.
        """
        try:
            access_token = _get_access_token()
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                resp = await client.get(
                    f"{ADMIN_V1BETA}/{property_name(property_id)}"
                )
                resp.raise_for_status()
                return json.dumps(resp.json(), indent=2)
        except Exception as e:
            logger.exception("ga_get_property_details failed")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="ga_list_google_ads_links",
        annotations={
            "title": "List Google Ads Links for a Property",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def ga_list_google_ads_links(property_id: str) -> str:
        """Returns all Google Ads accounts linked to a GA property.

        Args:
            property_id: The GA property ID. Accepted formats:
                - Numeric string (e.g. "123456789")
                - Resource name format (e.g. "properties/123456789")

        Returns:
            str: JSON array of googleAdsLinks objects, each with name,
                 customerId, canManageClients, adsPersonalizationEnabled,
                 and createTime.
        """
        try:
            access_token = _get_access_token()
            results = []
            page_token = None
            prop = property_name(property_id)
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                while True:
                    params = {}
                    if page_token:
                        params["pageToken"] = page_token
                    resp = await client.get(
                        f"{ADMIN_V1BETA}/{prop}/googleAdsLinks", params=params
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    results.extend(data.get("googleAdsLinks", []))
                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.exception("ga_list_google_ads_links failed")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="ga_list_property_annotations",
        annotations={
            "title": "List Property Annotations",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def ga_list_property_annotations(property_id: str) -> str:
        """Returns annotations (notes) added to a GA property for specific dates or periods.

        Annotations record events like deployments, campaign launches, or traffic
        anomalies. Useful for correlating data changes with business events.

        Args:
            property_id: The GA property ID. Accepted formats:
                - Numeric string (e.g. "123456789")
                - Resource name format (e.g. "properties/123456789")

        Returns:
            str: JSON array of annotation objects, each with name, title,
                 description, color, systemGenerated, and an annotationDate
                 or dateRange field.
        """
        try:
            access_token = _get_access_token()
            results = []
            page_token = None
            prop = property_name(property_id)
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                while True:
                    params = {}
                    if page_token:
                        params["pageToken"] = page_token
                    resp = await client.get(
                        f"{ADMIN_V1ALPHA}/{prop}/reportingDataAnnotations",
                        params=params,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    results.extend(data.get("reportingDataAnnotations", []))
                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.exception("ga_list_property_annotations failed")
            return json.dumps({"error": str(e)})
