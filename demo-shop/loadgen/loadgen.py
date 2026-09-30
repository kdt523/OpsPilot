"""Load generator: ~5 req/s (+/-20% jitter) against the gateway; prints a summary every 30 s."""

from __future__ import annotations

import asyncio
import os
import random
import time

import httpx

TARGET = os.environ.get("TARGET_URL", "http://gateway:8000/checkout")
RATE = float(os.environ.get("RATE", "5"))


class Stats:
    """Counters for one 30 s reporting window."""

    def __init__(self) -> None:
        self.ok = 0
        self.err = 0
        self.lat: list[float] = []

    def p95(self) -> float:
        """95th percentile latency in ms (0 if empty)."""
        if not self.lat:
            return 0.0
        s = sorted(self.lat)
        return s[min(len(s) - 1, int(len(s) * 0.95))]


async def one(client: httpx.AsyncClient, stats: Stats) -> None:
    start = time.perf_counter()
    try:
        ok = (await client.get(TARGET)).status_code < 500
    except Exception:  # noqa: BLE001
        ok = False
    if ok:
        stats.ok += 1
    else:
        stats.err += 1
    stats.lat.append((time.perf_counter() - start) * 1000)


async def main() -> None:
    stats = Stats()
    last = time.monotonic()
    tasks: set[asyncio.Task[None]] = set()
    async with httpx.AsyncClient(timeout=2) as client:
        while True:
            t = asyncio.create_task(one(client, stats))
            tasks.add(t)
            t.add_done_callback(tasks.discard)
            await asyncio.sleep((1 / RATE) * random.uniform(0.8, 1.2))
            if time.monotonic() - last >= 30:
                print(f"ok={stats.ok} err={stats.err} p95_ms={stats.p95():.0f}", flush=True)
                stats = Stats()
                last = time.monotonic()


if __name__ == "__main__":
    asyncio.run(main())
