"""Minimal optional PySide6 Windows preview, with no implicit packet capture."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

MODEL_STATUS_URL = "http://127.0.0.1:8787/model/status"
ASSESSMENTS_URL = "http://127.0.0.1:8787/assessments?limit=10"


def local_json(url: str) -> dict[str, Any]:
    """Reject arbitrary URLs; limit local response size and connect timeout."""
    if url not in {MODEL_STATUS_URL, ASSESSMENTS_URL}:
        raise ValueError("Only No Hack fixed loopback endpoints allowed")
    with urlopen(url, timeout=0.6) as response:
        payload = response.read(16385)
        if len(payload) > 16384:
            raise ValueError("Local response exceeds size limit")
    result = json.loads(payload.decode("utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Expected JSON object")
    return result


def launch() -> int:
    """Run on demand only. Requires separately installed optional PySide6."""
    from PySide6.QtWidgets import (
        QApplication, QLabel, QPushButton, QVBoxLayout, QWidget,
    )

    app = QApplication.instance() or QApplication([])
    window = QWidget()
    window.setWindowTitle("No Hack — experimental local companion")
    window.resize(620, 450)
    window.setStyleSheet(
        "QWidget { background:#fffaf0; color:#25221a; font-size:14px; } "
        "QPushButton { background:#ffdb4e; border:2px solid #25221a; "
        "border-radius:10px; padding:10px; } "
        "QLabel { padding:8px; }"
    )
    layout = QVBoxLayout(window)
    heading = QLabel("No Hack · experimental network-flow viewer")
    heading.setStyleSheet("font-weight:bold; font-size:20px;")
    layout.addWidget(heading)
    model_text = QLabel("Model not connected")
    assessment_text = QLabel("No network-flow assessments loaded")
    assessment_text.setWordWrap(True)
    refresh = QPushButton("Refresh local model and assessments")
    layout.addWidget(model_text)
    layout.addWidget(refresh)
    layout.addWidget(assessment_text)
    layout.addStretch()

    def refresh_state() -> None:
        try:
            status = local_json(MODEL_STATUS_URL)
            connected = status.get("model_connected") is True
            demo = status.get("synthetic_demo_only") is True
            model_text.setText(
                "Synthetic demonstration model (NOT security validated)"
                if connected and demo
                else "Experimental model connected (external validation pending)"
                if connected
                else "Model not connected"
            )
            data = local_json(ASSESSMENTS_URL)
            items = data.get("items", [])
            lines = []
            if isinstance(items, list):
                for item in items[:10]:
                    if isinstance(item, dict):
                        lines.append(str(item.get("state", "unknown")) + " · " +
                                     str(item.get("risk_score", "n/a")) + "/100")
            assessment_text.setText(
                "\n".join(lines) if lines else "No verified local assessments available"
            )
        except (OSError, URLError, ValueError, json.JSONDecodeError):
            model_text.setText("Model not connected")
            assessment_text.setText("Local service is unavailable")

    refresh.clicked.connect(refresh_state)
    window.show()
    return int(app.exec())
