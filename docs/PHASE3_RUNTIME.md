# Phase 3 — End-to-end observation skeleton

This branch wires Phase 2 NoHackFlow processing to a bounded runtime event queue and transactional SQLite storage. It records observations, not ML predictions.

## Local command

Install \`nohack[dev,capture]\` and run in PowerShell:

\`\`\`powershell
nohack replay-store --input .\data\samples\authorized.pcap --database .\runtime\observations.db
\`\`\`

Use only a capture you own or are authorized to inspect. The command uses the same Phase 1/2 packet normalization and flow feature extraction path. It stores model features, timestamps, hashed flow identifier, completion reason, source and explicitly \`UNASSESSED\`. It does not store packet payloads, raw IP endpoint fields, or process names.

The bounded runtime queue reports overload drops; \`stop()\` flushes remaining flow observations. SQLite uses parameterized statements and transactional commit/rollback. Retention deletion exists as a repository operation but is not automatically scheduled.

## Verification

\`\`\`powershell
python -m pytest tests/test_phase3_runtime.py -v
python -m ruff check .
python -m ruff format --check .
python -m mypy src/nohack
python -m pytest --cov=nohack --cov-report=term-missing --cov-fail-under=85
\`\`\`

Inspect the resulting SQLite database and command output. Missing or malformed PCAPs must fail rather than generating simulated observations. Phase 2 controlled Windows Npcap verification remains independent.

## Not yet implemented

No trained model, inference probability, attack-family labels, browser-native event matching, FastAPI HTTP API, GUI or installed service is included in this phase. A valid observation is not a cybersecurity verdict.
