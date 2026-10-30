# E-P7 capture transport and operation completion

Exact E-P7 1.1/1100 stock only. This continues
[GUI and request ownership](GUI_AND_REQUEST_OWNERSHIP.md). Read-only disassembly
and host-side assertions, not camera execution or a working H/L implementation.

## Iteration completion is not an asynchronous completion wait

The previously observed clone release follows `0x603e16f1`, but inspection of
that helper establishes a narrower fact: it compares **halfword +4 > halfword +6**
in the loop's auxiliary structure. Before comparing, the helper can invoke an
indirect callback for descriptor code `0x100a` with a nonnull descriptor+16
(`0x603e173e`); its effects are not qualified here. No direct async wait is
established in this helper, but this is not a recursive absence proof. The counters are initialized by `0x603e137c` and used
for processing iterations. Its nonzero return is not itself an event wait or a
proof that every image-processing reader has finished.

The loop at `0x603e5f71..0x603e5f74` separately clears the word pointed to by
descriptor+0 before this iteration test. Descriptor notification flags, iteration
counts and per-operation event tokens are distinct contracts; do not treat a
single zero/nonzero value as proof of all three lifetimes.

## A real job operation join exists elsewhere

The inspected job wrapper has this concrete sequence:

```text
0x603e6d04: allocate job → descriptor+36
  0x603e62d1: snapshot parameters into job
  0x603e61b8:
    normal arm → 0x60354214(job, 0xffff): run stage callbacks
    then       → 0x603544a6(job): join previous outstanding operation
  0x603e6c8d → 0x60353cb7: cleanup and free job
```

`0x60354214` iterates up to 16 stage rows rooted at job+10984 (stride operand
12), indexed by halfword job+11312. Row+0 is invoked as a callback. Status is
recorded at job+11316. `0x603544a6` checks the previous row's +8 operation pointer
and calls `0x60354930`; that helper joins the operation via `0x6035486d` then clears
the row pointer. This identifies actual operation synchronization machinery,
rather than inferring it from the outer clone-release loop.

`0x6035486d` checks operation+16, calls `0x60350da1` with argument **1000**, and
then applies operation+32's result before cleanup. The wrapper chain
`0x60350da1 → 0x60350ce4 → 0x60350c1a` reaches wait-like API `0x6003883c`, with
success, timeout-like `-50`, and other-error branches. We have not established
the time unit: **1000 is not claimed to mean milliseconds**. The helper may clear
an event token and clean resources after error, so observing that it returns
cannot by itself guarantee hardware quiescence.

The request callback already identified at `0x60355fd4` provides the matching
signal path: numeric event **10** stores the result at operation+32, then calls
`0x60350bfd`, which signals using the token at operation+16. This is a concrete
callback/result/event join. It does not qualify every callback producer, every
stage type, timeout cancellation or ISR/core ordering.

Cleanup `0x603e6c8d` calls `0x60353cb7` with descriptor+36. That routine performs
its own cleanup helpers, releases the object at job+13248, and calls `0x60022732`
on the job. It is therefore unsafe to bind new H/L data to a raw job address
without a proven generation/lifetime contract or to retain it after cleanup.

## Consequences for a future image-owned H/L design

- Snapshot values before operation submission; later UI/profile changes must not
  mutate an in-flight image's parameters.
- Keep transport notification, outer iteration and per-operation completion
  separate in the design and tests.
- Release an extension only under a demonstrated completion/cancellation contract;
  a wait timeout or a descriptor flag clear is not a substitute.
- A pointer cleared from a stage row is not proof that every hardware consumer
  ceased reading. The operation's producer/cancellation edges still need mapping.
- No vendor padding, clone tail, request field or RAM address is designated free
  extension space by this analysis.

## Reproduce

[Job-completion report](../../research/ep7/job-completion-1100.json) contains
instruction witnesses and hashes of reviewed windows, not firmware or listings.
Exact stock identity is checked before the explicitly supplied trusted objdump
runs; temporary decoded input is deleted on success or failure.

```sh
python3 tools/ep7_job_completion.py --stock /local/stock.BIN --objdump /trusted/mn103-objdump
python3 -m unittest discover -s tests -p 'test_ep7*.py'
```

The instruction checks identify reviewed operands; they do not automatically
prove the full prose control-flow interpretation or hardware completion.

## E-P7 owner shape: a host-only guard prototype

The stock operation allocator `0x60354b8c` scans 16 records at job+14576 with
stride 56 and writes the job pointer into a free record's first word. Binder
`0x60354bb0` connects request+4 to that operation and operation+8 back to the
request. Its embedded-request arm uses job+11364; an external-request arm also
exists and is deliberately outside the prototype below. Membership helper
`0x60355f56` checks exact equality with those 16 record addresses.

These are **not PEN-F's 52-byte records or its relative offsets**. The apparent
16-byte job tail at +15472 is occupied: the binder copies its eight halfwords
into operation+36 and clears the tail. It is not a spare H/L array.

[`ep7_owner_shape.py`](../../tools/ep7_owner_shape.py) implements a small
**host-only, non-dereferencing shape check** for supplied observations/fixtures:
exact embedded request position, E-P7 callback identity, membership in one of the
16 operation slots, and matching forward/back links. It rejects unknown/external
layouts and arithmetic wraparound. Tests cover all 16 slots, PEN-F-stride
misuse, corrupt links and invalid inputs.

The return value is only a matched slot index. It is NOT evidence of a valid
allocation, live memory, current generation, supported image mode or completed
hardware processing. A test explicitly demonstrates that reused identical
addresses match again: this guard cannot replace a generation/lifetime protocol.
It does not read camera memory, mutate firmware or provide a hook address.

## Transport producer and acknowledgement are now connected

Materializer `0x603dfc7a` receives a **16-byte command**, not a capture image,
through the handle stored at `0x60040d72`. Command+12 points to caller metadata;
metadata+72 supplies the dispatch code, and metadata+8..67 supplies **15 words**
copied to descriptor+56..115. The materialized descriptor is 300 bytes.

In the reviewed kind-16 branch, the selected ID at descriptor+116 normally comes
from descriptor+56, but dispatch `0x1002`/`0x1005` selects +60. For dispatch
`0x100c`, the first capture is initially resolved; marker byte +24776 equal to 11
selects the second ID instead. Registry getter `0x6029b9d1` provides descriptor+28.
Kinds 19 and 22 have distinct branches and are not collapsed into kind 16.
The materializer initializes +260 to zero; downstream helpers may change it.

The established transport path is:

```text
16-byte command → 0x603dfc7a materializer
  → 0x603dfb10 routing to handles at 0x60040d74 / 0x60040d76
  → 0x603ef892 relay → handle at 0x60040e34 (selected routes)
  → 0x603ef9bb relay → handle at 0x60040d70
  → 0x603e5d57 processing loop
```

Relay helpers can modify descriptors or capture data. This is not an immutable
end-to-end message guarantee, and kind 19 has another route.

Materializer identity lookup `0x603e0681` accepts IDs **1..27**, while the capture
registry accepts **1..25**. Class 0/1/2 and ID index an eight-byte entry at RAM
`0xa26a080c` (class stride operand 216). The materializer stores entry+4 in
descriptor+0, entry in descriptor+4, sets marker +296 and initializes entry+4=1,
entry=0. This fixed slot has **no demonstrated generation lease**. Do not unify
its ID domain with capture validity or use its address as unique image identity.

Concrete producer `0x602eea84` uses a 148-byte metadata block at stack+28. It
sets the first candidate ID and dispatch `0x100d`, then submits kind 16 via
`0x602c9cf1 → 0x60054b33`. The ordinary high-bit-clear path allocates a 16-byte
pointer-bearing envelope, sends it and waits for a 12-byte reply before returning.
The alternative high-bit-set submission path is not qualified here.

ACK helper `0x603df97d` returns status plus descriptor+44 and the metadata pointer
at descriptor+48 to the reply handle in descriptor+32. For the concrete `0x100d`
route, ROM tables connect processing to `0x603e6d04` and postprocessing to ACK
call `0x603e5f39`. **ACK precedes** descriptor flag clear `0x603e5f71..74`, outer
iteration check `0x603e5f78`, possible repetition, and conditional clone release
`0x603e5f8f`. Waiting for this reply therefore cannot be promoted to an
all-iterations or cancellation-quiescence guarantee.

The caller's stack metadata is active until that reply returns; a future H/L
snapshot must not depend on it remaining active after ACK. This is not a claim
that stock firmware erroneously dereferences the pointer afterward: required
fields may already have been copied.

[Transport report](../../research/ep7/capture-transport-1100.json) checks the
producer, envelope, materializer, relays, two ROM routes and ACK ordering landmarks:

```sh
python3 tools/ep7_capture_transport.py --stock /local/stock.BIN --objdump /trusted/mn103-objdump
```

[`ep7_kind16_contract.py`](../../tools/ep7_kind16_contract.py) is a **host-only
proposed contract**, not firmware execution. It tests the 15-word schema,
first/second selection gates, separate ID domains and conservative rejection of
metadata access after ACK. Every selection explicitly remains unqualified for
firmware use and requires generation qualification. Passing these tests does not
create a memory lease, implement H/L transport or validate real capture behavior.
