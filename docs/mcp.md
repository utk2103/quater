# MCP

Quater can expose selected HTTP routes as MCP tools.

The route stays a normal API. MCP is another way to call it. That is the design:
one handler, one auth rule, one validation path.

## Configure MCP

```python
from quater import Quater

app = Quater(
    mcp_docs_path="/mcp/docs",
    mcp_allowed_origins=["http://localhost:3000"],
)
```

The JSON-RPC endpoint is fixed at `POST /mcp`.

The docs page defaults to `/mcp/docs`. Set `mcp_docs_path=None` to turn off the
human page. The MCP endpoint itself stays available.

## Expose A Tool

Routes are not tools unless they opt in:

```python
@app.get("/users/{id:int}", tool=True, description="Fetch one user by id.")
async def get_user(id: int) -> dict[str, int]:
    return {"id": id}
```

Descriptions are required. Use `description=` or a handler docstring. This is
not decoration for humans only. It is the text an agent sees in `tools/list`, so
it needs to say what the tool is for.

This still works as HTTP:

```text
GET /users/123
```

It also appears in MCP discovery:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

## Client Lifecycle

Clients start with `initialize`:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "my-client", "version": "1.0.0"}
  }
}
```

Quater responds with the negotiated protocol version, server metadata, and tool
capability. After that, clients may send `notifications/initialized`.

For later requests, clients may include `MCP-Protocol-Version`. Unsupported
versions are rejected with `400 Bad Request`.

Tool calls look like this:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_user",
    "arguments": {"id": 123}
  }
}
```

## Request Context

The same handler can tell how it was called.

```python
from quater import Request


@app.get("/users/{id:int}", tool=True, description="Fetch one user by id.")
async def get_user(id: int, request: Request) -> dict[str, object]:
    return {
        "id": id,
        "source": request.context.source,
        "tool": request.context.tool_name,
    }
```

Normal HTTP calls use:

```python
request.context.source == "api"
request.context.tool_name is None
```

MCP tool calls use:

```python
request.context.source == "tool"
request.context.tool_name == "get_user"
```

## Auth

MCP tool calls use the auth hook attached to the route.

```python
@app.get(
    "/users/{id:int}",
    tool=True,
    auth=authenticate,
    description="Fetch one protected user by id.",
)
async def get_user(id: int, request: Request) -> dict[str, object]:
    assert request.auth is not None
    return {"id": id, "subject": request.auth.subject}
```

A protected HTTP route stays protected when exposed as a tool. A public route
stays public. No second auth system hiding off to the side.

## Input And Output Docs

Quater generates `inputSchema` from path parameters, query parameters, and one
JSON body parameter. Required fields follow the handler signature and body model.

`GET /mcp/docs` shows the same tool data in a human page:

- tool name
- description
- auth marker
- HTTP route
- pretty JSON input schema
- pretty JSON output schema when the return annotation is useful
- example `tools/call` request

That page is for developers. MCP clients should use `tools/list`.

## Auditing

Pass `mcp_audit` to receive sanitized tool-call events:

```python
from quater import ToolAuditEvent


async def audit(event: ToolAuditEvent) -> None:
    print(event.tool_name, event.subject, event.success)


app = Quater(mcp_audit=audit)
```

Arguments are redacted before they reach the hook.

## Implemented Now

- `POST /mcp`
- JSON-RPC request/response
- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`
- `GET /mcp/docs`
- auth parity with HTTP
- origin validation
- protocol version header validation
- audit hook support

## Not Yet

- SSE streaming
- resumability
- sessions
- server-to-client notifications
- prompts
- resources
- stdio transport
- full MCP SDK adapter
