# One-use immutable snapshot transport

This implements the value/identity part of G2, reusing `ep7p_snapshot`, the existing
poll-only lock callback vocabulary, and the actual job lifecycle integration test.
It is not a native queue adapter and does not use or extend firmware metadata tails.

An owned message must carry `{metadata, serial}` from prepare through every relay.
The serial never wraps or resets within a published runtime. A raw-address lookup
API deliberately does not exist. Each slot retains an immutable snapshot until
explicit cancellation/ACK retirement. After retirement, an old ticket cannot claim
a newly reused slot/address. Serial exhaustion refuses new work without disabling
cleanup or consumption of previously issued tickets.

The state sequence is PREPARED → PUBLISHED → CONSUMED → retired. Publish runs before
native enqueue so an immediate consumer can claim. An early claim consumes the
sampling opportunity without producing a value; duplicate claims cannot renew it.
Consumption copies into caller-owned storage; it never returns a borrowed slot
pointer. Retirement cannot change an already copied value. Caller may use that value
with `ep7l_run` after the node, transport slot, and native metadata have retired,
provided the job's own native descriptor lifetime is independently valid.

On failed send, explicitly retire the experimental ticket. This does not free or
change ownership of native metadata. On a failed lock, do not retry a descriptor's
claim later: its H/L result stays neutral. Cleanup may be retried, since failed lock
leaves the slot unchanged. Invalid output/identity parameters likewise never license
using an old output value. All outputs are unchanged on failure.

The eight-slot limit is a prototype choice. Capacity failure leaves stock processing
neutral. This is one-use admission per image/job, not a fan-out API. Multiple native
jobs per image need separately qualified tickets prepared from the same captured
value, not reissuing from current UI. Do not nest this module's lock inside the core
or controller critical section: finish the frozen value copy, then prepare transport.

## Native integration still required

Stock kind19 envelopes carry a pointer and stock 300-byte relays do not yet carry
this ticket. The owned wire codec below supplies it in host tests; no spare
metadata/descriptor bytes are claimed. Native producer provenance, controller exclusion, relay-owned ticket
storage, publication/cache ordering, cancellation and ACK cleanup are unresolved.
Tags, a current-pointer registry, or an unqualified metadata+148 read cannot fill
that gap. The existing lock provider also needs native task-context qualification.

Run the existing focused integration (strict and ASan/UBSan, no SHA):

```sh
python3 prototypes/ep7_volatile_hl/integration/check.py --no-hash
```

It checks early claim, stale address reuse, duplicate claim, lock failure/cleanup,
capacity and serial exhaustion, frozen values after UI/node changes, and the real
decoder's 16 operation slots. No target execution or multithread acceptance implied.
See [host report](../../../research/ep7/snapshot-ticket-integration-host.json) and
[target object report](../../../research/ep7/snapshot-ticket-target.json).

The GCC13.4 MN10300 object has 836 bytes of text, plus 49 bytes of existing memory
support. Compiler-reported local static frames range from 24 to 52 bytes; this is
not the full call-chain/interrupt stack budget. Symbol union has no unresolved
externals, but lock callbacks remain runtime bindings. No target link was performed.

## Owned wire codec: implemented after native queue research

`wire.c` encodes byte-for-byte native prefixes plus an explicit 12-byte trailer:
`E7T1`, serial low32, serial high32, all little-endian. The metadata address is
already in command+12 or descriptor+48 and must match the ticket before encoding.
Tagged command admission requires kind19; tagged descriptor admission additionally
requires dispatch2001. A marker only identifies the format, never live ownership.

No native descriptor tail is touched. Encoding uses caller-owned 28/312-byte
buffers and refuses short capacity or mismatched identity without partial writes.
Decoding consumes the **actual received byte count**, clears the previous ticket on
every call, and copies only the stock 16/300-byte prefix. A legacy message ignores
old trailer bytes in reused scratch. A bad marker, zero identity/serial or wrong
route produces neutral output; unsupported lengths reject before prefix writes.
The final worker must still claim the full ticket through `ep7t_claim`.

The integration now serializes a command, models native materialization, and makes
three actual codec round trips for each of the 16 real decoder operation slots.
Native queues/materializer/ABI are still mocked. It also checks full-width serial
endianness, stale scratch tails, short receive/capacity, malformed marker, zero serial,
and wrong identity/kind. Existing ticket tests cover duplicate and old-generation
consumption. [Current host report](../../../research/ep7/snapshot-wire-integration-host.json).

The codec's MN10300 object is 664 text bytes with compiler-reported local encode/
decode frames of 40 bytes. The three-object symbol union (transport, wire, memory)
has no unresolved symbols. [Current target report](../../../research/ep7/snapshot-wire-target.json).
This does not include native receive scratch or a full stack-chain budget.

The later [local raw queue ABI](native/README.md) supplies GCC callable veneers and
records remote/teardown limits. Pipeline abort can now call `ep7t_invalidate_all`
without resetting the serial or modifying already copied snapshots. Native hook
ordering, producer shutdown and task-domain qualifications remain external duties.

[Native queue research and remaining seams](../../../docs/ep7/QUEUE_TICKET_CARRIAGE.md)
show why enlarged queue configuration and all receive adapters must be installed
together. Merely changing send length would overwrite existing stock buffers.

## Owned queue I/O

`owned_io.c` implements the receive/send policy behind a qualified synchronous
local backend. Command receive uses a separate148-byte scratch, accepts actual
length16/28, copies only16 bytes to the stock command object, and writes the ticket
to an independently owned312-byte descriptor. Descriptor receive handles the
expanded4c/ab/4f queues and legacy-only4d, clearing the trailer before every attempt.
It never derives allocation provenance from a numeric extent or protocol marker.

Send consumes the descriptor trailer before passing a separate300/312-byte copy
to the backend. A failed send cannot be retried with the old ticket; the result
retains that ticket for explicit retirement. Native qualification must prove the
frame/queue installation group, task domain, queue maximum and stable lifetime
through I/O. No callback can substitute the remote positive255 wrapper.

[Focused host report](../../../research/ep7/owned-queue-integration-host.json)
records strict and ASan/UBSan success for capacity, timeout, stale-tail, alternate
queue, failed-send retry and the three-relay/16-job integration. One initial
ASan/UBSan invocation timed out at30 seconds; diagnostic rerun passed unchanged,
so its cause is unconfirmed. The native backend, materializer and ABI execution
remain fixtures. [Target report](../../../research/ep7/owned-queue-target.json)
has no unresolved symbols across transport/wire/owned I/O/memory objects. Owned
I/O uses1161 text bytes; compiler local command-receive/descriptor-receive/send
frames are220/104/400 bytes. The400-byte send frame must enter the later full
call-chain budget. No target link, hook installation or firmware build occurred.

`forward.c` now owns the sender's cleanup decision. It requires a callback that
accepts the independent retirement value, including unresolved poll-lock cleanup.
`ep7w_retirement_ticket` can recover cleanup identity after kind/route changes;
it never licenses claim/apply. The ordinary wire decoder keeps its route checks.
The current [host integration](../../../research/ep7/descriptor-send-integration-host.json)
uses this forwarder for all three relay stages and16 job slots, plus explicit
failed-send/legacy/route-change cleanup. Run the same checker with optional
`--asan-verbose` to capture sanitizer startup diagnostics without changing tests
or their timeout. See [native sender constraints](../../../docs/ep7/DESCRIPTOR_SEND_BINDING.md).

`producer.c` now carries a previously frozen snapshot in an owned one-use scope,
publishes its ticket before command enqueue, and delegates neutral16-byte stock
send when admission fails. The full host integration uses this producer for all16
jobs. Native scope bridges and the corrected notification-preserving sender are
described in [PRODUCER_SCOPE_BINDING](../../../docs/ep7/PRODUCER_SCOPE_BINDING.md).
No source capture/current-task provider is silently supplied by these modules.

`consumer.c` now consumes the actual owned descriptor before its first claim,
including a failed lock or unsupported route. Local marker`E7C1` retains only
cleanup identity; it is never accepted by ordinary wire admission. Idempotent
retirement distinguishes an absent old key from a failed lock, retaining the
descriptor on failure until cleanup succeeds. The16-job integration now calls
this consumer directly. See [owned consumer](../../../docs/ep7/OWNED_CONSUMER.md)
for results and remaining native worker/ACK/drain duties.
