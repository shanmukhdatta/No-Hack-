"""PyInstaller executable entrypoint for Chrome's Native Messaging protocol."""

from nohack.native_host import main

if __name__ == "__main__":
    raise SystemExit(main())
