from __future__ import annotations

import logging

import pytest

from quater import Quater, Request


@pytest.mark.asyncio
async def test_request_logging_emits_access_record(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = Quater()

    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    caplog.set_level(logging.INFO, logger="quater.access")

    response = await app.handle(
        Request(method="GET", path="/health", client="127.0.0.1")
    )

    assert response.status_code == 200
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.name == "quater.access"
    assert "GET /health -> 200" in record.getMessage()
    assert "client=127.0.0.1" in record.getMessage()
    assert "source=api" in record.getMessage()


@pytest.mark.asyncio
async def test_request_logging_can_be_disabled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = Quater(request_logging=False)

    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    caplog.set_level(logging.INFO, logger="quater.access")

    response = await app.handle(Request(method="GET", path="/health"))

    assert response.status_code == 200
    assert caplog.records == []
