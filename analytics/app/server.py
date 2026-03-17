"""FastMCP server for Google Analytics — runs behind mcp-oauth-proxy."""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.tools.admin import register_admin_tools
from app.tools.metadata import register_metadata_tools
from app.tools.realtime import register_realtime_tools
from app.tools.reporting import register_reporting_tools

PORT = int(os.getenv("PORT", 9000))
MCP_PATH = os.getenv("MCP_PATH", "/mcp/google-analytics")

mcp = FastMCP(
    name="google_analytics_mcp",
    on_duplicate_tools="error",
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
    mask_error_details=True,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "healthy"})


register_admin_tools(mcp)
register_reporting_tools(mcp)
register_realtime_tools(mcp)
register_metadata_tools(mcp)


def streamable_http_server():
    """Main entry point for the Google Analytics MCP server."""
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=PORT,
        path=MCP_PATH,
    )


def stdio_server():
    """STDIO entry point for the Google Analytics MCP server."""
    mcp.run()


if __name__ == "__main__":
    streamable_http_server()
