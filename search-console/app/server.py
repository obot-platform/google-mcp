"""FastMCP server for Google Search Console — runs behind mcp-oauth-proxy."""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.tools.analytics import register_analytics_tools
from app.tools.inspection import register_inspection_tools
from app.tools.properties import register_property_tools
from app.tools.sitemaps import register_sitemap_tools

PORT = int(os.getenv("PORT", 9000))
MCP_PATH = os.getenv("MCP_PATH", "/mcp/google-search-console")

mcp = FastMCP(
    name="google_search_console_mcp",
    on_duplicate="error",
    mask_error_details=True,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "healthy"})


register_analytics_tools(mcp)
register_inspection_tools(mcp)
register_property_tools(mcp)
register_sitemap_tools(mcp)


def streamable_http_server():
    """Main entry point for the Google Search Console MCP server."""
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=PORT,
        path=MCP_PATH,
    )


def stdio_server():
    """STDIO entry point for the Google Search Console MCP server."""
    mcp.run()


if __name__ == "__main__":
    streamable_http_server()
