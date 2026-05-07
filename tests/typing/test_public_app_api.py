from __future__ import annotations

from typing import assert_type

from quater import AuthContext, AuthRequest, Quater
from quater.request import Request
from quater.response import Response
from quater.typing import Authenticate, LifespanHook


async def authenticate(ctx: AuthRequest) -> AuthContext | None:
    token = ctx.headers.get("authorization")
    if token is None:
        return None
    return AuthContext(subject=token)


app = Quater(allowed_hosts=["api.example.com"])


@app.get("/me", auth=authenticate)
async def me(request: Request) -> dict[str, str]:
    assert request.auth is not None
    return {"subject": request.auth.subject}


@app.on_startup
async def startup() -> None:
    return None


@app.on_shutdown
async def shutdown() -> None:
    return None


async def dispatch_contract() -> None:
    response = await app.handle(Request(method="GET", path="/missing"))
    assert_type(response, Response)


assert_type(app.routes[0].auth, Authenticate | None)
assert_type(startup, LifespanHook)
assert_type(shutdown, LifespanHook)
assert_type(app.config.allowed_hosts, tuple[str, ...])
