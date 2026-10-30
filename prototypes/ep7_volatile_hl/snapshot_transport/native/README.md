# Local raw queue callable ABI

`queue_bridges.s` translates GCC13.4 MN10300 callers to the already observed native
local receive60036c8e and send60036ede signatures. It does not install a callsite
hook or bind those addresses. Entry words1/2 are d0/d1; words3/4 are entrySP+12/+16.
The veneer saves a2 and reserves12 bytes, giving a16-byte envelope, so the additional
arguments are loaded from SP+28/+32. Receive maps buffer→a0, timeout→d1; send maps
buffer→a0, bytes→d1, timeout→a1. The native save/frame operands are32 and40 bytes.
Returned d0 is unmodified; receive's byte count is not converted to success0.

[Target report](../../../../research/ep7/queue-raw-abi-target.json) checks13 bridge
instructions, native call masks/frames, two relocations, and16 instructions in
fresh GCC caller probes. The symbol union retains exactly two unresolved native
targets. This is static assembly/compiler evidence, not instruction execution or
a full stack budget. The raw veneer never enforces capacity. Callers must provide
a buffer at least as large as the proven queue maximum and a qualified local task
domain.

```sh
python3 tools/ep7_sidecar_target_check.py --tool-prefix /work/install/bin/mn10300-elf- --queue-abi-only
```

## Remote and teardown boundaries

Do not bind the local receive symbol to remote wrapper60053ab0. Its allocation
failure path returns positive255 at60053b20; positive alone does not prove copied
bytes. A normal remote record selects operation2, and backend60053e9c invokes the
local receive then stores d0 at record+8. Existing completion/failure/cache concerns
still apply; no remote wrapper or buffer lifetime qualification is supplied here.

The kind19 relay/worker exit paths603ef9ad/603f278b call603df93a, which passes the
queue to603eeb4d→60051372 (`OlyQeDl`) then calls the task-exit wrapper. This is
queue teardown, not another descriptor receive into a300-byte drain buffer. The
separate command drain603e0546 does invoke the materializer and must be covered.
[44-witness report](../../../../research/ep7/queue-shutdown-current.json) records
these bounded joins; no exhaustive receive/teardown closure is claimed.

`ep7t_invalidate_all` now supports experimental pipeline teardown under its existing
lock: all prepared/published/consumed slots clear, serial remains monotonic, copied
snapshots remain independent. Lock failure returns false and preserves the cleanup
obligation. A native adapter must serialize teardown and new admissions; this API
does not stop queues/producers, free native metadata, or cancel an already running
stock job. [Focused host report](../../../../research/ep7/snapshot-shutdown-integration-host.json).
