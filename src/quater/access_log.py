"""Request access logging."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from quater.request import Request
from quater.response import Response

LOGGER_NAME = "quater.access"


@dataclass(slots=True, frozen=True)
class AccessLogRecord:
    method: str
    path: str
    status_code: int
    duration_ms: float
    client: str | None
    source: str
    tool_name: str | None


def build_access_log_record(
    request: Request,
    response: Response,
    *,
    duration_ms: float,
) -> AccessLogRecord:
    return AccessLogRecord(
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client=request.client,
        source=request.context.source,
        tool_name=request.context.tool_name,
    )


def log_access(record: AccessLogRecord) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    logger.info(
        "%s %s -> %s %.3fms client=%s source=%s tool=%s",
        record.method,
        record.path,
        record.status_code,
        record.duration_ms,
        record.client or "-",
        record.source,
        record.tool_name or "-",
    )

