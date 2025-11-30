# Obot Google Groups MCP Server
- Obot Google Groups mcp server for managing Google Workspace groups and members.
- supports streamable HTTP
- tools of this mcp server expect `cred_token`(access_token of google oauth) as part of the tool input.

## Quickstart
Export (Google's) Oauth Client ID and Secret for Oauth Proxy
```bash
export OAUTH_CLIENT_ID=xxx
export OAUTH_CLIENT_SECRET=xxx
```

also export an base64-encoded 32-byte AES-256 key:
```bash
export ENCRYPTION_KEY=xxx
```

### Docker-compose
```bash
docker-compose up
```

### Using uv (development)
```bash
uv sync
```

## Run the Server

### Using uv
```bash
uv run python -m app.server
```

### Integration Testing

#### Get Your Access Token
This MCP server assumes Obot will take care of the Oauth2.0 flow and supply an access token. To test locally or without Obot, you need to get an access token by yourself. You can use [postman workspace](https://blog.postman.com/how-to-access-google-apis-using-oauth-in-postman/) to create and manage your tokens.

#### Required OAuth Scopes
- `https://www.googleapis.com/auth/admin.directory.group`
- `https://www.googleapis.com/auth/admin.directory.group.member`
- `https://www.googleapis.com/auth/admin.directory.domain.readonly` (for domain listing)

