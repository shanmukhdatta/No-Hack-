# NoHackFlow v1 — canonical feature contract

**Phase 1 contract, used by the Phase 2 Windows capture implementation.** The source of truth
is src/nohack/features/ and configs/nohackflow-v1.json. There are **33 model
inputs**: 32 numerical statistics/ports and one categorical protocol value.

## Packet metadata normalization

PacketMeta validates nonnegative integer nanosecond timestamps, IPv4/IPv6
addresses, 0–65535 ports, protocol TCP/UDP/ICMP/ICMPV6, positive network-layer
IP packet length in bytes and optional TCP flag tokens. ICMP port values must
be zero; non-TCP traffic cannot have TCP flags. Payload bytes never enter
this interface. Synthetic fixtures use reserved documentation addresses.

A first-observed 5-tuple defines *forward* direction and reversed endpoints
define *backward*. This is not proof of which endpoint initiated a connection.
Packet times within each flow must be nondecreasing. Invalid/out-of-order
events are rejected, not quietly repaired. The Phase 2 adapter now handles capture, flow-table expiry and best-effort
process context. Phase 3 owns broader queue/orchestration concerns.

## Feature conventions

- Duration: last minus first timestamp, milliseconds.
- Packet/byte totals and direction counts: per observed network packet and
  supplied IP-layer length (not Ethernet length or application payload).
- Length min/max/mean/std: all packet lengths; std uses population ddof=0;
  forward/backward mean length uses just that direction.
- IAT: elapsed milliseconds between consecutive packets, separately for
  all packets and for successive packets per direction. No IAT until two
  relevant packets have been seen. Empty statistics are zero.
- Rates: counts / duration in **seconds**, with zero returned for zero elapsed
  time, meaning insufficient elapsed time to calculate a rate.
- TCP counts: per-packet presence of SYN, ACK, FIN, RST and PSH flags.
- Ratios: forward_count / max(backward_count, 1), and forward_bytes /
  max(backward_bytes, 1). These are **regularized** when the denominator
  is zero; they are not strict mathematical ratios in that case.
- Ports and protocol: taken from the first-observed packet. Protocol is
  categorical, not yet encoded for any trained model.

A numerically stable Welford online algorithm calculates population moments.
FlowAccumulator stores aggregates, not per-packet history.

## Version and training-serving requirements

All feature names, dtypes and canonical order are in the manifest; the
schema_fingerprint() function hashes a deterministic serialization of it.
FlowSchemaError rejects missing, extra, negative, nonfinite, wrong-type or
wrong-version features. ordered_feature_values() always returns the fixed
model-input order. Endpoint IP addresses, process names and other context
are deliberately excluded from model inputs.

**NSL-KDD-only attributes cannot be silently used in deployable inference.**
Similarly named dataset columns are not assumed compatible without explicit
units, definitions and provenance checks. Dataset mappings and model-side
transformations will be reviewed in later phases.

Tests use replay_packets() and FlowAccumulator.add() on the same fixed packet
fixture and compare *every intermediate snapshot*. This proves controlled
synthetic parity, **not** PCAP-vs-live capture parity, which Phase 2 must test.
Packet drops, offload, fragmentation, midstream capture, retransmissions and
timestamp precision may affect real captured values. IP addresses held in
context require future storage/UI minimization, redaction and retention.

## Windows Antigravity checks

Run from a clean clone with Python 3.11 and no administrator privileges:

    git fetch origin
    git switch --track origin/phase-01-nohackflow-features
    .\.venv\Scripts\python.exe -m pip install -e ".[dev]" -c requirements/dev-py311-constraints.txt
    .\.venv\Scripts\python.exe -m pytest --cov=nohack --cov-report=term-missing --cov-fail-under=85
    .\.venv\Scripts\python.exe -m ruff check .
    .\.venv\Scripts\python.exe -m ruff format --check .
    .\.venv\Scripts\python.exe -m mypy src/nohack
    .\.venv\Scripts\python.exe -m build

GitHub CI and these Windows checks must pass before merging. Npcap, Kaggle
and model downloads are not needed for Phase 1.

## Phase 2 integration note

The Phase 2 Scapy packet normalizer is now the only packet-header-to-PacketMeta adapter used by both local PCAP replay and live Npcap ingestion. It uses integer-ns capture timestamps rounded with decimal ties-to-even arithmetic, IPv4 total lengths and IPv6 40+payload lengths. Unsupported fragments and protocols are skipped. The 33-column NoHackFlow v1 schema is unchanged. The flow manager enforces ordering and bounded TCP/UDP lifecycles before calling the existing Phase 1 `FlowAccumulator`. Process metadata and interface identifiers are non-model context. See [PHASE2_CAPTURE.md](PHASE2_CAPTURE.md) for implementation and device-verification limits.
