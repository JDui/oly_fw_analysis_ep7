# Exact fresh text rollback — compile-only boundary

No native target is executed, installed or linked. The native addresses remain
unresolved relocations. This implements a strictly narrower contract than generic
widget deletion. It is not a validator for arbitrary pointers/resources.

## Admission and allocation ownership

Before any byte read, `qualify` must establish an exact live180-byte allocation,
completed exact text constructor, new/unattached/unpublished identity, never bound,
rendered, text-set or otherwise modified, and exclusive UI ownership. Merely seeing
the right vtable/tag does not establish allocation liveness or prevent ABA.
C then reads exact little-endian32 vtable=60faec7c and parent+20=NULL, two typebytes
+4/+5=8010, and single bytes+68/+88=0. These byte gates avoid the two proven
parent-null dereferences in native+152; they are not arbitrary zero-fill defaults.
Corresponding qualified resource descriptor bytes84/68 must be zero on successful
initialization; failed base initialization leaves the constructor-zero fields.

## Global allocator context is not hidden

`enter_context` must atomically within the existing serialized/exclusive UI scope
save prior GLOBAL native UI allocator selection, select child's saved bytes28/29,
and produce an opaque prior token. A failure must leave context unchanged. The
provider must keep that selection stable across cleanup/destructor/deallocation.
`restore_context` is an infallible callback restoring the exact prior context even
after the object has been freed. These are normalized GCC callback interfaces,
NOT casts of native virtuals. Their native implementations remain unbound; no
claim that static evidence proves a global allocator mutex or task-local context.
Tests demonstrate restoration with mocks only. Native sequence changes context
without restoration; the new adapter deliberately requires restoration instead.

## Actual veneer

GCC d0=object. Own MOVM saves d2,d3,a2,a3 at S-4/-8/-12/-16, reserves16 more;
child pointer local at S-20, native CALLS return slot at S-32, original GCC return
at S. CALLS exact text cleanup (unresolved target intended60d048d0 with its own
MOVM/add prologue), CALLS text destructor (intended60d4be64, own prologue), then
CALLS the deallocator returned in a0 with original child pointer. RET32 restores
original GCC frame. No incorrect native CALL immediate frame and no midfunction
entry. Native callee internal stack frames extend below S-32. Exact35-byte body,
13 instructions and two absolute relocations are checked with4 negative mutations.

Exact class+368 is bareRET60cfeafe and deliberately omitted, not assumed for other
classes. +152 is necessary because destructor alone does NOT free layout+64.
Cleanup can inspect/remove matching native global UI references, queued events,
and timers; this is why live serialized UI context is mandatory. No C object
reads occur after native destruction. State must be revoked before caller retains
or reuses any pointer. Once native cleanup starts there is no recoverable callback
failure/exception protocol: all providers must return normally and restoration
must succeed; longjmp/abnormal native faults are outside this compile-only model.

Host test uses a destruction stub that overwrites the object, not firmware. Nine
cases cover field guards, qualification rejection, failed context entry, success
and exact prior-context restoration. Strict ASan/UBSan tests and target compilation
are not hardware validation or renderer readiness. Independent review required
before calling this provider gap closed; all current publication files untouched.

## Callback storage lifetime

The ops table, its context and the saved-context representation must be independent of the child and every child-owned allocation, stable and alive through restoration. They must not alias freed object/layout/string storage. The saved token cannot borrow such storage. Qualification and context-entry callbacks cannot mutate the admitted object, change ownership, publish it, reenter this operation or invalidate earlier checks. These are mandatory provider assumptions, not properties proved by the host mocks. Enter failure leaves global context unchanged. All callbacks return normally.

## Current native context implementation

`native_context.c` and `context_bridges.s` now supply those context callbacks via
the actual service getter and inherited selection leaves. The earlier unbound
status above describes the original checkpoint. `ep7_text_rollback_native` still
requires the exact allocation qualifier and admitted live/exclusive GUI scope;
its current-task and service identity checks establish neither a lock nor a lease.
No later task/service admission occurs after destructive cleanup starts. A pinned
service and a copied 16-bit old selection suffice for restoration under that scope.
Details and current reports: [UI_CONTEXT_BINDING](../../../docs/ep7/UI_CONTEXT_BINDING.md).
Run `check_native.py` and the target checker's `--ui-context-only` mode; neither
invokes the original SHA-guarded main. No firmware is linked or executed.
