"""Post-hoc calibration diagnostics need independently verified labels."""
from __future__ import annotations

import pytest

pytest.importorskip("numpy")
from nohack.evaluation.calibration import calibration_bins


def test_calibration_math() -> None:
    bins = calibration_bins([0, 1], [0.1, 0.9], bins=5)
    assert bins["n"] == 2
    assert bins["expected_calibration_error"] == pytest.approx(0.1)
    with pytest.raises(ValueError):
        calibration_bins([0, 1], [0.1, float("nan")])
