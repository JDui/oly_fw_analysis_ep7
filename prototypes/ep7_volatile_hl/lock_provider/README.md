# Same-domain-only provider scaffold (not a usable native adapter yet)

These self-authored C callbacks plug directly into existing `ep7p_ops.lock/unlock`.
The host test links the actual core, edits a real profile and exercises its
single-critical-section adjustment API. This is not a disconnected lock model.
It neither creates a semaphore nor binds camera addresses/ABIs. A trusted caller
must supply a NEW private live semaphore, initial/max1, and normalized veneers.

## Actual behavior

- Immutable configuration is initialized once before sharing. Require positive
  nonspecial16bit handle, nonzero low12 index and reviewed domain0/1/2.
- Every acquire queries native task ID, requiring exact success, nonspecial ID,
  same **full 0x7000** domain. Domain mismatch/unknown context declines before
  native wait. No CPU transport, no claim UI and processing share a domain.
- C11 atomic state READY→BUSY is acquired before raw wait and held throughout the
  whole core call and native signal. This serializes provider state and rejects
  reentry/competing admission. It remains BUSY while signal may wake/preempt a
  task; only confirmed signal0 publishes READY. Thus there is no ready-before-
  poison gap caused by another task observing the native semaphore release.
- Raw wait timeout0 only: exact0 acquires; known raw -50 poll contention reopens
  READY without signal; any other result poisons. Unknown error is conservative,
  even if a later native qualification proves it unambiguously non-acquiring.
- Unlock is valid only after this task's successful acquire, with no task/core
  migration, cancellation or nonlocal exit. It rechecks task identity/domain;
  identity failure declines signal and poisons. Exact signal0 alone reopens;
  anything else latches POISON. No automatic reset/recreate/release retries.
- Task-instance/epoch API deliberately returns unavailable; direct reader/UI
  paths work without task leases. Scoped APIs are not silently assigned an epoch.
- Caller pointers/contexts and function pointers are trusted live distinct C
  objects; normalized callbacks must return normally and not reenter. The test's
  synthetic signal callback attempts acquire only to demonstrate BUSY rejection;
  that is not a license for real camera callback reentry.

## Concrete target blocker found by compile, not assumed away

Trusted local GNU GCC13.4.0 MN10300 compile and GNU2.45 assemble succeed, but the
object has exactly one undefined symbol: **`___atomic_compare_exchange_4`**
(leading ABI underscore plus GCC `__atomic_compare_exchange_4`). The platform
atomic implementation/ordering is **not provided**. No libatomic was built,
linked or run. Plain loads/stores or `volatile` are not a substitute. Do not add
unreviewed interrupt/PSW assembly to force this to link. C11's host semantics and
host tests do not qualify multicore camera memory ordering or task context.
Therefore this is an actual core-compatible scaffold, **not native-deployable**.
A future qualified short control-state primitive could replace C11 backend, but
would need an explicit ordering/preemption/context proof.

## Void unlock and lifecycle limitations are intentionally exposed

Current core unlock returns void. A core operation may commit an edit, register
or revoke a job, or copy an H/L snapshot before unlock fails. Provider poison
prevents later acquisitions; it cannot retract that work. The regression test
specifically asserts core adjustment returns true/changed while provider becomes
poisoned. This is **not** an assertion of safe successful completion.

A real outer adapter must inspect provider failure status (without resetting it)
and distinguish 'mutation committed, release uncertain' from 'not admitted'.
Outputs already computed/applied must not be claimed rolled back. If revocation
succeeded before poison, that job is no longer in the registry, but release/error
lifetime policy must be explicit before native free. Other still-registered jobs
cannot be revoked through a poisoned provider: retain/quarantine their native
allocations and do not reuse them. No lifecycle exception/fatal recovery policy
is implemented here. Cross-domain cleanup rejection similarly retains ownership
for a qualified same-domain retry; it must not free on lock failure.

## Reproduction

`python prototypes/ep7_volatile_hl/lock_provider/check_provider.py`

Runner checks target tool hashes before execution. It compiles/runs only these
self-authored host tests in strict C11 and fail-fast ASan/UBSan (LSan disabled),
then compiles/assembles the provider to a temporary unlinked MN10300 object and
checks the exact undefined helper. The [actual report](../../../research/ep7/lock-provider-host-target.json) records source/tool hashes.
Target object is never executed or installed; no firmware input is needed.

Cases: actual core edit; foreign-domain/get_tid failure decline; raw poll
contention/retry; positive unexpected acquire result poison; signal failure plus
reentrant admission attempt; wrong owner release poison; successful release with
wake-time admission rejected; and actual core committed-edit/void-unlock poison.
No actual host multithread stress or camera scheduling/hardware test is claimed.
Native veneers, atomic backend, task/domain fixture, initialization/teardown and
lifecycle error policy remain unbound. Stop here rather than pretending helper
linkage alone would make a safe native HSL lock.
