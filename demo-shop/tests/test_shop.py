"""Demo-shop failure-flag tests (FEATURES F22)."""

import logging
import time

import pytest
from fastapi.testclient import TestClient

from shop import app as shop

ENV_KEYS = (
    "ROLE",
    "DATABASE_URL",
    "FAIL_RATE",
    "CPU_WORK_MS",
    "MEMORY_BALLAST_MB",
    "FAIL_SEED",
    "STARTUP_LOG_MESSAGE",
)


def make(monkeypatch: pytest.MonkeyPatch, **env: str) -> TestClient:
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    async def ok(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr(shop, "db_ping", ok)
    return TestClient(shop.create_app())


def test_fail_rate_one_returns_500(monkeypatch: pytest.MonkeyPatch) -> None:
    with make(monkeypatch, ROLE="orders", DATABASE_URL="postgresql://x", FAIL_RATE="1") as c:
        assert c.get("/orders").status_code == 500
        assert c.get("/healthz").status_code == 200


def test_orders_ok_without_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    with make(monkeypatch, ROLE="orders", DATABASE_URL="postgresql://x") as c:
        assert c.get("/orders").status_code == 200


def test_missing_database_url_exits_1(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit) as e:
        make(monkeypatch, ROLE="orders")
    assert e.value.code == 1


def test_cpu_work_adds_latency(monkeypatch: pytest.MonkeyPatch) -> None:
    with make(monkeypatch, ROLE="orders", DATABASE_URL="postgresql://x", CPU_WORK_MS="80") as c:
        t = time.perf_counter()
        c.get("/orders")
        assert time.perf_counter() - t >= 0.08


def test_metrics_names(monkeypatch: pytest.MonkeyPatch) -> None:
    with make(monkeypatch, ROLE="orders", DATABASE_URL="postgresql://x") as c:
        c.get("/orders")
        body = c.get("/metrics").text
    for name in ("http_requests_total", "http_request_duration_seconds_bucket", "upstream_errors"):
        assert name in body
    assert 'http_requests_total{route="/orders",service="orders",status="200"} 1.0' in body


def test_startup_log_message(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    with (
        caplog.at_level(logging.INFO, logger="shop"),
        make(monkeypatch, ROLE="inventory", STARTUP_LOG_MESSAGE="hello-marker"),
    ):
        pass
    assert "hello-marker" in caplog.text


def test_ballast_allocated(monkeypatch: pytest.MonkeyPatch) -> None:
    with make(monkeypatch, ROLE="inventory", MEMORY_BALLAST_MB="2") as c:
        assert c.get("/healthz").status_code == 200
