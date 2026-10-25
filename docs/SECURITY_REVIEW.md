# No Hack — engineering security review and limitations

## Trust boundaries

1. **Extension:** Chrome MV3 obtains top-level HTTP(S) navigation *scheme and hostname* after opt-in and keeps local bounded history. It neither inspects HTTPS payloads nor proves a website safe.
2. **Native Messaging:** only one registered extension ID should be allowlisted; it exposes a small read-only message set and must never accept arbitrary file paths or capture commands.
3. **Windows capture:** must require authorized interface selection, finite capture or controlled shutdown, and consistent 33-feature schema. Only metadata should enter flow features.
4. **Model bundles:** joblib/pickle can execute code. Do not load unknown binary files; require explicitly trusted local training and manifest/schema SHA-256 validation.
5. **Loopback API:** bind 127.0.0.1 only. Read-only model status may be queried by the native host. Manual POST inference requires a high-entropy local NOHACK_API_TOKEN.
6. **MLflow:** keep tracking server bound to 127.0.0.1 unless proper team authentication is introduced. Never publish its database or artifacts containing private data.
7. **GitHub Pages:** static documentation only. No hosted prediction API, Chrome Web Store install button, driver auto-installer or fabricated risk metrics.

## Verification gates

- Provenance and licensing of public labeled datasets and captured traffic.
- Synthetic smoke suite, real independent group-disjoint held-out evaluation, model calibration and documented false positives.
- Clean Windows hardware live Npcap retest (especially post-fix timestamps and drop/skip counters).
- Chrome popup/full-page accessibility, opt-in/retention/deletion and exact allowlisted native host behavior.
- Local API exposure probe, package hashes, executable scanner/Code Signing status and Npcap redistribution terms.
- Actual GitHub Pages workflow success and any Web Store listing checked separately.

## Threats intentionally not claimed solved

Payload-level threats, browser tab-to-flow attribution, guaranteed zero-day detection, evasive attackers, encrypted traffic decryption, protection against a compromised local Windows account, and comprehensive realtime device defense.
