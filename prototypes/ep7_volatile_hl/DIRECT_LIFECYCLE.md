# Direct observer and fresh-job lifecycle integration

These are executable C integration components, not installed native hooks. The
existing task-scoped API remains unchanged. `ep7p_direct_apply` adds a separate
trusted exact-synchronous-observer path with no task identity query. Its header
states the lifetime/stability/ABA preconditions; the C entry itself cannot prove
that its caller is the proposed post-builder seam.

## Direct authorization

The core lock spans exact integer request lookup against each registered
`base+11364`, bounded native-layout decoding, output nonalias/bounds validation,
and copying the immutable24-byte H/L snapshot. Unknown requests are never
dereferenced. Decoder gates include operation membership/backlinks, stage2 and
count3..16, callback6036884d/no mutation callback, rawmode11, type0, owner0 and
supported header/format. Captured profile comes from the registry: there is no
invented request selector field or current-GUI lookup. Only local H/L values
remain after unlock; output writing uses the same private LUT helper as the
scoped path. Zero H/L lanes preserve original output, including nonzero native
values; S and all other bytes remain unchanged.

The registry lock does not serialize arbitrary stock request writers. The
trusted native caller must establish stable request/config fields, live output
through return, no queued/retained invocation, and no stale request across free
and address reuse. Revocation must succeed under the core lock before free.
The test explicitly demonstrates that a naked old request address matches a newly
registered allocation at the same address; this is NOT detected as a stale
invocation. Native synchronous lifetime must exclude that scenario. Task ID
alone would not solve it. Stock field stability and placement remain separately
unqualified native-adapter obligations.

On the32-bit target native pointer and wire addresses coincide. Host tests use
the low32bits of a malloc allocation as a synthetic decoder relocation, never
dereferenced. The full host uintptr_t is used for registry matching; wrapping or
invalid wire geometry is rejected conservatively.

## Lifecycle orchestration

`ep7p_lifecycle.c` performs:

1. Copy an already-capture-bound immutable snapshot before any callbacks.
2. Invoke trusted fresh constructor, then converter only on constructor success.
3. Register H/L only after both succeed and independent extent/provenance permits
   the enlarged15512-byte allocation. The callback's `fresh_extent_proven` is a
   trusted allocator-boundary assertion, NOT self-validating evidence.
4. Invoke processing even if extension registration fails: stock-neutral fallback.
5. A synchronous reader callback accepts only this invocation's request address,
   then calls the direct API on initialized native-layout bytes and built output.
6. Invalidate registry admission before cleanup on every normal return.

This path does not enter a premature reader scope before request initialization,
query task identity, or fabricate an `ep7p_observation`. Constructor, converter,
process, cleanup and native capture attachment remain host callback interfaces,
not direct calls to camera addresses. Native statuses are preserved unchanged in
`native_status`, meaningful only when `invoked` is true.

Failed invalidation (for example lock failure) quarantines the descriptor and
allocation: no cleanup/free is permitted. `ep7l_retry_cleanup` retries registry
release before cleanup. Its result/token and matching core/ops/descriptor are
trusted lifecycle state; do not copy ownership or retry with mismatched objects.
Constructor partial failures still receive cleanup. The native cleanup contract
remains responsible for existing hardware/job lifetime; host callback return
alone does not prove hardware quiescence.

A prototype budget permits16 reader attempts per invocation, not a claim about
native stage count or processing duration. Processing must return normally only
when it retains no callback/context. Asynchronous callbacks, longjmp/exceptions,
task death, concurrent descriptor reuse and reentry are not handled by this C
orchestrator. The native observer's eventual context routing is not installed.

## Reproduction

`python3 prototypes/ep7_volatile_hl/check_host.py --sanitize` now runs six host
suites under strict C11 and ASan/UBSan. Direct tests cover16operation slots,
unknown/freed/interior requests, malformed shape, output bounds/alias, failedlock,
neutral preservation and explicit same-address reuse limits. The lifecycle suite
runs raw logical wheel input → volatile UI → captured snapshot → real malloc →
constructor/converter byte fixture → direct reader → invalidation → cleanup.
Later UI edits do not change captured output; native S/status are preserved.
Thirteen lifecycle scenarios include construction/conversion errors, old extent,
absent provenance/snapshot, unsupported type, failed release/quarantine/retry,
serial exhaustion, allocation failure, registration-lock failure, wrong invocation request
and bounded reader attempts. Repeated failed cleanup retry preserves quarantine/status. A deliberately
failing current-task callback is never called. LeakSanitizer remains disabled.

The target checker compile-checks the lifecycle module as an unlinked MN10300
object, alongside core/decoder/UI/memory modules. No target execution, native
address linking, firmware patch, camera writes or pixel-calibration claim follows.
