"""Access token helper — extracts the Google OAuth token from proxy headers."""

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers


def _get_access_token() -> str:
    """Retrieves the Google access token forwarded by mcp-oauth-proxy."""
    headers = get_http_headers()
    access_token = headers.get("x-forwarded-access-token", None)
    if not access_token:
        raise ToolError("No access token found in headers.")
    return access_token
