# No Hack — Phase 3 integration handoff (from Phase 2)

**Do not implement Phase 3 until the user approves the Phase 2 PR.**
This document defines the reviewed interface boundary, not runtime orchestration
or an ML predictor.

## Source of truth

- `nohack.capture.normalizer.normalize_scapy(packet)` takes a Scapy packet and
  yields `PacketMeta | None`. Unsupported/malformed observations are dropped or
  reported by `FlowProcessor`; no payload bytes are persisted.
- `nohack.capture.replay.FlowProcessor` owns a `FlowManager` and provides
  `accept(packet, interface_name=None) -> list[CompletedFlow]` and
  `finish() -> list[CompletedFlow]`.
- `nohack.collector.flows.FlowManager(limits, process_resolver)` owns the
  canonical flow table. `ingest(PacketMeta)` emits completed records;
  `expire(now_ns)` advances timeouts; `flush()` drains all outstanding
  records. `FlowLimits` controls idle/max-lifetime/FIN-grace and flow count.
- `nohack.capture.replay.replay_pcap(Path, processor=None)` supplies
  deterministic offline input through the same normalization path.
- `nohack.capture.session.CaptureSession(interface, processor, on_record)`
  starts only when `start()` is invoked after explicit authorization, requires
  Npcap on Windows, and drains active records on `stop()`. A session's
  `tick()` schedules idle/close/lifetime expiration. Use callbacks or a bounded
  queue in Phase 3; no unbounded packet/event list is built into Phase 2.
- `CompletedFlow.flow` is an immutable `NoHackFlow` with the ordered 33
  canonical inputs; `completion_reason`, process and interface are outside
  the feature vector. `CompletedFlow.to_dict()` includes sensitive endpoint
  metadata, so future storage must apply retention and privacy protections.

## Invariants for integration

1. Only one thread may modify the `FlowManager` at a time; the Phase 2
   `CaptureSession` serializes its callback and timeout access.
2. Flow records are observations, **not** labels or predictions. Do not call
   them NORMAL, MALICIOUS or anomaly-free in Phase 3.
3. NoHackFlow v1 feature order/version and feature fingerprint must remain
   compatible with `configs/nohackflow-v1.json`.
4. A service stop must call `CaptureSession.stop()` or
   `FlowProcessor.finish()` so active, partial and half-closed connections
   are not discarded.
5. Do not infer a historical PCAP process from current Windows socket tables.
   Best-effort OS context is for authorized live capture only.
6. Expiration ticks use epoch nanoseconds; out-of-order events are rejected
   rather than reordered. Rates/durations remain Phase 1 definitions.
7. Preserve explicit consent, local-only scope, and no payload/packet
   persistence. No network injection or blocking feature is authorized.

## Acceptance / next actions

- Phase 2 synthetic tests, Ruff, mypy, build and Linux/Windows CI must pass
  at a specific PR commit; update `docs/PHASE_LOG.md` with actual evidence.
- The user's Windows Antigravity run still must verify Npcap installation,
  enumeration, an authorized 10-second capture, JSONL feature validation,
  resource stability and graceful Ctrl+C.
- If that real-device verification fails, fix Phase 2 on the **same PR branch**
  and repeat the checks before merging; do not silently start Phase 3.
- In Phase 3, introduce a bounded service/event-delivery lifecycle and health
  reporting as defined by `docs/ROADMAP.md`, without new ML claims.
