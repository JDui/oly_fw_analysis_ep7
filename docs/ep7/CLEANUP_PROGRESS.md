# Cleanup progress and runtime publication constraints

The next runtime provider must keep installation/lifetime availability separate
from accepting new experimental work. Published storage, private semaphore and
frame/queue installation remain stable until reboot; there is currently no live
uninstall/reset path. A poisoned private lock disables new registration but cannot
make existing worker/ACK contexts disappear or downgrade them to stock cleanup.

| Runtime condition | New capture/job admission | Existing owned job/ticket cleanup |
|---|---|---|
|Unpublished|Unavailable|No hooks may have published owned work|
|Published, healthy|Subject to task/domain/route qualification|Same stable runtime and stack provider|
|Published, temporarily contended|One-use sampling/registration may remain neutral|Retain ownership and yield before retry|
|Published, permanently poisoned|Stop new experimental admission|Retain job/descriptor/key; no fake ACK, free or automatic reset|

The existing private poll provider already distinguishes contention (-50) from
permanent poison. Its void-unlock limitation also remains: a mutation can commit
before a failed signal poisons the provider. Runtime consumers must inspect health
without withdrawing the contexts needed to retain those already committed records.

## Concrete progress primitive

The reviewed raw entry`600313ef` takes a delay in`d0`, checks wait-context flags,
enqueues a timer with counter input+1 and enters wait helper`60033caf` with reason2.
Normal timer expiry -50 becomes0; other results remain visible. The native return
frame is`[d2,a2,a3],16`.

The new GCC veneer fixes input to1 native unit, preserves the result and owns16
bytes. This is not a proven millisecond duration or a complete scheduler proof.
No core/private lock may be held by an ordinary retrying caller across the delay.
Permanent poison that retained the semaphore requires its separate quarantine
policy, not an assumption that another retry can release it.

Do not use named`tslp_tsk` as the substitute: its reviewed wrapper at`612c7307`
calls`60036e23`, which decrements an already pending wakeup at TCB+21 and uses wait
reason1. Reusing that wakeup count could interfere with the original task protocol.
The selected delay body has no corresponding wakeup-count consumption path.

## What remains to bind

- Shared immutable runtime publication and stable context providers, using the
  [actual current-task stack view](CURRENT_TASK_STACK.md).
- Supported task wait contexts and the absence of cancellation/migration while
  owning a descriptor/job; same-domain private poll semantics and visibility.
- A quarantine/progress policy that records permanent poison and unexpected delay
  errors without calling original ACK/free or spinning as if cleanup succeeded.
- Actual queue instance/max/lifetime checks and full installation group publication.

The delay veneer is therefore available for the provider, but is not installed as
its callback yet. No sleep API, task operation or camera code has been executed.

## Verification

[Stock report](../../research/ep7/task-delay-current.json) checks44 instructions in
the delay, wait helper and contrasting sleep path, without SHA or firmware writes.
[Target report](../../research/ep7/task-delay-target.json) checks the five-instruction
17-byte delay bridge, call/return masks and relocation. The task-view/delay object
group now has two native address bindings remaining. No host behavior changed in
this node, so the passing prior host integration was not repeated. This is not a
firmware build or target execution.
