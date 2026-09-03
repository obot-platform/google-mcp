from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_DAILY_USERS = 25_000
MAX_DAILY_TOOL_COUNTERS = 256
MAX_TOOL_NAME_LENGTH = 128
OVERFLOW_TOOL_NAME = "__other__"


class UsageTelemetry(Middleware):
    """Current-UTC-day MCP call counters and rotating pseudonymous user IDs."""

    def __init__(self, server_id: str, display_name: str, provider: str) -> None:
        self.server_id = server_id
        self.display_name = display_name
        self.provider = provider
        self._hmac_key = os.getenv("MCP_USAGE_HMAC_KEY", "").encode()
        self._scrape_token = os.getenv("MCP_USAGE_SCRAPE_TOKEN", "")
        self._enabled = bool(self._hmac_key and self._scrape_token)
        self._instance_id = str(uuid.uuid4())
        self._started_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        self._day = self._utc_day()
        self._calls: dict[str, int] = defaultdict(int)
        self._errors: dict[str, int] = defaultdict(int)
        self._users: set[str] = set()
        self._unidentified_calls = 0
        self._lock = asyncio.Lock()

    @staticmethod
    def _utc_day() -> str:
        return datetime.now(UTC).date().isoformat()

    def _roll_day(self) -> str:
        day = self._utc_day()
        if day != self._day:
            self._day = day
            self._calls.clear()
            self._errors.clear()
            self._users.clear()
            self._unidentified_calls = 0
        return day

    def _identity_hash(self, day: str) -> str | None:
        headers = get_http_headers()
        email = headers.get("x-forwarded-email", "").strip().lower()
        forwarded_user = headers.get("x-forwarded-user", "").strip().lower()
        identity = email if email else f"{self.provider}:{forwarded_user}" if forwarded_user else ""
        if not identity:
            return None
        return hmac.new(self._hmac_key, f"{day}\n{identity}".encode(), hashlib.sha256).hexdigest()

    def _tool_counter_key(self, tool: str) -> str:
        if tool == OVERFLOW_TOOL_NAME or len(tool) > MAX_TOOL_NAME_LENGTH:
            return OVERFLOW_TOOL_NAME
        if tool in self._calls:
            return tool
        named_tool_count = len(self._calls) - (OVERFLOW_TOOL_NAME in self._calls)
        if named_tool_count < MAX_DAILY_TOOL_COUNTERS - 1:
            return tool
        return OVERFLOW_TOOL_NAME

    async def on_call_tool(
        self,
        context: MiddlewareContext[Any],
        call_next: Callable[[MiddlewareContext[Any]], Awaitable[Any]],
    ) -> Any:
        if not self._enabled:
            return await call_next(context)
        tool = str(getattr(context.message, "name", "unknown"))
        async with self._lock:
            day = self._roll_day()
            tool = self._tool_counter_key(tool)
            self._calls[tool] += 1
            identity_hash = self._identity_hash(day)
            if identity_hash:
                if len(self._users) < MAX_DAILY_USERS or identity_hash in self._users:
                    self._users.add(identity_hash)
            else:
                self._unidentified_calls += 1
        try:
            result = await call_next(context)
        except Exception:
            async with self._lock:
                if self._roll_day() == day:
                    self._errors[tool] += 1
            raise
        if bool(getattr(result, "isError", False)) or bool(getattr(result, "is_error", False)):
            async with self._lock:
                if self._roll_day() == day:
                    self._errors[tool] += 1
        return result

    async def handle_request(self, request: Request) -> JSONResponse:
        if not self._enabled:
            return JSONResponse({"error": "usage_metrics_disabled"}, status_code=503)
        token = request.headers.get("x-obot-metrics-token", "")
        if not hmac.compare_digest(token.encode(), self._scrape_token.encode()):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        async with self._lock:
            self._roll_day()
            return JSONResponse(
                {
                    "schemaVersion": "v1",
                    "server": {"id": self.server_id, "displayName": self.display_name, "provider": self.provider},
                    "instance": {"id": self._instance_id, "startedAt": self._started_at},
                    "day": self._day,
                    "calls": [
                        {"tool": tool, "calls": calls, "errors": self._errors.get(tool, 0)}
                        for tool, calls in sorted(self._calls.items())
                    ],
                    "userHashes": sorted(self._users),
                    "unidentifiedCalls": self._unidentified_calls,
                }
            )
