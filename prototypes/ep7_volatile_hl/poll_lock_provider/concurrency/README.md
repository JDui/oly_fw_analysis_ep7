# Threaded actual-core + restricted poll-provider stress

Self-authored HOST-only test. Compiles the unchanged actual portable core,
bounded decoder and restricted no-CAS `ep7_sem_provider.c` together. No separate
lock model substitutes for the provider. No native firmware APIs are invoked.

One writer performs12,000 actual settings edits. Two job workers each execute
2,000 real allocation/capture/register/direct-read/revoke/free cycles, cycling
4profiles and16operation slots. Capture coherence is checked, and every output
byte is compared with that worker's immutable captured H/L snapshot—including S
and untouched canaries. Job memory is never freed until successful revocation.

Mock-native callback implementation:
- Thread-local task IDs1002/1003/1004, all the handle1001 domain; no task epochs
  fabricated. These IDs exercise the provider's real domain/owner checks.
- A private error-checking pthread mutex supplies native mutual exclusion.
- Raw poll uses `pthread_mutex_trylock`: 0 acquires; EBUSY maps to proven -50;
  any other pthread error fails the test.
- Raw signal unlocks the mutex, then `sched_yield()` BEFORE returning success.
  An atomic acquisition counter proves another task can acquire in this interval.
  Every run must observe at least one such handoff. The real provider must avoid
  post-success owner writes; wrong-owner/poison would fail the continued core
  operations or final assertions.
- All operations retry contention, bounded to1,000,000 attempts each and60seconds
  per executable. This is a test bound, not a native fairness guarantee.

`check_stress.py` executes strict C11, fail-fast ASan/UBSan and TSan host builds.
All three pass in the recorded report. Example observed handoffs before prior
signal returned: strict11,712; ASan2,930; TSan114. Counts depend on scheduling;
reproductions must compare source hashes, successful results and positive handoff
coverage, NOT demand byte-identical numerical counters. A compiled sanitizer
runtime failure raises; unsupported TSan compilation is explicitly not passed.
LeakSanitizer is disabled in this ptrace environment.

This tests actual C provider ordering against a pthread-backed mock of the
restricted raw API contract. It does NOT prove the camera's native semaphore
memory ordering, exclusive handle lifetime, allowed tasks/domain, no-waiter
invariant, raw pre-mutation failure semantics or scheduler behavior. Separate
provider failure fixtures cover poison/void-unlock outcomes; this threaded suite
uses successful releases and poll contention, not injected ambiguous releases.
No target code was linked or executed, and no public core/provider files changed.

Reproduce from repository root:
`python3 prototypes/ep7_volatile_hl/poll_lock_provider/concurrency/check_stress.py`.
