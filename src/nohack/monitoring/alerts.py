"""Conservative notification gate; never blocks traffic or claims safety."""

from __future__ import annotations

from dataclasses import dataclass, field

STATES = frozenset({"NORMAL", "KNOWN_THREAT", "NOVEL_ANOMALY", "UNCERTAIN"})


@dataclass
class LocalAlertGate:
    """Bounded deduplication by opaque caller-supplied key.

    Timestamps are caller monotonic seconds. This is UI notification logic
    only; source IPs, payloads and browser tab IDs must not be used as keys.
    """

    cooldown_seconds: float = 30.0
    max_keys: int = 256
    last_seen: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.cooldown_seconds <= 86400 or not 1 <= self.max_keys <= 10000:
            raise ValueError("Invalid cooldown/max_keys policy")

    def should_notify(self, key: str, state: str, now_seconds: float) -> bool:
        if not key or len(key) > 128 or state not in STATES:
            raise ValueError("Invalid opaque key or assessment state")
        import math

        if not math.isfinite(now_seconds) or now_seconds < 0:
            raise ValueError("Invalid monotonic timestamp")
        if state == "NORMAL":
            return False
        previous = self.last_seen.get(key)
        if previous is not None and 0 <= now_seconds - previous < self.cooldown_seconds:
            return False
        if previous is not None and now_seconds < previous:
            return False
        if len(self.last_seen) >= self.max_keys and key not in self.last_seen:
            oldest = min(self.last_seen, key=self.last_seen.__getitem__)
            del self.last_seen[oldest]
        self.last_seen[key] = now_seconds
        return True
