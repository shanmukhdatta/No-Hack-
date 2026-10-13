# Phase completion ledger

## Phase 0 — repository foundation

- Date: 2026-10-13
- Branch: phase-00-foundation
- Baseline: main @ 97294f77806692bafc2b51a5d4752ece6c9b2a1d
- Prior contents: one existing README.md, preserved and annotated.
- Implemented source: packaging, importable nohack package, settings, logging, diagnostics CLI, domain exceptions and future module package boundaries.
- Engineering: tests, pytest-cov/Ruff/mypy configuration, Python 3.11 Linux/Windows GitHub CI workflow.
- Documentation: ROADMAP, ARCHITECTURE, DECISIONS, DEVELOPMENT and data/README.
- Test evidence: **PASS** on GitHub-hosted Python 3.11 (Linux and Windows), checked commit 96c297006b66034310c7d22e2a888300d33e17a7: pytest 18 passed on each OS; branch coverage 96.77%; Ruff lint/format and strict mypy passed.
- GitHub Actions: **PASS** on both OS jobs at https://github.com/shanmukhdatta/No-Hack-/actions/runs/38429825926. Linux: package editable install, build sdist and wheel, wheel reinstall and nohack doctor smoke passed. Windows: editable install, lint, formatting, mypy, and pytest passed. This is a run at a historical commit; later documentation commits must get their own status check.
- Windows GitHub-hosted runner: **PASS** for unprivileged Phase 0 checks. Windows Antigravity user-machine smoke: **not yet tested**; see docs/DEVELOPMENT.md.
- Acceptance: **CI foundation verified; local Windows Antigravity check and PR review pending**. A successful CI run does not prove Npcap capture, UI or local-device compatibility.

### Follow-up evidence

Verified GitHub Actions commands: python -m pip install -e ".[dev]"; python -m ruff check .; python -m ruff format --check .; python -m mypy src/nohack; python -m pytest --cov=nohack --cov-report=term-missing --cov-fail-under=85; Linux additionally python -m build, installation of the resulting wheel, import and nohack doctor.

Linux run: 18 passed in 0.13s; Windows run: 18 passed in 0.27s. Coverage output on both: 96.77% (98 statements, 2 missed; 26 branches, 2 partial). Command exit status 0 on each successful job. Source commit checked: 96c297006b66034310c7d22e2a888300d33e17a7. Later phases should append their own evidence; do not fabricate results.
