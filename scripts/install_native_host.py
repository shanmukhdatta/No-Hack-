"""Install a read-only Native Messaging host manifest for the current Windows user.

The extension ID must be taken from chrome://extensions after loading/installing
the unpacked or published extension. This tool never requests admin privileges.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HOST_NAME = "org.nohack.companion"
EXTENSION_ID = re.compile(r"[a-p]{32}\Z")


def host_manifest(extension_id: str, executable: Path) -> dict[str, object]:
    if not EXTENSION_ID.fullmatch(extension_id):
        raise ValueError("Extension ID must be exactly 32 characters a-p")
    if not executable.is_file() or executable.suffix.lower() != ".exe":
        raise ValueError("Supply the built native host .exe path")
    return {
        "name": HOST_NAME,
        "description": "No Hack local read-only companion status",
        "path": str(executable.resolve()),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id}/"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register No Hack Chrome host")
    parser.add_argument("--extension-id", required=True)
    parser.add_argument("--host-exe", required=True, type=Path)
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path.home() / ".nohack" / "native" / "host.json",
    )
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        parser.error("Windows-only installer")
    try:
        manifest = host_manifest(args.extension_id, args.host_exe)
    except ValueError as exc:
        parser.error(str(exc))
    destination = args.manifest_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    import winreg

    key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, str(destination))
    print(f"Registered {HOST_NAME} for this Windows user")
    print(f"Manifest: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
