from unittest.mock import patch

from app import server


@patch("app.server.mcp.run")
def test_server_path_matches_oauth_proxy_target(mock_run):
    server.streamable_http_server()

    mock_run.assert_called_once_with(
        transport="streamable-http",
        host="0.0.0.0",
        port=server.PORT,
        path=server.MCP_PATH,
    )
