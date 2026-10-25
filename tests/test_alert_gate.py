"""Local UI notifications never block network traffic."""
from __future__ import annotations

import pytest

from nohack.monitoring.alerts import LocalAlertGate


def test_bounded_alerts_and_cooldown() -> None:
    gate = LocalAlertGate(cooldown_seconds=10, max_keys=2)
    assert gate.should_notify("a", "NORMAL", 1) is False
    assert gate.should_notify("a", "KNOWN_THREAT", 2) is True
    assert gate.should_notify("a", "KNOWN_THREAT", 3) is False
    assert gate.should_notify("a", "UNCERTAIN", 12) is True
    assert gate.should_notify("b", "NOVEL_ANOMALY", 13) is True
    assert gate.should_notify("c", "UNCERTAIN", 14) is True
    assert len(gate.last_seen) == 2


def test_bad_inputs_fail() -> None:
    gate = LocalAlertGate()
    with pytest.raises(ValueError):
        gate.should_notify("", "KNOWN_THREAT", 1)
    with pytest.raises(ValueError):
        gate.should_notify("k", "INVALID", 2)
