# No Hack — Phase 2 Windows capture and PCAP validation

**State:** implementation branch; automated CI and physical Windows verification must
be recorded in [PHASE_LOG.md](PHASE_LOG.md) before acceptance. There is **no ML
classification** or packet-blocking feature in this phase.

## Consent and setup

Only capture traffic on network interfaces and systems you own or are explicitly
authorized to monitor. A selected adapter may expose other devices' traffic on
shared links; permission must extend to any such data. Nothing starts on import,
package installation, `nohack doctor`, or `nohack capture-check`.

1. Use Python 3.11 on Windows and install `python -m pip install -e ".[dev,capture]" -c requirements/dev-py311-constraints.txt`.
2. Install Npcap separately from its official distribution, subject to its
   current EULA. No Hack does not redistribute Npcap.
3. Run `nohack capture-check` and `nohack capture-interfaces` to identify an
   available, authorized network interface. Presence of DLLs cannot verify
   access rights, working drivers or capture performance.
4. Run `nohack capture-demo --interface "SELECTED_INTERFACE" --seconds 10 --authorized`.
   The default summary includes only aggregate counts.
5. To inspect full 33-column feature records, *explicitly* add
   `--output runtime/phase2-demo.jsonl`. The directory must already exist;
   the file is created without overwriting an existing file. The output includes
   sensitive endpoint IPs/ports and optional process metadata, **not payloads**.
   Do not upload or commit it.
6. Stop with Ctrl+C; capture duration also has a 300-second hard maximum.
   Active and half-closed flows are flushed at shutdown.

Offline controlled fixture replay:

```powershell
nohack replay-pcap --input path\to\authorized.pcap --output runtime\replay.jsonl
```

Replay and live callbacks call the same `normalize_scapy` and `FlowManager`.
PCAP must have been legally obtained and consented to. Only synthetic PCAPs
created during tests are allowed in repository test workflows. A PCAP input
may hold packet payloads on disk before No Hack reads it; **No Hack does not
create or retain a payload-bearing capture file**.

## Normalization and contract

- Timestamp: Scapy `packet.time` converted via decimal arithmetic into an
  integer number of nanoseconds since the UNIX epoch (nearest ns,
  ties-to-even). Offline and live processing use this exact adapter.
- Packet size: the IPv4 total-length field or calculated synthetic IPv4
  layer length; IPv6 fixed 40-byte header plus IPv6 payload length, including
  transport headers and any supported extension headers. Excludes Ethernet
  headers. These values feed v1 length/byte features unchanged.
- TCP flags: SYN/ACK/FIN/RST/PSH/URG/ECE/CWR from the TCP header bits.
  Unsupported protocols, non-IP packets, IPv4/IPv6 fragments, tunneled
  transports, unsupported IPv6 extension chains and IPv6 jumbograms are
  skipped to avoid misattribution.
- `PacketMeta` enforces IP formats, protocols, ports and bounds.
  `FlowAccumulator` is the unchanged Phase 1 implementation. The **33
  ordered model features** remain the source of truth. Endpoints, process and
  interface context do not become model inputs.
- Network interfaces and OS drivers may drop packets, coalesce segments or
  observe only one direction. Packet retransmissions are counted as
  observations; arbitrary identical packets are **not** discarded as
  duplicates. Real-device captures cannot be assumed complete.

## Lifecycle and resource controls

`FlowLimits` defaults: **30-second idle timeout**, **120-second maximum
flow lifetime**, **1-second grace after both TCP FIN directions**, **4096
maximum simultaneous flows**. Limits can be injected into the processor
without changing the schema.

- First-observed 5-tuple orientation defines forward and reverse.
- New SYN from the first observed side after bidirectional/established traffic
  ends the old session. SYN retransmission before establishment stays in the
  same flow. No flow identifier proves the TCP handshake or application.
- RST closes a flow immediately. One FIN never closes a connection by itself;
  two-sided FIN begins the grace interval, which can include final ACK packets.
- Flow expiration, bounded-capacity eviction, TCP reuse, RST and explicit
  shutdown all return validated `CompletedFlow` snapshots. No unbounded
  history list is retained by the flow manager.
- Out-of-order arrivals are rejected and counted, not reordered to fabricate
  timing. TCP sequence numbers are not tracked; therefore this is not full
  TCP session reconstruction. A reused tuple with no observable SYN can be
  bounded by idle/max-lifetime expiration, but not separated perfectly.
- `FlowManager` is intentionally single-threaded; `CaptureSession` serializes
  live callback and expiry operations using a lock. Downstream callbacks
  must be short-lived and output storage must remain bounded by the operator.

## Process attribution limitations

On Windows, cached `psutil.net_connections(kind="inet")` is matched by
local address/port, transport and optional remote peer. Ambiguous socket
matches, inaccessible processes, unsupported protocols and race conditions
return `None`; a process can exit/reuse a PID between capture and lookup.
Process names and PIDs are **best-effort auxiliary context**, never model
columns or attribution proof.

## Privacy, operation and Npcap license

- Do not capture without explicit consent. Never monitor public or other
  parties' traffic without authorization. The CLI refuses live capture without
  `--authorized`.
- Scapy objects containing packet payloads are consumed transiently; callbacks
  and records retain metadata only. Application logging should avoid even
  unredacted IP addresses. An explicitly selected JSONL output includes
  endpoint metadata and must be protected and deleted when no longer needed.
- No network injection, automatic block action, internet API or ML verdict is
  implemented in Phase 2.
- The Npcap EULA is **not** a standard open-source redistribution license.
  The standard license has usage restrictions, including a five-install
  limit in its EULA. Do not bundle or silently install the driver. Review
  terms independently before enterprise use or distribution:
  https://github.com/nmap/npcap/blob/master/LICENSE .
- Scapy's AsyncSniffer documentation describes the `prn`, `store=False`,
  `started_callback`, interface and stop lifecycle used here:
  https://scapy.readthedocs.io/en/latest/api/scapy.sendrecv.html .

## Phase 3 handoff boundary

The Phase 3 runtime orchestrator may own a `FlowProcessor`, configure
`FlowLimits`, subscribe to `CompletedFlow` callbacks, and schedule expiry
ticks. It must manage storage/retention, health, and stable delivery separately.
Do not mark absent ML inference as successful threat classification. Integrate
the same `NoHackFlow` schema and preserve metadata-only boundaries.
