# Restricted no-CAS poll provider — separate alternative, not installed

This self-authored alternative supplies actual `ep7p_ops` callbacks and links the
real portable core in host tests. It does not replace the conservative CAS
provider. Trusted GNU MN10300 compile/assemble yields **zero undefined symbols**:
only atomic loads/stores are used, no compare-exchange helper. This removes that
specific build dependency, NOT the remaining native API/memory-order qualification.
No target linking, execution, camera access or firmware writes occur.

## Admitted native shape is deliberately narrow

A newly created, private, same-domain semaphore initialized1/max1, with every user
using exact raw timeout0 poll. No external users, blocking waits, signals, deletes,
reset or handle reuse. Kernel object and task/domain remain stable. Only ordinary
supported task contexts, no migration, cancellation/nonlocal exit or interrupt
reentry. Native normalized callbacks must implement exactly the pinned raw APIs
and return normally; arbitrary fallible wrappers/CPU transport are NOT substitutes.

The raw code has the following restricted control flow (SHA-guarded probe):

- Poll errors -18/-25/-17/-42 return before count access or mutation. Count0 +
  timeout0 returns -50 before timer/enqueue. Count>=1 decrement6003716e jumps
  directly to exit helper600371f8, then **d0=0**600371fd.
- Signal errors -18/-25/-42 return before count mutation. For an empty queue,
  current>=maximum returns -43 before mutation. Otherwise count increment60035c27
  branches to exit helper60035c32, then **d0=0**60035c37.
- Queue-wait and waiter-wake paths exist but are excluded: this new semaphore has
  only poll0 users, which cannot enqueue. No inference about a blocking user's
  error/ownership semantics is used. The -43 case is itself inconsistent with
  valid1/1 ownership after our successful acquire; poison rather than recover.
- Context helpers60031503/60031540 only inspect state, no calls/stores;
  600315a3 is RETF-only. Native critical enter/exit helpers are existing kernel
  primitives, not fully recursively proven. Exit6003860b can invoke scheduler
 6003436e. No claim that every transitive helper has no arbitrary side effects.

Thus **conditional on the native primitive and exclusive-lifetime contract**,
none of the reviewed negative returns releases our held semaphore; successful
release can schedule a new owner before the C signal callback returns. This is
not a blanket firmware theorem and not a proof for foreign-domain transport.

## Provider ordering

1. Require exact-success get_tid, nonspecial positive16bit task/handle, low12
   index nonzero, full0x7000 domain in0..2 and equal; decline foreign/unknown.
2. Check permanent atomic poison; raw poll0 exact0 alone acquires. -50 declines;
   other errors poison. Reentrant acquire naturally sees count0/-50, not recursion.
3. Recheck poison after acquisition (another admitted context could have failed
   while inside native code). If poisoned, signal without entering core and
   retain poison regardless of release result. There is no automatic recovery.
4. Record owner only while holding native semaphore. Valid unlock requires this
   task's successful acquire and the same task/domain. Clear owner **before**
   calling signal. Signal0: return with **no shared writes**. Signal error: latch
   poison; under the restricted contract it has not released ownership.
5. Poison is never reset. New admissions stop; retained/registered allocations
   need quarantine and an explicit fatal/recovery policy. No native teardown is
   attempted. Correct caller lock/unlock pairing remains a trusted contract.

Atomic owner/poison use only load/store. Their generated inline instructions are
not a proof of hardware ordering: the real same-domain semaphore must supply
mutual exclusion and required compiler/hardware visibility. Host mocks can prove
C ordering and observed race fixtures, not target scheduler/cache semantics.

## Core void-unlock limitation remains

A core edit can return true after mutation even if signal failed and poison was
latched. A regression asserts this limitation deliberately. Outer adapters must
report committed-but-release-failed distinctly; they cannot assert rollback or
silently free all jobs. Other still-registered jobs remain quarantined because
new lock attempts fail. This alternative removes CAS linkage, not that lifecycle
integration obligation. Task leases remain unavailable; direct/UI paths only.

## Reproduction

```
python prototypes/ep7_volatile_hl/poll_lock_provider/check_provider.py
python tools/ep7_poll_failure_paths.py \
 --stock ../ep7-research/firmware-inputs/OLY_E_142_1100_0000_0000.BIN \
 --objdump toolchains/binutils-2.45-build/binutils/objdump
```

Host strict and fail-fast ASan/UBSan pass. Actual core callbacks tested: edit,
foreign domain/context rejection, poll contention/retry, unexpected status poison,
pre-release error retaining semaphore, wrong-owner rejection, poison recheck,
and committed-edit/void-unlock failure. A synthetic scheduler fixture releases the
mock semaphore then acquires as another task *before the original signal returns*;
the new owner survives because old unlock does no post-success writes. It models
native scheduling rather than permitting arbitrary application callback reentry.

No multithread stress test is claimed for this separate candidate. Reports hold
actual source/tool hashes; target object is unlinked with undefined_symbols=[];
stock probe proves only the named windows/operands, not automatic full CFG or
kernel correctness. Native veneers and qualified hook-domain/lifetime fixture
remain unbound. Do not promote to native-ready from an empty undefined-symbol set.
