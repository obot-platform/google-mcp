import asyncio
from unittest import TestCase
from unittest.mock import ANY, patch

from app import server


class StreamableHTTPServerTest(TestCase):
    @patch("app.server.mcp.run")
    def test_server_configures_canonical_path_and_compatibility_middleware(
        self, mock_run
    ):
        server.streamable_http_server()

        mock_run.assert_called_once_with(
            transport="streamable-http",
            host="0.0.0.0",
            port=server.PORT,
            path=server.MCP_PATH,
            middleware=ANY,
        )

        middleware = mock_run.call_args.kwargs["middleware"]
        self.assertEqual(len(middleware), 1)
        self.assertIs(middleware[0].cls, server.LegacyTrailingSlashMiddleware)
        self.assertEqual(middleware[0].kwargs, {"path": server.MCP_PATH})

    def test_legacy_trailing_slash_is_rewritten_without_redirect(self):
        seen_paths = []

        async def app(scope, receive, send):
            seen_paths.append((scope["path"], scope["raw_path"]))

        async def exercise_middleware():
            middleware = server.LegacyTrailingSlashMiddleware(
                app, path=server.MCP_PATH
            )
            for path in (server.MCP_PATH, f"{server.MCP_PATH}/", f"{server.MCP_PATH}//"):
                await middleware(
                    {"type": "http", "path": path, "raw_path": path.encode()},
                    None,
                    None,
                )

        asyncio.run(exercise_middleware())

        expected = (server.MCP_PATH, server.MCP_PATH.encode())
        self.assertEqual(seen_paths, [expected, expected, expected])
