# Google MCP Servers

Local development and testing instructions for the Google MCP servers. Each server uses a Google OAuth Desktop client token forwarded by MCP Inspector.

## Prerequisites

- Python 3.13 and `uv`
- Google Cloud CLI (`gcloud`)
- Node.js 22.19 or later for MCP Inspector 2.0
- A Google account authorized to use the test OAuth client

Verify the local tools:

```bash
python3 --version
uv --version
gcloud --version
node --version
```

## Available Servers

All servers use port `9000` by default and expose `/health`. Set `PORT` when running more than one server at once.

| Server | Directory | MCP path | Google API and OAuth scope |
| --- | --- | --- | --- |
| Google Analytics | `analytics` | `/mcp/google-analytics` | Google Analytics Admin and Data APIs; `https://www.googleapis.com/auth/analytics.edit` |
| Google Calendar | `calendar` | `/mcp/google-calendar` | Google Calendar API; `https://www.googleapis.com/auth/calendar` |
| Google Docs | `docs` | `/mcp/google-docs` | Google Docs and Drive APIs; `https://www.googleapis.com/auth/documents`, `https://www.googleapis.com/auth/drive` |
| Google Drive | `drive` | `/mcp/google-drive` | Google Drive API; `https://www.googleapis.com/auth/drive` |
| Gmail | `gmail` | `/mcp/gmail` | Gmail API; `https://mail.google.com/` |
| Google Groups | `group` | `/mcp/google-groups` | Admin SDK API; `https://www.googleapis.com/auth/admin.directory.group`, `https://www.googleapis.com/auth/admin.directory.group.member`, `https://www.googleapis.com/auth/admin.directory.domain.readonly` |
| Google Search Console | `search-console` | `/mcp/google-search-console` | Search Console API; `https://www.googleapis.com/auth/webmasters` |
| Google Sheets | `sheets` | `/mcp/google-sheets` | Google Sheets API; `https://www.googleapis.com/auth/spreadsheets` |

The Groups server requires a Google Workspace account with the necessary Admin SDK privileges. The other servers require an account authorized for the target Google resources.

## Configure Google Cloud

Use one Google Cloud project for all following steps.

1. Enable the Google APIs required by the server from the table above. Enable the [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) as well when testing Drive or Docs.
2. Configure the [OAuth audience](https://console.cloud.google.com/auth/audience).
   - For an organization-owned project limited to organization accounts, select `Internal` when available.
   - Otherwise select `External`, keep the app in `Testing`, and add the testing Google account under `Test users`.
3. Add the OAuth scopes required by the server from the table above in [OAuth scopes](https://console.cloud.google.com/auth/scopes). For example, the Drive server requires:

   ```text
   https://www.googleapis.com/auth/drive
   ```

   The Drive server supports listing, reading, modifying, deleting, sharing, permission management, and shared-drive management, so it requires full Drive access.
4. Create a `Desktop app` client in [OAuth clients](https://console.cloud.google.com/auth/clients) and download its client JSON.

Keep the downloaded JSON outside this repository. It contains OAuth client credentials and must not be committed.

## Obtain A Local Access Token

The default `gcloud` OAuth client cannot request non-Cloud scopes such as full Google Drive access. Log in with the downloaded Desktop client JSON, adding the scope or scopes for the server you intend to test. For example, this obtains a Drive token:

```bash
gcloud auth application-default login \
  --client-id-file="$HOME/Downloads/client_secret_<client-id>.apps.googleusercontent.com.json" \
  --scopes="openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/cloud-platform"
```

Replace the placeholder filename with the downloaded file. The `cloud-platform` scope is also required for a successful local Application Default Credentials login.

Choose an account eligible for the configured internal audience or listed as an external test user, then verify token generation:

```bash
gcloud auth application-default print-access-token
```

Access tokens are short-lived. Restart Inspector to use a fresh token after expiration.

To test another server, replace the Drive scope in the login command with its scope from the table. Include multiple comma-separated scopes for a server that lists more than one. For example, Google Docs requires both the Documents and Drive scopes. Repeat this login whenever you change the requested scopes; it overwrites existing Application Default Credentials.

For Gmail, request its full Gmail scope before restarting Inspector:

```bash
gcloud auth application-default login \
  --client-id-file="$HOME/Downloads/client_secret_<client-id>.apps.googleusercontent.com.json" \
  --scopes="openid,https://www.googleapis.com/auth/userinfo.email,https://mail.google.com/,https://www.googleapis.com/auth/cloud-platform"
```

Enable the Gmail API in the same Google Cloud project that owns the downloaded OAuth client. Use the project ID, not the currently configured `gcloud` project:

```bash
gcloud services enable gmail.googleapis.com --project="<oauth-client-project-id>"
```

Alternatively, enable it in the [Google Cloud console](https://console.cloud.google.com/apis/library/gmail.googleapis.com). Allow a few minutes for the change to propagate before retrying the tool.

## Start Google Drive

From the repository root:

```bash
cd drive
uv sync --frozen
uv run python -m app.server
```

The local endpoints are:

```text
Health: http://localhost:9000/health
MCP:    http://localhost:9000/mcp/google-drive
```

From another terminal, verify the server:

```bash
curl http://localhost:9000/health
```

Expected response:

```json
{"status":"healthy"}
```

Do not add a trailing slash to the local MCP URL.

## Connect MCP Inspector

The server reads its Google credential from the `X-Forwarded-Access-Token` HTTP header. The declared `GOOGLE_OAUTH_TOKEN` environment variable is not used.

In a separate terminal, run:

```bash
npx -y @modelcontextprotocol/inspector@2.0.0 \
  --transport http \
  --server-url "http://localhost:9000/mcp/google-drive" \
  --header "X-Forwarded-Access-Token: $(gcloud auth application-default print-access-token)"
```

Inspector opens at <http://localhost:6274>. Connect, open `Tools`, and start with the read-only `list_files` tool:

```json
{
  "max_results": 5
}
```

Avoid write or delete tools unless using disposable test data. The stdio entry point does not support authenticated tool testing: tool calls require the forwarded access-token header.

## Run Another Server

From the repository root, synchronize the selected component and start it. Use a distinct `PORT` for each concurrently running server:

```bash
cd <component>
uv sync --frozen
PORT=9001 uv run python -m app.server
```

Gmail has a different Python module name:

```bash
cd gmail
uv sync --frozen
PORT=9001 uv run python -m obot_gmail_mcp.server
```

Connect Inspector using the selected component's MCP path from the table. For example, to test Calendar on port `9001`:

```bash
npx -y @modelcontextprotocol/inspector@2.0.0 \
  --transport http \
  --server-url "http://localhost:9001/mcp/google-calendar" \
  --header "X-Forwarded-Access-Token: $(gcloud auth application-default print-access-token)"
```

All components read the token from `X-Forwarded-Access-Token`; do not use a `GOOGLE_OAUTH_TOKEN` environment variable for local Inspector testing. Confirm the process is ready before connecting:

```bash
curl http://localhost:9001/health
```

## Hosted Dev Endpoint

The hosted endpoint uses its deployed MCP OAuth proxy rather than the downloaded Desktop client JSON:

```bash
npx -y @modelcontextprotocol/inspector@2.0.0 \
  --transport http \
  --server-url "https://dev-google-drive-mcp.obot.ai/mcp/"
```

Click `Connect` and complete Google consent. An initial HTTP 401 before authentication is expected.

## Optional Local OAuth Proxy

[`drive/docker-compose.yml`](drive/docker-compose.yml) runs the MCP server, PostgreSQL, and OAuth proxy together. It requires a Google OAuth `Web application` client with this authorized redirect URI:

```text
http://localhost:8080/callback
```

This Web client is separate from the Desktop client used by `gcloud`. Export its credentials without storing them in the repository:

```bash
export OAUTH_CLIENT_ID="<web-client-id>"
export OAUTH_CLIENT_SECRET="<web-client-secret>"
cd drive
docker compose up --build
```

Then connect Inspector to:

```bash
npx -y @modelcontextprotocol/inspector@2.0.0 \
  --transport http \
  --server-url "http://localhost:8080/mcp"
```

Prefer the direct forwarded-token setup for initial testing. The Compose file uses the mutable `mcp-oauth-proxy:master` image and an older proxy configuration style, which can cause unrelated compatibility failures.

## Troubleshooting

### `This app is blocked`

- Include `--client-id-file` in the login command; the default `gcloud` OAuth client cannot request Drive scope.
- Confirm the account is a test user or eligible for the internal audience.
- For managed Google Workspace accounts, an administrator might need to trust the OAuth client under `Security > Access and data control > API controls > Manage Third-Party App Access`.
- Test with a personal Google account added as a test user to isolate Workspace policy from application configuration.

### `No access token found in headers`

Reconnect Inspector using the `X-Forwarded-Access-Token` argument above. `GOOGLE_OAUTH_TOKEN` currently has no effect.

### Google API Reports Insufficient Scopes

Repeat `gcloud auth application-default login` with the custom client and exact scope or scopes for the server being tested. This overwrites existing Application Default Credentials.

### Local Server Fails During Import

If `FastMCP()` reports that it no longer accepts `on_duplicate_tools`, apply the compatibility fix in [`HANDOFF.md`](HANDOFF.md).

### Local MCP Endpoint Returns 404

Use exactly `http://localhost:9000/mcp/google-drive`, without a trailing slash, and first confirm that the health endpoint succeeds.
