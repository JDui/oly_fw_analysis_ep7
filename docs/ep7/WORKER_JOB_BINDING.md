# Worker-owned fresh job binding

The kind19 default worker call at`603f2722` can now carry an explicit48-byte
snapshot/job scope through the original`603f2800` body. The self-authored wrapper
reserves80 bytes and calls that original body with its native56-byte frame. This
adds136 live stack bytes along this path; it does not further change the five
descriptor frame edits. The configured worker stack is8192 bytes, which is not
yet a complete worst-case stack proof.

The scope contains the frozen snapshot, actual allocator result and requested
extent, one-use phase and registered job token. It is private to this synchronous
invocation. No global current-job pointer, stock padding or enlarged metadata is
used. The original job body still constructs, converts, processes, postprocesses,
cleans up and records status through its own control flow.

| Seam | Native behavior retained | Experimental action |
|---|---|---|
|`603f2722` → `603f2800`, frame56|Original worker job body and status return|Initialize owned scope; claim descriptor once|
|`603537f3` → `60022700`, frame4|Original allocator, pointer result in`a0`|Only the qualified frozen scope requests15512 instead of15488; record actual result and zero the24 newly requested bytes|
|`603f2890` → `603e61b8`, frame24|Original synchronous processing|After successful native conversion/predicate, register the actual matching descriptor+36 job once|
|`603f28c0` → `603e6c8d`, frame24|Original descriptor/job cleanup|Revoke registered job before entering native cleanup; failed lock retains job/scope until cleanup can retry|

Allocation failure, wrong descriptor job, failed registration lock or neutral
capture cannot gain a late registration. Unknown/unqualified constructor calls
retain the original allocation request. Both15488 and15512 fall within allocator
class2; this only confirms class compatibility. Extent comes from the actual
explicit allocation request/result, never from the stride table or object shape.

## Stack identity and ABI

The stack provider must prove real current-task bounds and the installed group.
Mappings also check the exact native return PCs, original worker return`603f2727`,
saved descriptor identity and the linked self-authored`_ep7_worker_native_return`
label. These numeric matches alone never qualify storage.

| Stage / entry SP | Scope offset | Descriptor offset | Wrapper label offset | Original worker return |
|---|---:|---:|---:|---:|
|Wrapper owns80 bytes (`S`)|32|140|not yet called|136|
|Allocator native entry (`W`)|136|244|104|240|
|Process/cleanup native entry (`W`)|112|220|80|216|

Allocator also checks return`603537fa` atW+4 and constructor return`603f2845` atW+48.
Process/cleanup check`603f2897` / `603f28c7` atW+24. The two observer bridges save
and restore native`d0,d1,a0,a1`, then tail-delegate with the original frame intact.

A compiled GCC caller confirms pointer return in`a0`; it must not be replaced by
an assumed integer`d0` result. The native allocator veneer retains`a0` directly.
This is now an explicit ABI check in the existing target checker.

## Remaining native obligations

The worker context provider is deliberately unresolved. Runtime bindings and stack
qualification must stay valid from allocation through cleanup. Registration requires
a cleanup-wait callback; the cleanup observer does not call stock free while a job
token remains registered. Its retry loop is not a qualified RTOS wait implementation.
G3 must prove permitted yielding/progress, exclusion, runtime lifetime and the
response to lost context. A changed/failed provider must never misclassify a live
registered invocation as an unknown stock call. The installation group cannot be
enabled until that obligation is implemented.

ACK/drain ticket retirement remains separate from job revocation. Native metadata
identity preservation, full affected caller closure, code placement, relocation,
cache publication and the complete stack budget remain to be finished. No hardware
completion/quiescence guarantee is inferred from this synchronous CPU binding.

## Current verification

- [Stock seam report](../../research/ep7/worker-scope-current.json):53 exact instruction
  witnesses and one stride-table record, using the current structured stock input
  without SHA. No stock bytes changed.
- [Host integration](../../research/ep7/worker-scope-integration-host.json): strict
  and ASan/UBSan passed, exercising actual job scope, extent/tail initialization,
  real decoder/direct apply, mismatched job, failed registration, failed allocation,
  pre-cleanup lock retry and all four bounded stack maps. Native allocation/ABI/
  scheduler/cleanup calls remain fixtures; native C binding itself is not executed.
- [MN10300 objects](../../research/ep7/worker-scope-target.json):59 bridge instructions,
  eight call/jump relocations, frame masks, owned label and GCC pointer return
  checked. Job code288 text bytes, bridge162, mapper419, native binding554. Compiler
  local frames: job24–28, mapper56, binding12–88 bytes. These exclude callees and
  interrupts.17 native/context externals remain; no target link, execution, firmware
  build or installation.
