# Controller-local, out-of-object capture sidecar prototype

Actual C backend for the existing compiled state observer, not native metadata
modification. `transition_binding.c` defines its exact previously unresolved
callback and invokes the bounded backend on a still-unresolved private runtime.
The newer pipeline selects `native_binding.c` instead of that legacy thin binding;
it defines the real source/observers and storage. See
[native capture binding](../../../docs/ep7/CAPTURE_NATIVE_BINDING.md). Its actual
installation, serialized lifetime and safe-placement gates remain open.
The selected seven-object MN103 symbol-set closure leaves only that runtime and
original native state service unresolved. Objects remain unlinked/unexecuted.
No56-byte native node is expanded. Capacity8 is a prototype choice, not nativepool.

## Ownership/ordering contract — not supplied by these interfaces

A fresh zeroed object is initialized once from actual controller state before any
hook use; native initialization/reset placement is UNBOUND. No runtime reinit,
poison recovery or persisted tokens. All calls, nativeprefix reading and associated
native lifetime must be in a single exclusive controller interval: no interrupt,
foreign task, async callback, cancellation or reentry can mutate/free those objects.
This is not inferred merely from running on the same CPU. Settings capture may
use its separately qualified core lock; its callbacks must not reenter sidecar.
The transition callback itself performs no locks, allocation or fallible callback.
Under the exclusive contract its clearing/generation update is synchronous and
infallible, so the native state commit cannot outrun invalidation.

1. A trusted adapter proves fresh allocator602a3116 provenance before registration.
   Supply opaque node and its actual associated-object label. The backend NEVER
   dereferences these integers. A duplicate still-live node poisons the entire
   registry instead of silently replacing an existing capability.
2. Registration returns a monotonically unique token and binds current generation.
   `authorize(state,node,token)` MUST succeed BEFORE the adapter reads nativeprefix
   or resolves capture. Keep the interval serialized through seal/copyout. Passing
   sampled prefix structs to the backend does not prove caller obeyed this order.
3. After actual population completion (normal control return, not guessed d0==0),
   seal once using that owned capture's rawmode/selector and actual `ep7p_capture`.
   A failed/unsupported/early sampling attempt permanently leaves this node neutral;
   no later retry using current GUI settings. Early copyout similarly consumes the
   opportunity, so already-published unsealed nodes cannot be backfilled later.
4. Prefix supplied by adapter binds node->associated label, resolved capture label,
   captureID1..25, rawmode11 and COLORselector1..4. Widths are normalized C unsigned,
   not claims about native field encodings. No invented backlink: associated+8 is
   populated only later by selected-node route. Copyout requires exact same prefix,
   token/current generation and returns only `ep7p_snapshot` by value. Observed
   prefix mismatch permanently unseals the entry. Subsequent GUI edits do not change
   an already captured snapshot. No native metadata/job output is written here.
5. Forget token BEFORE original native free, even when a nodefree is not capture
   retirement. Cover every admitted within33 disposal path, not just state changes.
   Unknown/stale token cannot forget a reused pointer's new entry.

Every observed actual old33 commit clears entries, INCLUDING33->33; every enter33
increments generation. Sentinel255 is no commit. Observed old/current-state
mismatch and token/generation overflow permanently poison and clear the registry.
State no longer33 declines admission. No counter wrap and no reset-to-reuse path.
Registryfull simply rejects a fresh node neutral, without overwriting live entries.

## What is still not proved

Known fresh provenance, exact native prefix/lifetime, full disposal/retirement
coverage, no unseen state writes, controller serialization, captured settingslock
qualification, and native initialization/hook installation remain adapter gates.
Tokens do NOT cure a stale queued pointer or pin freed native memory. No claim
that an integer tag establishes an allocation generation. An adapter cannot reuse
an old token on a new object at the same address. Caller must use genuinely valid,
nonaliasing C buffers; this API does not validate arbitrary output addresses.
Runtime definitions are public for test inspection, not permission for production
code to mutate counters/state or memcpy/reset a live registry.

This layer can be source-domain-local. Future downstream job runtime can consume
an independently owned snapshot value rather than share the same lock/runtime
across cores. That handoff, transport coherence and job attachment are NOT here.

## Reproduce

`python prototypes/ep7_volatile_hl/controller_sidecar/check.py > research/ep7/controller-sidecar-host-target.json`

Runs actual host strict C11 and ASan+UBSan with no sanitizer recovery; compiles
actual backend/core/decoder/memory/observer/bridge to separate target objects,
checks definitions/undefined-symbol closure WITHOUT linking or target execution.
Native evidence: docs/ep7/{NODE_STATE_GUARD,NODE_DISPOSAL,CAPTURE_ATTACHMENT}.md.

## Current-live node/token join (host validated, native binding unbound)

The split native population envelope now uses `ep7c_sample_population` after
the first normal return and `ep7c_finish_population` after postpopulation. The
second step uses the stored snapshot only. Early copyout burns a pending sample;
later completion cannot backfill it. Existing `ep7c_seal` combines both steps for
an already complete envelope. See
[capture population evidence](../../../docs/ep7/CAPTURE_POPULATION_ENVELOPE.md)
for current host/target checks and the still-unbound native hooks.

`ep7c_resolve_live(runtime, state, node, &token)` now resolves a registered,
current-generation node label without reading native memory. It uses the existing
bounded registry rather than a second token map. Failure leaves the output token
unchanged; callers must check the return before using it. State mismatch poisons
and clears the registry through the same admission policy as other operations.

The required synchronous adapter order is:

1. Independently prove that the native node is currently live and hold the exclusive
   controller interval. A queued pointer alone is insufficient.
2. Resolve its token, then authorize before reading its native prefix.
3. Seal/copyout under that same interval, or forget before the original native free.
4. Transfer only an owned snapshot value across a later asynchronous boundary.

This is an implemented lookup primitive, not an installed native adapter. A stale
pointer numerically equal to a reused node resolves the NEW token; the test records
that limitation explicitly. Old tokens cannot authorize or forget the new entry.
No API here pins memory, proves controller exclusion, or qualifies a free hook.
Native initialization, actual hook ABI/placement and complete free coverage remain
unbound. No executable region or runtime placement has been qualified.

Focused fixture coverage includes COLOR4 H/L snapshot freezing after later edits,
forget/reuse, all eight registry slots, state33 reentry invalidation, sentinel255,
state exit/reentry, mismatch poisoning, and preservation of a copied snapshot after
node invalidation. It executes the existing sidecar/core/transition implementation.

Run without a target toolchain, firmware input or SHA checks:

```sh
python3 prototypes/ep7_volatile_hl/controller_sidecar/check.py --host-only --sanitize
```

The [current host report](../../../research/ep7/controller-sidecar-live-join-host.json)
records strict C11 and ASan/UBSan success using GCC12.2 in an existing Docker image
on the Windows host. The repository was mounted read-only and networking disabled.
LeakSanitizer was disabled, as in the prior checker. The earlier target report
predates this extension: the modified source has NOT been cross-compiled, linked,
installed or executed on the camera.
