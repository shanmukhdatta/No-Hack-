# No Hack — Chrome-first product and Windows companion

## Status and truthful limits

The Chrome extension in this PR is a **working browser-navigation indicator MVP**, not a trained malware scanner. It contains popup, full-page dashboard, Overview, Activity, Companion and Settings screens. It can observe top-frame HTTP/HTTPS navigation changes using Chrome's webNavigation API, retaining only host, scheme, local timestamp and deterministic indicator after the user explicitly enables monitoring. It does not inspect packet payloads, cookies, passwords, query strings, or full URL paths. It never sends browsing history to an external service.

An HTTP page is flagged for review because it lacks HTTPS protection in transit. An encoded internationalized hostname and numeric address are possible user-verification cues, *not proof of maliciousness*. HTTPS is informational only and does not guarantee a safe destination.

The optional Windows native companion in this PR supports a **read-only status handshake** only. It reports installed capture dependencies and explicitly reports model_loaded=false and monitoring_active=false. Phase 0–2 Python features/capture already present in main are not automatically connected to the extension by this status bridge.

## Load and test the Chrome extension

1. Open Chrome, navigate to \`chrome://extensions\`, enable **Developer mode** and choose **Load unpacked**.
2. Select the repository's \`extension/\` directory, **not the repo root**.
3. Pin No Hack in Chrome. Click its icon to open the popup, or use the expansion icon to open the full dashboard.
4. Confirm monitoring is initially **Paused**. Open an HTTP site and an HTTPS site and examine the indicators.
5. Click **Enable** and navigate to authorized test pages. Open Activity to verify hostname-only history; click **Clear** to delete it; Pause to stop adding events.
6. Try navigating to \`chrome://extensions\` and observe the unavailable indication.
7. Check the **Companion** tab; without an installed host it should report disconnected. This is correct.

Testing locally: \`node --test extension/tests/*.test.mjs\`. No npm install is required for this extension MVP.

Chrome's service-worker lifecycle is event-driven; browsing history is limited and stored via chrome.storage.local, not worker globals. Depending on Chrome permissions and special pages, some navigations may not be observable. No Hack must never present this limited visibility as complete device monitoring.

## Optional Windows Native Messaging handshake

Chrome Native Messaging requires a **per-extension-ID origin allowlist**, a host manifest and Windows Registry registration. Never use wildcard origins.

1. In PowerShell from repository root, activate Python 3.11 venv and run:
   \`python -m pip install -e ".[dev,capture,packaging]" -c requirements/dev-py311-constraints.txt\`
2. Build the native executable:
   \`python -m PyInstaller --onefile --console --name nohack-native-host --paths src scripts/native_host_entry.py\`
3. Copy the extension ID shown in \`chrome://extensions\` (32 lowercase letters a–p).
4. Register a host for **only this extension**:
   \`python scripts/install_native_host.py --extension-id YOUR_EXTENSION_ID --host-exe dist/nohack-native-host.exe\`
5. Restart Chrome if necessary, then use **Companion → Check connection**.
6. Remove registration via \`python scripts/uninstall_native_host.py\`.

The compiled executable is never started automatically by our installer script. Chrome starts it only on an explicitly requested Native Messaging message. The host accepts \`ping\` and \`status\` only, never remote commands, capture commands or arbitrary file access.

Do not bundle or distribute Npcap without checking its separate license terms. The host registers in HKCU rather than requesting administrative rights; actual packet capture still requires appropriate local permissions.

## Architecture interfaces

\`\`\`text
Chrome popup/dashboard ── message API ── MV3 background worker
   ├── webNavigation: top-frame HTTP(S) navigation metadata
   ├── chrome.storage.local: settings and bounded domain-only history
   └── Native Messaging: read-only status ── optional Python Windows host
                                        └── capture capability diagnostics
\`\`\`

The existing NoHackFlow v1 collector does not become a browser API. The full ML runtime, inference event delivery, browser/flow matching, API hardening, Windows installer and external validation remain in later phases. Do not describe the status host as performing ML inference.

## Privacy and acceptance gates

- No monitoring before explicit opt-in; pause stops new history.
- Only hostname, scheme, timestamps and review indicators are saved; retention 1/7/14/30 days, max 200 records.
- No website content, network payload, cookies or credentials collected.
- No external API calls or analytics.
- No explicit malware/zero-day claim from HTTP, domain spelling or a missing capture driver.
- Check Chrome functionality manually on supported Windows Chrome; automated Node tests validate pure browser logic but do not prove live Chrome behavior.
- Native host must be packaged and tested on the intended Windows installation, with exact extension origin.

## Subsequent engineering work

Integrate the real authorized Windows monitoring status and ML inference outputs when and only when released/validated. Browser UI must show the source and confidence semantics of any future ML result. Add Chrome Web Store policies, icon assets, accessibility and usability tests, distributable extension signing, installer/licensing work, and a separate advanced Windows settings UI when needed.
