"""Static structural checks for educational notebooks without private data."""

from __future__ import annotations

import json
from pathlib import Path


def test_five_learning_notebooks_compile() -> None:
    notebooks = Path(__file__).resolve().parents[1] / "notebooks"
    for number in range(1, 6):
        candidates = sorted(notebooks.glob(f"{number:02d}_*.ipynb"))
        assert len(candidates) == 1, f"Missing learning stage {number}"
        notebook = json.loads(candidates[0].read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        assert notebook["cells"][0]["cell_type"] == "markdown"
        for index, cell in enumerate(notebook["cells"]):
            assert cell["cell_type"] in {"markdown", "code"}
            if cell["cell_type"] == "code":
                compile(
                    "".join(cell["source"]), f"{candidates[0].name}:cell{index}", "exec"
                )
                assert cell["outputs"] == []
