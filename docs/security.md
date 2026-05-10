# Security

Quater runs security checks before auth, route handlers, and MCP tool lookup.
That order matters. Bad hosts, oversized bodies, and invalid MCP origins should
not reach user code.

## Response Headers

Strict mode is the default. It adds baseline headers to handler responses,
framework errors, auth failures, 404s, 405s, and MCP responses:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: same-origin`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security` on HTTPS requests
- `Content-Security-Policy` when configured

Use `security="off"` only for controlled local or embedded cases.

## Hosts And Proxies

Use `allowed_hosts` to reject unexpected Host headers:

```python
app = Quater(allowed_hosts=["api.example.com"])
```

Use `trusted_proxies` only for proxy IPs or CIDR ranges you control:

```python
app = Quater(
    allowed_hosts=["api.example.com"],
    trusted_proxies=["10.0.0.0/8"],
)
```

Forwarded host and scheme headers are ignored unless the client IP matches a
trusted proxy.

## Body Limits

`max_body_size` defaults to `2mb` and applies before JSON decoding:

```python
app = Quater(max_body_size="2mb")
```

If `Content-Length` is larger than the limit, Quater rejects the request before
reading the stream.

## Auth

Quater does not ship a user system. You write an auth hook and attach it to the
routes that need it.

```python
from quater import AuthContext, AuthRequest, Quater, Request

app = Quater()


async def authenticate(ctx: AuthRequest) -> AuthContext | None:
    if ctx.headers.get("authorization") != "Bearer demo-token":
        return None
    return AuthContext(subject="demo-user")


@app.get("/me", auth=authenticate)
async def me(request: Request) -> dict[str, str]:
    assert request.auth is not None
    return {"subject": request.auth.subject}
```

Returning `None` gives `401 Unauthorized`. Routes without `auth=` stay public.
The same hook protects normal HTTP calls and MCP tool calls.

`AuthRequest.context.source` is `"api"` for HTTP and `"tool"` for MCP
`tools/call`.

## CORS And MCP Origins

Use `CORSConfig` for browser CORS headers:

```python
from quater import CORSConfig, Quater

app = Quater(
    cors=CORSConfig(
        allowed_origins=("https://app.example.com",),
        allow_credentials=True,
    )
)
```

MCP origin validation uses `mcp_allowed_origins` first. If that is empty and CORS
is configured, Quater uses the CORS origins for MCP too.

```python
app = Quater(
    mcp_allowed_origins=["https://app.example.com"],
)
```

Invalid MCP origins are rejected before auth and before tool lookup.

## Documentation Endpoints

Docs are public endpoints. That is useful in development and sometimes fine in
production. It is not always fine.

Defaults:

- `/docs` for Swagger UI.
- `/openapi.json` for OpenAPI JSON.
- `/mcp/docs` for human-readable MCP tool docs.

Disable them when route or tool metadata should not be public:

```python
app = Quater(
    docs_path=None,
    openapi_path=None,
    mcp_docs_path=None,
)
```

If `docs_path` is enabled, `openapi_path` must also be enabled.

## Signed Cookies

`SignedCookieSigner` signs small cookie values with HMAC and supports fallback
secrets for rotation:

```python
from quater import SignedCookieSigner

signer = SignedCookieSigner("new-secret", fallback_secrets=["old-secret"])
value = signer.sign("user_123")
subject = signer.verify(value)
```
