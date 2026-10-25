"""Measured local inference latency; no invented speed claims."""
from __future__ import annotations

import math
import statistics
import time
from collections.abc import Callable
from typing import Any


def benchmark(
    predict: Callable[[dict[str, Any]], Any],
    rows: list[dict[str, Any]],
    *,
    warmups: int = 3,
    repetitions: int = 5,
) -> dict[str, float | int | str]:
    """Sample wall-clock inference after warmup; measures given device only."""
    if not rows or not 0 <= warmups <= 1000 or not 1 <= repetitions <= 100:
        raise ValueError("Need rows, 0..1000 warmups, and 1..100 repetitions")
    for i in range(warmups):
        predict(rows[i % len(rows)])
    times: list[float] = []
    for _ in range(repetitions):
        for row in rows:
            start = time.perf_counter_ns()
            predict(row)
            times.append((time.perf_counter_ns() - start) / 1_000_000)
    ordered = sorted(times)
    p95 = ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)]
    return {
        "kind": "local_observed_inference_latency_not_production_sla",
        "samples": len(times),
        "median_ms": round(statistics.median(times), 6),
        "p95_ms": round(p95, 6),
        "max_ms": round(max(times), 6),
    }
