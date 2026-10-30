# Private runtime semaphore: concrete facility, not yet a native lock adapter

Read-only stock E-P7 1.1 analysis. No native API was invoked, no semaphore created,
no existing handle borrowed, no firmware modified or executed. The public core's
`ep7p_ops.unlock` is void: a native signal error cannot safely be ignored.

## Creation and ABI

`60051c8e` is a named semaphore creation wrapper. Its native arguments are a0=name,
d0=initial count, d1=maximum count; native caller frame `[d2,d3,a2,a3],40`.
Actual caller `60c4fbb6..` creates ten separate initial=maximum=1 semaphores, stores
each signed16 handle, and tests for negative failure. This is evidence for a new
private binary semaphore facility, not permission to reuse those handles.
The diagnostic spelling is `acre_Semapore1` (60073394), not `OlySmCr`.

The wrapper constructs a 12-byte raw kernel input: attribute byte +0=0, initial
u32 +4, maximum u32 +8. It calls `6003057f` with a0=input and native frame
`[d2,a2],16`; result is d0. The kernel checks attribute 0 or 1 (-11 otherwise),
context state via the current core's +28 flags (-25), count limits
0<=initial<=maximum<=65535 with maximum>0 (-17), then allocates.
Allocator `60034f31` returns -34 when no free dynamic ID is found.
The wrapper does NOT add a domain encoding. Allocator `60034fd6..de` forms
`index | (current_core_word_8050 << 12)` and stores a 16-bit handle. Index selection
and the object table (+208) are current-core based. 8050 is not a task identity.

The named wrapper has a separate 64-record diagnostic registry: it allocates the
kernel semaphore first, then searches this registry. Registry-full branch
60051cf9→60051d1d logs and returns -1 with no visible kernel-delete rollback.
This is a *conditional static branch*, not a demonstrated camera leak. Its
initialization also lazily clears current-core metadata when a shared magic does
not equal 0xbeef; don't invoke it speculatively during concurrent camera work.
Raw kernel creation avoids this particular registry step but is **not thereby a
qualified universal lock API**. Initialization needs an explicit task/context,
paired acquire/release domain policy, and checked lifetime publication.

## Acquire/release and the cross-domain boundary

Native raw wait `600370af`: d0=signed16 handle, d1=timeout, frame
`[d2,d3,a2,a3],24`. Available count (object+24) is decremented. With count zero,
timeout=0 returns -50 without enqueue; timeout=-1 follows the no-timer enqueue
branch, positive values follow timer preparation. **Timeout units not proven.**
Native raw signal `60035b62`: d0=handle, frame `[d2,d3,a2],16`. It increments
count if no queued waiter, compares against maximum (+20), and returns -43 on
that over-release branch; otherwise wakes a waiter through another helper.
Success result is zero. Context and invalid/missing handle errors are present.
This does not prove owner tracking, recursion support or priority inheritance.

Both raw accessors extract handle domain `(handle & 0x7000)>>12` and low index
`handle & 0x0fff`, selecting the corresponding table. Therefore they are not
simply current-core-index-only. However, this does not prove the kernel critical
helpers serialize every cross-core access. The camera's named wrappers explicitly
route some cross-domain operations through a separate CPU transport.

`6005393a` calls get_tid, compares task and handle `0x3000` bits, with bit0x8000
bypass and a preceding context predicate. get_tid failure is not locally checked
before the stack ID is consumed on that branch. Meaning of all context bits and
domain topology is not established. Raw calls may only be admitted after a
specific same-domain/task-context fixture or a qualified cross-domain protocol;
GUI and processing must not be assumed to share a core.

Named wait `6005168d` uses d0=handle,d1=timeout, returns with
`[d2,d3,a2],40`; same-domain route calls raw wait, alternate route calls60053c92.
It maps raw -50 to -2, other negative errors to -1, nonnegative to0. Named signal
`60051762` uses d0=handle, returns `[d2,d3],36`; alternate route60053c5e,
local route60035b62; maps negatives to-1, nonnegative to0.

### Concrete adapter hazard: positive transport failure branch

Both CPU helpers obtain a transport record via600544f0. If that helper returns
a0=NULL, signal branches60053c6b→60053c89 and wait60053ca1→60053cc5 return
**+255** without executing their operation submission60053fb2. Named wrappers
classify this nonnegative result as success. This is not a proven reachable
firmware defect: allocation helper's null reachability and system configuration
are not established. It *is* sufficient to reject blindly adapting these
wrappers as a new lock whose success means acquisition/release really happened.
A future routed adapter must qualify the lower protocol and accept only documented
success (not >=0); bypassing the wrapper alone does not solve that protocol.

## Minimal safe initialization/integration requirements (design only)

1. Keep admission disabled. In an established allowed task context, create a
   **new** private semaphore with attr0, initial1,max1 using a qualified veneer.
   Never use camera handle60040a26 or any preexisting semaphore.
2. Check raw creation result, retain exact domain-encoded handle, publish runtime
   only after creation and paired lock-provider initialization succeed. A GCC
   veneer must move pointer d0→nativea0 for raw creation and use exact native
   frame tuples; no ordinary GCC call to firmware addresses.
3. Establish all GUI/processing acquisition contexts and domain relationship.
   Qualify same-domain raw APIs or the actual routed protocol, including errors;
   reject unknown contexts. This remains unresolved, not a blanket taskID need
   for the separate synchronous direct reader.
4. Nonblocking timeout0 can conservatively decline new edit/read admission on
   contention. It does not make teardown/invalidation safe to drop: retain and
   retry quarantined owners until successful registry revocation. Blocking -1
   requires known task context, fixed lock order and short bounded critical
   sections; no callback reentry or nested locking of this nonrecursive facility.
5. Signal failure must latch an explicit fail-closed state before further
   admission (plus allocation quarantine/fatal policy). Since current unlock is
   void, a provider needs an independently checked poison mechanism or core API
   change; this candidate does not implement that. Do not free or blindly retry
   signal after ambiguous completion. Raw direct errors and routed ambiguity
   differ and must not be conflated.
6. Shutdown requires no in-flight readers, no pending owner retry, admission
   disabled, then qualified delete. Delete wrapper60051619 calls raw60031107,
   but raw deletion/waiter semantics are not reviewed here; no teardown claim.
7. Native memory ordering, reentrancy, context/interrupt interactions and
   cross-domain transport are unqualified. No native lock adapter is ready.

## Reproduction and scope boundary

`tools/ep7_private_semaphore.py` first validates the entire stock identity, then the trusted objdump
SHA before disassembling temporary decoded bytes. It emits only metadata/window
hashes; no firmware bytes or bulk listing. `research/ep7/private-semaphore-1100.json` captures actual result.
`tests/test_ep7_private_semaphore.py`: 6 tests, including stock/tool pre-execution guards, all opcode
and operand mutations, and unique window coverage. These test the analysis
harness, not the kernel or a lock implementation.

```
python tools/ep7_private_semaphore.py \
 --stock ../ep7-research/firmware-inputs/OLY_E_142_1100_0000_0000.BIN \
 --objdump toolchains/binutils-2.45-build/binutils/objdump
python -m unittest discover -s tests -p 'test_ep7_*semaphore*.py' -v
```

Stop here: one concrete creation facility and its paired wrapper hazards are
identified. Do not map the whole OS. The host fail-closed provider contract is now implemented below; a native atomic
backend and narrow domain/routed-status qualification remain open if actual hook
contexts require them. Nothing here
establishes camera stack headroom, successful HSL rendering, or flash readiness.

## Actual host scaffold, still not a native binding

The [core-compatible provider](../../prototypes/ep7_volatile_hl/lock_provider/)
now implements the same-domain fail-closed contract with a C11 atomic state gate.
Host tests include real core edits and explicitly demonstrate that void-unlock
failure may poison after an edit committed. Target compile requires an unresolved
`___atomic_compare_exchange_4`; no native atomic backend is supplied. Neither
that scaffold nor the successful [pthread stress test](../../prototypes/ep7_volatile_hl/concurrency/)
qualifies native memory ordering, task domains or recovery.
