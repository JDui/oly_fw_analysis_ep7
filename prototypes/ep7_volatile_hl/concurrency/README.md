# Actual pthread integration stress (host only)

This compiles the existing real `ep7p.c` and `ep7p_decode.c`, unchanged, with a
self-authored pthread mutex adapter. Three threads start at one barrier: one
settings writer performs12,000 atomic full-profile edits, and two workers each
perform2,000 capture → real owned allocation → native-layout fixture → register →
direct read → revoke → free cycles. No model substitutes for the core/decoder.

Each capture is checked as either boot-neutral or one complete settings pattern,
not a torn edit. Each output is compared byte-for-byte against that worker's own
captured H/L values, independent of intervening edits. This checks every S lane
and every untouched byte as well as H/L. All16operation slots and4profiles are
cycled. Workers deliberately yield while jobs are registered to encourage
interleavings. Settings edits use the actual core edit API; this does not claim
that native GUI events or UI scheduling were exercised by this particular suite.

Only the pthread mutex protects the shared core; no dummy lock is used. The
current-task callback deliberately returns failure and increments an atomic
counter: final count must be zero. All counters shared between threads use C11
atomics. Allocation/request/output stay owned by their worker until after reader
return and successful registry revocation. This matches the direct API's trusted
synchronous/no-ABA contract, rather than manufacturing arbitrary stale invocations.

Reproduce: `python3 prototypes/ep7_volatile_hl/concurrency/check_stress.py`.
The runner builds/runs strict C11, ASan/UBSan fail-fast and TSan host executables
in temporary directories, then removes them. Current report: **all three pass**,
4,000 jobs and12,000 edits per run. TSan reports no race in these executions;
this is not a proof over all schedules or over untested adapters. LeakSanitizer is
explicitly disabled in this ptrace environment.

The first TSan attempt exposed a host-fixture address issue: its allocator gave a
pointer whose low32bits were zero, rejected by the existing synthetic wire-base
precondition. The fixture now allocates an extra64bytes and uses the aligned
interior region at+64 as its independently known job allocation; it frees the
original owning pointer only after revocation. This changes no core admission
logic and does not weaken the nonzero/bounds wire check. After this correction,
strict, ASan/UBSan and TSan runs all pass. No native runtime failure is inferred
from the initial host-fixture assertion.

No firmware input, native API, target execution, target lock binding, camera
access or output-image calibration. It validates only this host pthread-backed
integration. Native cross-domain semaphore, memory ordering, interrupt context,
callback lifetime and hook installation remain separately unqualified. The [separate stress report](../../../research/ep7/pthread-stress-host.json)
records this actual threaded run; the ordinary check_host report covers its own
single-thread suites. Core code is unchanged by this experiment. The runner
raises on any compiled sanitizer runtime failure; unavailable TSan compilation
is reported explicitly as not passed, never silently promoted to coverage.
