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

[Native queue research and remaining seams](../../../docs/ep7/QUEUE_TICKET_CARRIAGE.md)
show why enlarged queue configuration and all receive adapters must be installed
together. Merely changing send length would overwrite existing stock buffers.
