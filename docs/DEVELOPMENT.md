# Windows / Antigravity development setup

This is a Python 3.11 package foundation, not a running traffic detector. Run from a cloned repository in Windows PowerShell. GitHub is the source of truth; always verify which branch is checked out.

## Prerequisites

Install Git and 64-bit Python 3.11 from trusted sources. Confirm the Python launcher with: py -3.11 --version. Npcap is **not** necessary for Phase 0. Do not run the IDE as administrator for these steps.

## Clone and set up

~~~powershell
git clone https://github.com/shanmukhdatta/No-Hack-.git
Set-Location No-Hack-
git fetch origin
git switch --track origin/phase-00-foundation
git status --short
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]" -c requirements/dev-py311-constraints.txt
~~~

The expected git status is empty and current branch is phase-00-foundation. If you already cloned, run git fetch origin and git switch phase-00-foundation (or git switch --track origin/phase-00-foundation the first time).

## Phase 0 verification

~~~powershell
git branch --show-current
.\.venv\Scripts\python.exe -c "import nohack; print(nohack.__version__)"
.\.venv\Scripts\nohack.exe --version
.\.venv\Scripts\nohack.exe doctor
.\.venv\Scripts\python.exe -m pytest --cov=nohack --cov-report=term-missing --cov-fail-under=85
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src/nohack
.\.venv\Scripts\python.exe -m build
git status --short
~~~

The doctor prints a JSON object on stdout with status "foundation-only", phase 0, capture_active false, model_loaded false, and api_host "127.0.0.1". One structured JSON log record goes to stderr. Tests should pass; Ruff/mypy should exit 0; build generates sdist and wheel in ignored dist/. These are *expected* results to verify, not a claim they passed on Windows.

PowerShell variable example:

~~~powershell
$env:NOHACK_LOG_LEVEL = "DEBUG"
.\.venv\Scripts\nohack.exe doctor
Remove-Item Env:NOHACK_LOG_LEVEL
~~~

The .env.example is documentation, not an auto-loaded secret file. For a local-only setup, avoid putting private traffic records into Git.

## Workflow and future phases

Do not develop on main. Commit to a reviewed phase branch and open a PR; use GitHub checks before merging. Phase 1 introduces NoHackFlow schema/features; Phase 2 introduces capture (Npcap installed separately, after license/driver compatibility review). Kaggle is reserved for expensive training in later phases. Bring Windows terminal traces into the project discussion for debugging; never paste secrets or sensitive packet payloads.

## Dependency reproducibility boundary

The package pins its minimum Python version and bounds optional dependency families. The verified Phase 0 Python 3.11 CI development environment is additionally version-constrained in requirements/dev-py311-constraints.txt for both Linux and Windows. This file pins tested tooling/transitive versions but does not lock wheels by hash or guarantee platform-identical system dependencies. The version of each tool used in CI is observable in its job log; capture the installed versions with:

~~~powershell
.\.venv\Scripts\python.exe -m pip freeze
~~~

When Phase 4+ needs substantial training dependencies, generate and review separate frozen CPU/Windows and Kaggle training environments rather than imposing huge dependencies on the base installer.
