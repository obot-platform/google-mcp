"""Property management tools: list, get, add, delete GSC sites."""

import json
import logging

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from app.auth import _get_access_token
from app.gsc_clients import WEBMASTERS_V3, auth_headers, encode_site

logger = logging.getLogger(__name__)


def register_property_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="gsc_list_properties",
        annotations={
            "title": "List GSC Properties",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def gsc_list_properties() -> str:
        """Lists all verified Google Search Console properties the authenticated user can access.

        This is typically the first tool called to discover available site URLs
        before calling analytics, inspection, or sitemap tools.

        Returns:
            str: JSON array of site objects, each with siteUrl and permissionLevel.
        """
        try:
            access_token = _get_access_token()
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                resp = await client.get(f"{WEBMASTERS_V3}/sites")
                resp.raise_for_status()
                data = resp.json()
                return json.dumps(data.get("siteEntry", []), indent=2)
        except httpx.HTTPStatusError as e:
            logger.exception("gsc_list_properties failed: HTTP %s — %s", e.response.status_code, e.response.text)
            raise ToolError(f"Google API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception("gsc_list_properties failed")
            raise ToolError(f"gsc_list_properties failed: {e}")

    @mcp.tool(
        name="gsc_get_site_details",
        annotations={
            "title": "Get GSC Site Details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def gsc_get_site_details(
        site_url: str,
    ) -> str:
        """Returns details about a specific Google Search Console property.

        Args:
            site_url: The full site URL as registered in GSC
                (e.g. "https://example.com/" or "sc-domain:example.com").

        Returns:
            str: JSON object with siteUrl, permissionLevel, and verificationState.
        """
        try:
            access_token = _get_access_token()
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                resp = await client.get(
                    f"{WEBMASTERS_V3}/sites/{encode_site(site_url)}"
                )
                resp.raise_for_status()
                return json.dumps(resp.json(), indent=2)
        except httpx.HTTPStatusError as e:
            logger.exception("gsc_get_site_details failed: HTTP %s — %s", e.response.status_code, e.response.text)
            raise ToolError(f"Google API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception("gsc_get_site_details failed")
            raise ToolError(f"gsc_get_site_details failed: {e}")

    @mcp.tool(
        name="gsc_add_site",
        annotations={
            "title": "Add GSC Site",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def gsc_add_site(
        site_url: str,
    ) -> str:
        """Adds a site to the authenticated user's Google Search Console account.

        The site must be a valid URL. After adding, the user will need to verify
        ownership before full data becomes available.

        Args:
            site_url: The full site URL to add
                (e.g. "https://example.com/" or "sc-domain:example.com").

        Returns:
            str: JSON success message or structured error.
        """
        try:
            access_token = _get_access_token()
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                resp = await client.put(
                    f"{WEBMASTERS_V3}/sites/{encode_site(site_url)}"
                )
                if resp.status_code == 204:
                    return json.dumps({"success": True, "siteUrl": site_url})
                if resp.status_code == 409:
                    raise ToolError(f"Site already exists in GSC: {site_url}")
                if resp.status_code == 403:
                    raise ToolError(f"Permission denied adding site: {site_url}")
                if resp.status_code == 400:
                    raise ToolError(f"Bad request — invalid site URL format: {site_url}")
                resp.raise_for_status()
                return json.dumps({"success": True, "siteUrl": site_url})
        except ToolError:
            raise
        except httpx.HTTPStatusError as e:
            logger.exception("gsc_add_site failed: HTTP %s — %s", e.response.status_code, e.response.text)
            raise ToolError(f"Google API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception("gsc_add_site failed")
            raise ToolError(f"gsc_add_site failed: {e}")

    @mcp.tool(
        name="gsc_delete_site",
        annotations={
            "title": "Delete GSC Site",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def gsc_delete_site(
        site_url: str,
    ) -> str:
        """Removes a site from the authenticated user's Google Search Console account.

        WARNING: This action is irreversible. The site and its associated data
        will be removed from the user's GSC account. Ownership verification
        will need to be repeated if re-added.

        Args:
            site_url: The full site URL to delete
                (e.g. "https://example.com/" or "sc-domain:example.com").

        Returns:
            str: JSON success confirmation or structured error.
        """
        try:
            access_token = _get_access_token()
            async with httpx.AsyncClient(
                headers=auth_headers(access_token), timeout=30.0
            ) as client:
                resp = await client.delete(
                    f"{WEBMASTERS_V3}/sites/{encode_site(site_url)}"
                )
                if resp.status_code == 204:
                    return json.dumps({"success": True, "deleted": site_url})
                if resp.status_code == 404:
                    raise ToolError(f"Site not found in GSC: {site_url}")
                if resp.status_code == 403:
                    raise ToolError(f"Permission denied deleting site: {site_url}")
                resp.raise_for_status()
                return json.dumps({"success": True, "deleted": site_url})
        except ToolError:
            raise
        except httpx.HTTPStatusError as e:
            logger.exception("gsc_delete_site failed: HTTP %s — %s", e.response.status_code, e.response.text)
            raise ToolError(f"Google API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.exception("gsc_delete_site failed")
            raise ToolError(f"gsc_delete_site failed: {e}")
