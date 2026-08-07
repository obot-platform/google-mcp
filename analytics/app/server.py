"""FastMCP server for Google Analytics — runs behind mcp-oauth-proxy."""

import os

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.tools.admin import register_admin_tools
from app.tools.metadata import register_metadata_tools
from app.tools.realtime import register_realtime_tools
from app.tools.reporting import register_reporting_tools

PORT = int(os.getenv("PORT", 9000))
MCP_PATH = os.getenv("MCP_PATH", "/mcp/google-analytics").rstrip("/")


class LegacyTrailingSlashMiddleware:
    def __init__(self, app: ASGIApp, path: str):
        self.app = app
        self.path = path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"].rstrip("/") == self.path:
            scope = dict(scope)
            scope["path"] = self.path
            scope["raw_path"] = self.path.encode()

        await self.app(scope, receive, send)

mcp = FastMCP(
    name="google_analytics_mcp",
    on_duplicate="error",
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
        middleware=[Middleware(LegacyTrailingSlashMiddleware, path=MCP_PATH)],
    )


def stdio_server():
    """STDIO entry point for the Google Analytics MCP server."""
    mcp.run()


if __name__ == "__main__":
    streamable_http_server()
