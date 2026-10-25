# Optional PySide6 Desktop Interface — future reference

Chrome Manifest V3 is the primary UI. A standalone Windows PySide6 application is **not part of the accepted initial release**. The PySide6 extra is declared but the complete desktop GUI is not implemented.

If pursued later, the interface should show:
- Local companion permissions, device interface selection and explicit time-bounded capture controls.
- A model-connectivity state that is **unavailable** until a verified trusted bundle is genuinely loaded.
- Recent independent NoHackFlow assessments, not verdicts about the active Chrome tab.
- False-positive review workflows, model/version metadata and calibrated explanation labels.
- Local drift reports, collection health, retained metadata lifecycle and delete controls.
- Error recovery, accessibility, keyboard operation and safe shutdown.

Implementation should reuse existing SQLite and the loopback-only API rather than creating a second feature or inference implementation. Avoid auto-capture on app launch or saving raw payloads; leave unsigned executable and Npcap license compliance for separate user-device release acceptance.

Do not describe this document as a shipped Windows GUI.
