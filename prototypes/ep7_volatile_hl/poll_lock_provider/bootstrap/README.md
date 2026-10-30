# Caller-serialized private semaphore bootstrap — compile-only candidate

This is a real C startup adapter for the selected no-CAS `ep7s_provider` and
`ep7p` core, with mockable normalized native calls and unresolved MN10300 veneers.
It does not identify or install a camera startup hook. No native API was called.
The existing publication batch and target runtime object remain unchanged.

## Native evidence and bounded ownership

Raw creation6003057f takes a0→12-byte input: attributes byte+0, initial32+4,
maximum32+8; native CALL/RET `[d2,a2],16`. Bootstrap uses a stable zero-filled
attribute word and initial=maximum=1. Raw allocator60034f31 yields an encoded
positive ID `(core<<12)|index`, or a negative preallocation failure (-34 for
exhaustion). The create function preserves the allocated ID in d2, copies three
input words into the object, invokes initializer60030b78, exits its critical
section, and returns d2. It does not add the named wrapper's fallible64-slot
metadata registry. No diagnostic-wrapper status is used here.

Initializer60030b78 validates maximum!=0 (otherwise -17), writes initial count
at object+24 and makes both queue links point to the empty queue head. With the
already-validated stable1/1 spec this follows its zero-status branch. Create
ignores initializer's returned status, so this evidence must NOT be generalized
to mutable/corrupted input or arbitrary normalized callbacks. The contract
requires exact pinned raw semantics and normal return, not universal kernel
correctness or fault recovery.

Raw delete60031107 takes signed handle in d0, CALL/RET
`[d2,d3,a2,a3],20`. -18/-25/-42 return before its handle-clear. Empty-queue path
updates allocation bookkeeping, clears the object handle at60031218, invokes
scheduler-related helper6003593f, then sets d2=0 and returns. General deletion
also contains a waiter-removal path delivering -51 via600344b2: **not admitted**.
Our deletion is only for newly-created, caller-private, never-published semaphores
with no users/waiters. Published-runtime shutdown is intentionally unsupported.
Transitive scheduler/helper behavior is not exhaustively proved.

`tools/ep7_semaphore_bootstrap.py` SHA-guards stock and trusted objdump before temporary
read-only analysis;48 operands/four windows. `ownership-report.json` holds only
metadata/hashes, no firmware payload. It extends prior creation/poll evidence,
not an OS-wide reverse engineering claim.

## State machine and no lost positive handle

Caller provides fresh zero-initialized distinct `ep7b` and `ep7p` objects. It
serializes every startup/control call and must keep objects private/unmoved until
publication. Callbacks return normally, do not retain input or reenter startup;
no cancellation/nonlocal exits. No global once/compare-exchange is invented.

- COLD → CREATING after validating all callbacks. Unknown task context fails
  before create. Creation called once with private1/1 spec.
- Nonpositive raw create result → FAILED; no hidden allocated handle is permitted
  by the admitted raw-create contract. No retry/reinitialization of that object.
- **Any positive result is recorded as full-width int immediately**, before
  narrowing/validation. Invalid encoded shape (width, unsupported domain bits, or zero index) becomes permanent QUARANTINED;
  it is not truncated and no delete is attempted on a possibly unrelated ID.
  A valid encoded handle whose domain differs from the current task is instead
  RETAINED for cleanup from a qualified matching domain, not terminal quarantine.
- Valid handle with matching successful task-domain query initializes the actual
  poll provider and actual core. Result PREPARED means fully initialized but
  still private; no hook/observer/UI access is permitted during prepare.
- `ep7b_mark_published` changes PREPARED→PUBLISHED only. This is an ownership marker,
  NOT an installer, pointer-publication primitive or native synchronization. The
  caller must perform safe actual publication after this success.
- Post-create validation failure or explicit abort of PREPARED disables the
  still-private core and attempts rollback only in qualified matching domain.
  Delete callback accepts **full-word unsigned handle**, after complete validation.
  Exact delete0 → CLOSED, ownership field cleared. Context/domain check failure
  or raw -25 retains the exact handle for later caller-serialized cleanup retry.
  Missing/invalid/unexpected delete results → terminal QUARANTINED, **no retry**
  that could act on a reused numeric ID. Handle/result remain visible for diagnosis.
- PUBLISHED rejects prepare, publish again and abort, even with identical arguments.
  No reset API, no automatic deletion on runtime poison, no forced teardown.

Tracked retained ownership is not a claim every failure frees the native resource.
When deletion cannot be qualified, resources remain quarantined instead of being
silently forgotten or released unsafely. The caller must preserve that state and
keep hooks disabled. No claim of automatic recovery after -42 or corrupted IDs.

## Teardown/reboot boundary

This bootstrap never tears down a published runtime. A future live shutdown must
first stop entry, drain all callers, revoke job admissions, retain/quarantine
failed owners, and qualify kernel object lifetime; this candidate does none of
that. Reboot handling is owned by native platform/kernel initialization, not this
prototype. Do not persist semaphore IDs/runtime state across reboot or interpret
an old positive ID as the same object after restart. Volatile core settings are
not saved to firmware/NVM. There is no camera reset or reboot command here.

## Actual ABI/compile interfaces

GCC create pointer d0→nativea0; native mask `[d2,a2],16`. Delete full-word d0 already
matches; native mask `[d2,d3,a2,a3],20`. Each outer veneer uses verified own
MOVM[a2], reserve12, finalRET[a2],16. Native create's unsaved d3/a3 are not directly
clobbered and its allocator call saves them; delete's tuple restores all four.
MDR/flags are call-clobbered; finalRET uses stackRA, never guessed RETF. Two
unresolved PCREL32 relocations; nine instructions/32-byte text total. Minimum
nested envelope32/36bytes excludes deeper native stack/scheduler/interrupt usage.
A host arithmetic model checks return/saved-register/status mechanics, not CPU
instruction execution or stack headroom.

`native_callbacks.c` constructs a normalized bootstrap table using the existing
raw get_tid/poll/signal callback factory plus these create/delete veneers. It is
32-bit-target-only. No initialization function is run merely by constructing or
compiling the sources. All camera symbols remain unresolved.

## Reproduction / observed tests

```
python prototypes/ep7_volatile_hl/poll_lock_provider/bootstrap/check_bootstrap.py
python -m unittest discover -s tests -p 'test_ep7_semaphore_bootstrap.py' -v
python tools/ep7_semaphore_bootstrap.py \
 --stock ../ep7-research/firmware-inputs/OLY_E_142_1100_0000_0000.BIN \
 --objdump toolchains/binutils-2.45-build/binutils/objdump
```

Actual core/provider host tests pass strict C11 and fail-fast ASan/UBSan; scenarios
include publication and edits, repeated-call rejection, rollback0, context retry,
create failure, missing-delete terminal quarantine, malformed full-width positive
handle preservation, and callback validation before allocation. Seven checker
unit tests pass, including stock/tool guards and pointer/frame mutations.
Target compile/assemble succeeds without linking. Selected object-set closure
is now12objects, with seven exact remaining external symbols: existing native
builder/get_tid/wait/signal/runtime plus raw create/delete. All self-authored
references resolve as a set; dynamic runtime initialization/hook wiring is NOT
thereby proved. Reports contain source/tool/object hashes, not objects/firmware.
No device execution, semaphore creation, target linking or flash-ready image.
