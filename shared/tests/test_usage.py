import asyncio
import hashlib
import hmac
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from obot_mcp_usage import (
    MAX_DAILY_TOOL_COUNTERS,
    MAX_TOOL_NAME_LENGTH,
    OVERFLOW_TOOL_NAME,
    UsageTelemetry,
)
from starlette.requests import Request


class UsageTelemetryTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _context(tool: str) -> SimpleNamespace:
        return SimpleNamespace(message=SimpleNamespace(name=tool))

    @staticmethod
    def _request(token: str | None = None) -> Request:
        headers = []
        if token is not None:
            headers.append((b"x-obot-metrics-token", token.encode()))
        return Request({"type": "http", "headers": headers})

    @staticmethod
    def _enabled_usage() -> UsageTelemetry:
        with patch.dict(
            os.environ,
            {"MCP_USAGE_HMAC_KEY": "secret", "MCP_USAGE_SCRAPE_TOKEN": "token"},
            clear=True,
        ):
            return UsageTelemetry("server", "Server", "provider")

    async def test_disabled_operation_bypasses_collection_and_scraping(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            usage = UsageTelemetry("server", "Server", "provider")
        expected_result = object()
        call_count = 0

        async def call_next(_context: object) -> object:
            nonlocal call_count
            call_count += 1
            return expected_result

        result = await usage.on_call_tool(self._context("tool"), call_next)
        response = await usage.handle_request(self._request("token"))

        self.assertIs(result, expected_result)
        self.assertEqual(call_count, 1)
        self.assertEqual(dict(usage._calls), {})
        self.assertEqual(dict(usage._errors), {})
        self.assertEqual(usage._users, set())
        self.assertEqual(usage._unidentified_calls, 0)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.body), {"error": "usage_metrics_disabled"})

    def test_both_secrets_are_required_to_enable_collection(self) -> None:
        environments = (
            {},
            {"MCP_USAGE_HMAC_KEY": "secret"},
            {"MCP_USAGE_SCRAPE_TOKEN": "token"},
        )
        for environment in environments:
            with self.subTest(environment=environment):
                with patch.dict(os.environ, environment, clear=True):
                    usage = UsageTelemetry("server", "Server", "provider")
                self.assertFalse(usage._enabled)

        self.assertTrue(self._enabled_usage()._enabled)

    async def test_scrape_token_authentication(self) -> None:
        usage = self._enabled_usage()

        for supplied_token in (None, "", "wrong"):
            with self.subTest(supplied_token=supplied_token):
                response = await usage.handle_request(self._request(supplied_token))
                self.assertEqual(response.status_code, 401)
                self.assertEqual(json.loads(response.body), {"error": "unauthorized"})

        response = await usage.handle_request(self._request("token"))
        payload = json.loads(response.body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["schemaVersion"], "v1")
        self.assertEqual(
            payload["server"],
            {"id": "server", "displayName": "Server", "provider": "provider"},
        )
        self.assertEqual(payload["calls"], [])
        self.assertEqual(payload["userHashes"], [])

    def test_identity_hash_is_deterministic_and_rotates_daily(self) -> None:
        usage = self._enabled_usage()
        day = "2026-09-03"
        expected = hmac.new(
            b"secret", f"{day}\nalice@example.com".encode(), hashlib.sha256
        ).hexdigest()

        with patch(
            "obot_mcp_usage.get_http_headers",
            return_value={"x-forwarded-email": " Alice@Example.COM "},
        ):
            first = usage._identity_hash(day)
            second = usage._identity_hash(day)
            next_day = usage._identity_hash("2026-09-04")

        self.assertEqual(first, expected)
        self.assertEqual(second, expected)
        self.assertNotEqual(next_day, expected)

    def test_identity_hash_falls_back_to_provider_scoped_forwarded_user(self) -> None:
        usage = self._enabled_usage()
        day = "2026-09-03"
        expected = hmac.new(
            b"secret", f"{day}\nprovider:user-123".encode(), hashlib.sha256
        ).hexdigest()

        with patch(
            "obot_mcp_usage.get_http_headers",
            return_value={"x-forwarded-user": " User-123 "},
        ):
            identity_hash = usage._identity_hash(day)

        self.assertEqual(identity_hash, expected)

    def test_daily_rollover_clears_all_daily_state(self) -> None:
        usage = self._enabled_usage()
        usage._day = "2026-09-03"
        usage._calls["tool"] = 2
        usage._errors["tool"] = 1
        usage._users.add("hash")
        usage._unidentified_calls = 3

        with patch.object(usage, "_utc_day", return_value="2026-09-03"):
            self.assertEqual(usage._roll_day(), "2026-09-03")
        self.assertEqual(usage._calls["tool"], 2)

        with patch.object(usage, "_utc_day", return_value="2026-09-04"):
            self.assertEqual(usage._roll_day(), "2026-09-04")

        self.assertEqual(dict(usage._calls), {})
        self.assertEqual(dict(usage._errors), {})
        self.assertEqual(usage._users, set())
        self.assertEqual(usage._unidentified_calls, 0)

    async def test_call_and_error_accounting(self) -> None:
        usage = self._enabled_usage()
        context = self._context("tool")

        async def successful(_context: object) -> object:
            return SimpleNamespace(isError=False)

        async def camel_case_error(_context: object) -> object:
            return SimpleNamespace(isError=True)

        async def snake_case_error(_context: object) -> object:
            return SimpleNamespace(is_error=True)

        async def raises(_context: object) -> object:
            raise ValueError("tool failed")

        with patch("obot_mcp_usage.get_http_headers", return_value={}):
            await usage.on_call_tool(context, successful)
            await usage.on_call_tool(context, camel_case_error)
            await usage.on_call_tool(context, snake_case_error)
            with self.assertRaisesRegex(ValueError, "tool failed"):
                await usage.on_call_tool(context, raises)

        self.assertEqual(usage._calls["tool"], 4)
        self.assertEqual(usage._errors["tool"], 3)
        self.assertEqual(usage._unidentified_calls, 4)

    async def test_cancellation_is_not_counted_as_tool_error(self) -> None:
        usage = self._enabled_usage()
        context = self._context("cancelled-tool")

        async def call_next(_context: object) -> object:
            raise asyncio.CancelledError

        with (
            patch("obot_mcp_usage.get_http_headers", return_value={}),
            self.assertRaises(asyncio.CancelledError),
        ):
            await usage.on_call_tool(context, call_next)

        self.assertEqual(usage._calls["cancelled-tool"], 1)
        self.assertNotIn("cancelled-tool", usage._errors)

    async def test_concurrent_calls_are_accounted_for_exactly(self) -> None:
        usage = self._enabled_usage()
        total_calls = 200

        async def call_next(context: SimpleNamespace) -> object:
            await asyncio.sleep(0)
            return SimpleNamespace(isError=context.sequence % 7 == 0)

        contexts = [
            SimpleNamespace(message=SimpleNamespace(name="tool"), sequence=index)
            for index in range(total_calls)
        ]
        with patch(
            "obot_mcp_usage.get_http_headers",
            return_value={"x-forwarded-email": "alice@example.com"},
        ):
            await asyncio.gather(
                *(usage.on_call_tool(context, call_next) for context in contexts)
            )

        expected_errors = sum(index % 7 == 0 for index in range(total_calls))
        self.assertEqual(usage._calls["tool"], total_calls)
        self.assertEqual(usage._errors["tool"], expected_errors)
        self.assertEqual(len(usage._users), 1)

    async def test_tool_counters_collapse_excess_names(self) -> None:
        usage = self._enabled_usage()

        async def call_next(_context: object) -> object:
            return SimpleNamespace(isError=True)

        with patch("obot_mcp_usage.get_http_headers", return_value={}):
            for index in range(MAX_DAILY_TOOL_COUNTERS + 100):
                await usage.on_call_tool(self._context(f"invalid-{index}"), call_next)

        self.assertEqual(len(usage._calls), MAX_DAILY_TOOL_COUNTERS)
        self.assertEqual(len(usage._errors), MAX_DAILY_TOOL_COUNTERS)
        self.assertEqual(usage._calls[OVERFLOW_TOOL_NAME], 101)
        self.assertEqual(usage._errors[OVERFLOW_TOOL_NAME], 101)

    async def test_oversized_tool_name_uses_overflow_counter(self) -> None:
        usage = self._enabled_usage()
        context = self._context("x" * (MAX_TOOL_NAME_LENGTH + 1))

        async def call_next(_context: object) -> object:
            return SimpleNamespace(isError=False)

        with patch("obot_mcp_usage.get_http_headers", return_value={}):
            await usage.on_call_tool(context, call_next)

        self.assertEqual(dict(usage._calls), {OVERFLOW_TOOL_NAME: 1})
        self.assertEqual(dict(usage._errors), {})

    async def test_daily_user_cardinality_is_capped(self) -> None:
        usage = self._enabled_usage()
        emails = [
            "user-0@example.com",
            "user-1@example.com",
            "user-2@example.com",
            "user-3@example.com",
            "user-0@example.com",
        ]

        async def call_next(_context: object) -> object:
            return SimpleNamespace(isError=False)

        with (
            patch("obot_mcp_usage.MAX_DAILY_USERS", 3),
            patch(
                "obot_mcp_usage.get_http_headers",
                side_effect=({"x-forwarded-email": email} for email in emails),
            ),
        ):
            for _ in emails:
                await usage.on_call_tool(self._context("tool"), call_next)

        expected_hashes = {
            hmac.new(
                b"secret", f"{usage._day}\n{email}".encode(), hashlib.sha256
            ).hexdigest()
            for email in emails[:3]
        }
        self.assertEqual(usage._users, expected_hashes)
        self.assertEqual(usage._calls["tool"], len(emails))


if __name__ == "__main__":
    unittest.main()
