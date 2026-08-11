import asyncio
from unittest.mock import ANY, patch

from app import server
from httpx import ASGITransport, AsyncClient


@patch("app.server.mcp.run")
def test_server_configures_canonical_path_and_compatibility_middleware(mock_run):
    server.streamable_http_server()

    mock_run.assert_called_once_with(
        transport="streamable-http",
        host="0.0.0.0",
        port=server.PORT,
        path=server.MCP_PATH,
        middleware=ANY,
    )

    middleware = mock_run.call_args.kwargs["middleware"]
    assert len(middleware) == 1
    assert middleware[0].cls is server.LegacyTrailingSlashMiddleware
    assert middleware[0].kwargs == {"path": server.MCP_PATH}


@patch("app.server.mcp.run")
def test_mcp_endpoint_accepts_trailing_slash_variants_without_redirect(mock_run):
    server.streamable_http_server()
    config = mock_run.call_args.kwargs
    app = server.mcp.http_app(
        transport=config["transport"],
        path=config["path"],
        middleware=config["middleware"],
    )

    async def exercise_endpoint():
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                return [
                    await client.post(
                        path,
                        content=b"{}",
                        headers={"content-type": "application/json"},
                    )
                    for path in (
                        server.MCP_PATH,
                        f"{server.MCP_PATH}/",
                        f"{server.MCP_PATH}///",
                    )
                ]

    responses = asyncio.run(exercise_endpoint())

    assert len({response.status_code for response in responses}) == 1
    for response in responses:
        assert not 300 <= response.status_code < 400
        assert "location" not in response.headers
