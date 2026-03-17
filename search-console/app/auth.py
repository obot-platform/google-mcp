"""Access token helper — extracts the Google OAuth token from proxy headers."""

from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError


def _get_access_token() -> str:
    """Retrieves the Google access token forwarded by mcp-oauth-proxy."""
    headers = get_http_headers()
    access_token = headers.get("x-forwarded-access-token", None)
    if not access_token:
        raise ToolError(
            "No access token found in headers, available headers: " + str(headers)
        )
    return access_token
