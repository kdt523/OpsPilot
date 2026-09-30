"""Demo shop: one FastAPI codebase; the ROLE env var selects gateway | orders | inventory.

Failure knobs (FAIL_RATE, MEMORY_BALLAST_MB, CPU_WORK_MS, STARTUP_LOG_MESSAGE, missing
DATABASE_URL) exist so chaos scenarios can break the system in realistic ways.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

ROLES = ("gateway", "orders", "inventory")
BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout
)
log = logging.getLogger("shop")


def fatal(message: str) -> None:
    """Log a FATAL line and exit 1 (shows up as CrashLoopBackOff)."""
    log.critical("FATAL %s", message)
    raise SystemExit(1)


async def db_ping(url: str) -> None:
    """SELECT 1 against Postgres."""
    conn = await asyncpg.connect(url, timeout=2)
    try:
        await conn.fetchval("SELECT 1")
    finally:
        await conn.close()


async def db_ping_with_retries(url: str, attempts: int = 5, delay: float = 2.0) -> None:
    """Check the DB once at startup: 5 tries, 2 s apart."""
    for i in range(1, attempts + 1):
        try:
            await db_ping(url)
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("db check %d/%d failed: %s", i, attempts, exc)
            if i < attempts:
                await asyncio.sleep(delay)
    fatal("database unreachable after retries")


def busy_loop(ms: float) -> None:
    """Burn CPU for `ms` milliseconds."""
    end = time.perf_counter() + ms / 1000
    while time.perf_counter() < end:
        pass


def create_app() -> FastAPI:
    """Build the app for the configured ROLE."""
    role = os.environ.get("ROLE", "gateway")
    if role not in ROLES:
        fatal(f"invalid ROLE {role!r}")
    database_url = os.environ.get("DATABASE_URL")
    if role == "orders" and not database_url:
        fatal("missing required config DATABASE_URL")

    fail_rate = float(os.environ.get("FAIL_RATE", "0"))
    cpu_ms = float(os.environ.get("CPU_WORK_MS", "0"))
    ballast_mb = int(os.environ.get("MEMORY_BALLAST_MB", "0"))
    rng = random.Random(os.environ.get("FAIL_SEED"))
    orders_url = os.environ.get("ORDERS_URL", "http://orders:8000")
    inventory_url = os.environ.get("INVENTORY_URL", "http://inventory:8000")
    redis_url = os.environ.get("REDIS_URL", "redis://redis-demo:6379/0")

    registry = CollectorRegistry()
    requests_total = Counter(
        "http_requests", "HTTP requests", ["service", "route", "status"], registry=registry
    )
    duration = Histogram(
        "http_request_duration_seconds",
        "Request duration",
        ["service", "route"],
        buckets=BUCKETS,
        registry=registry,
    )
    upstream_errors = Counter(
        "upstream_errors", "Upstream call errors", ["service", "target"], registry=registry
    )

    ballast: list[bytearray] = []

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if msg := os.environ.get("STARTUP_LOG_MESSAGE"):
            log.info(msg)
        if ballast_mb:
            block = bytearray(ballast_mb * 1024 * 1024)
            for i in range(0, len(block), 4096):  # touch every page so RSS really grows
                block[i] = 1
            ballast.append(block)
        if role == "orders":
            assert database_url
            await db_ping_with_retries(database_url)
        log.info(
            "started role=%s fail_rate=%s cpu_ms=%s ballast_mb=%s",
            role,
            fail_rate,
            cpu_ms,
            ballast_mb,
        )
        yield

    app = FastAPI(title=f"demo-shop-{role}", lifespan=lifespan)

    @app.middleware("http")
    async def observe(request: Request, call_next: Any) -> Response:
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            log.exception("unhandled error")
            response = JSONResponse({"error": "internal"}, status_code=500)
        elapsed = time.perf_counter() - start
        route = getattr(request.scope.get("route"), "path", request.url.path)
        if route not in ("/metrics", "/healthz"):
            requests_total.labels(role, route, str(response.status_code)).inc()
            duration.labels(role, route).observe(elapsed)
        log.info(
            "%s %s %s %.1f", request.method, request.url.path, response.status_code, elapsed * 1000
        )
        return response

    def maybe_fail() -> Response | None:
        if fail_rate and rng.random() < fail_rate:
            return JSONResponse({"error": "injected failure"}, status_code=500)
        return None

    @app.get("/healthz")
    async def healthz() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    if role == "gateway":

        @app.get("/checkout")
        async def checkout() -> Response:
            if cpu_ms:
                await asyncio.to_thread(busy_loop, cpu_ms)
            if (failure := maybe_fail()) is not None:
                return failure
            out: dict[str, Any] = {}
            targets = (("orders", f"{orders_url}/orders"), ("inventory", f"{inventory_url}/stock"))
            async with httpx.AsyncClient(timeout=2) as client:
                for target, url in targets:
                    try:
                        r = await client.get(url)
                        r.raise_for_status()
                        out[target] = r.json()
                    except Exception as exc:  # noqa: BLE001
                        upstream_errors.labels(role, target).inc()
                        log.error("upstream error target=%s error=%s", target, exc)
                        return JSONResponse({"error": f"upstream {target} failed"}, status_code=502)
            return JSONResponse(out)

    elif role == "orders":

        @app.get("/orders")
        async def orders() -> Response:
            if cpu_ms:
                await asyncio.to_thread(busy_loop, cpu_ms)
            if (failure := maybe_fail()) is not None:
                return failure
            assert database_url
            try:
                await db_ping(database_url)
            except Exception as exc:  # noqa: BLE001
                log.error("database error: %s", exc)
                return JSONResponse({"error": "database unavailable"}, status_code=500)
            return JSONResponse({"orders": [{"id": 1, "item": "widget", "qty": 2}]})

    else:

        @app.get("/stock")
        async def stock() -> Response:
            if cpu_ms:
                await asyncio.to_thread(busy_loop, cpu_ms)
            if (failure := maybe_fail()) is not None:
                return failure
            try:
                client = aioredis.from_url(redis_url, socket_timeout=1, socket_connect_timeout=1)
                try:
                    count = await client.incr("stock:hits")
                finally:
                    await client.aclose()
            except Exception as exc:  # noqa: BLE001
                log.error("redis error: %s", exc)
                return JSONResponse({"error": "redis unavailable"}, status_code=500)
            return JSONResponse({"stock": {"widget": 42}, "hits": count})

    return app
