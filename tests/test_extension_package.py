"""Extension packaging should contain only audited source files."""
from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path


def test_package_only_allowlisted_files(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts/package_extension.py"
    spec = importlib.util.spec_from_file_location("pkg_ext", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    src = Path(__file__).resolve().parents[1] / "extension"
    output = module.package(src, tmp_path / "extension.zip")
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == set(module.EXTENSION_FILES)
        assert "manifest.json" in archive.namelist()
