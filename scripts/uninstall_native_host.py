"""Unregister the current user's No Hack native messaging host."""

from __future__ import annotations

import sys


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("Windows only")
    import winreg

    key_path = r"Software\Google\Chrome\NativeMessagingHosts\org.nohack.companion"
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    except FileNotFoundError:
        pass
    print("No Hack Chrome Native Messaging registration removed.")
    print("Any existing manifest and executable files must be deleted separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
