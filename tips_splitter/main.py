"""HTTP API for the tips splitter.

Run locally:  uvicorn tips_splitter.main:app --reload
Docs:         http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import date
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from . import __version__
from .splitter import TipEntry, TipSplitError, split_period

# Structured (JSON) logs: easy to search later in CloudWatch (Phase 2).
logger = logging.getLogger("tips_splitter")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="Tips Splitter API",
    description="Splits each day's tips equally among the people who worked that day.",
    version=__version__,
)


class TipEntryIn(BaseModel):
    date: date
    amount: Decimal = Field(ge=0, decimal_places=2, examples=["45.50"])
    workers: list[str] = Field(min_length=1, examples=[["Alex", "Bia", "Caio"]])


class SplitRequest(BaseModel):
    entries: list[TipEntryIn] = Field(min_length=1)


class DayOut(BaseModel):
    date: date
    amount: Decimal
    shares: dict[str, Decimal]


class SplitResponse(BaseModel):
    total: Decimal
    per_person: dict[str, Decimal]
    days_worked: dict[str, int]
    days: list[DayOut]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    logger.info(
        json.dumps(
            {
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        )
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    """Used by the load balancer / monitoring to check the app is alive."""
    return {"status": "ok", "version": __version__}


@app.post("/split", response_model=SplitResponse)
def split(request: SplitRequest) -> SplitResponse:
    entries = [TipEntry(day=e.date, amount=e.amount, workers=tuple(e.workers)) for e in request.entries]
    try:
        report = split_period(entries)
    except TipSplitError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SplitResponse(
        total=report.total,
        per_person=report.per_person,
        days_worked=report.days_worked,
        days=[DayOut(date=d.day, amount=d.amount, shares=d.shares) for d in report.days],
    )
