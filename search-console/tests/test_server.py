from unittest.mock import patch

from app.server import streamable_http_server


@patch("app.server.mcp.run")
def test_server_path_matches_oauth_proxy_target(mock_run):
    streamable_http_server()

    mock_run.assert_called_once_with(
        transport="streamable-http",
        host="0.0.0.0",
        port=9000,
        path="/mcp/google-search-console/",
    )
