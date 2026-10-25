"""Aggregate bounded local flow assessment states; never accuracy without labels."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

VALID = frozenset({"NORMAL", "KNOWN_THREAT", "NOVEL_ANOMALY", "UNCERTAIN"})


def summarize_assessments(items: Iterable[Mapping[str, Any]]) -> dict[str, object]:
    counts: Counter[str] = Counter()
    risks: list[int] = []
    for item in items:
        state = item.get("state")
        risk = item.get("risk_score")
        if state not in VALID or type(risk) is not int or not 0 <= risk <= 100:
            raise ValueError("Invalid assessment record")
        counts[str(state)] += 1
        risks.append(risk)
    return {
        "kind": "unlabeled_local_assessment_summary",
        "rows": len(risks),
        "by_state": {state: counts[state] for state in sorted(VALID)},
        "mean_risk_index": sum(risks) / len(risks) if risks else None,
        "mean_is_probability": False,
        "detection_accuracy_not_measured": True,
    }
