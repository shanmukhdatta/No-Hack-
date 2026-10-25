"""Create a reproducible unpacked-extension ZIP; not a Web Store release."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

EXTENSION_FILES = (
    "manifest.json",
    "background.js",
    "logic.mjs",
    "popup.html",
    "dashboard.html",
    "styles.css",
    "ui.js",
)


def package(source: Path, output: Path) -> Path:
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != 3:
        raise ValueError("Only Chrome Manifest V3 is supported")
    if not all((source / name).is_file() for name in EXTENSION_FILES):
        raise ValueError("Required extension files are missing")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as dest:
        for name in EXTENSION_FILES:
            info = zipfile.ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            dest.writestr(info, (source / name).read_bytes())
    return output


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("extension"))
    p.add_argument(
        "--output", type=Path, default=Path("dist/nohack-extension-source.zip")
    )
    args = p.parse_args()
    print(package(args.source, args.output))


if __name__ == "__main__":
    main()
