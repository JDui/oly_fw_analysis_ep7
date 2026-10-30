# Read-only current-task stack provider

The new`runtime/task_context` module supplies an actual native current-task view
for the existing bounded frame mappers. It reuses the existing GCC`get_tid` veneer
and does not borrow a task-ID registry, infer a generation or enable installation.

## Native provenance

`600317ac` checks per-core context flags, then follows context+96 → current-cell →
current TCB and returns the halfword at TCB+16. Both dynamic creation`60030619` and
the configured-task loader copy a24-byte specification into TCB+68. The initializer
`60030afa` requests the specified stack size when no stack pointer was supplied,
then stores the actual allocation back into that specification.

| TCB field | Meaning from the reviewed creation/start path |
|---|---|
|+16|Current full task ID, including domain bits|
|+76|Task entry copied from specification+8|
|+84|Requested stack bytes, specification+16|
|+88|Actual stack base, specification+20 (supplied or allocated)|

Task starter`6003221e` computes saved SP as base+bytes−20 and installs the task
entry into that initial frame. The reviewed deletion path passes the same base
to the stack free routine when the kernel allocated it. This supports obtaining
the real current stack bounds; it is not proof of lifetime for a foreign TCB.

## Query behavior

1. Call the original`get_tid`; reject errors and unsupported ID/domain shape.
2. Require core word`8050` to match the full ID's domain before following the
   per-core table`8ff00004` and current-TCB chain. Check word alignment/overflow.
3. Require TCB+16 to equal the returned ID. Read its entry, actual base and size;
   reject empty/unaligned/wrapping bounds and an anchor outside the stack.
4. Call`get_tid` again and reread the current-TCB chain. A changed ID, domain or
   TCB refuses the view. Every refusal clears output.

The native access callbacks perform volatile read-only kernel accesses. They trust
the same live kernel objects as native`get_tid`; they are not fault handlers for
corrupt arbitrary pointers. The view is valid only in a normally returning current
task without cancellation/migration. It cannot be cached as a task-instance lease,
prove nonreuse after deletion, establish a GUI session, or set
`expanded_group_ready`. Runtime publication and cohort/domain admission remain
separate duties. A successfully read domain1 view does not authorize using domain0
queues or the private domain0 semaphore.

## Focused verification

- [Stock evidence](../../research/ep7/current-task-stack-current.json):59 exact
  instruction witnesses, including dynamic/configured initialization and initial
  stack formation; current structured stock input, no SHA or firmware mutation.
- [Host integration](../../research/ep7/current-task-stack-host.json): strict and
  ASan/UBSan passed. Real query algorithm ran against a mocked kernel read/API
  backend: first/second query failure, domain and TCB-ID mismatch, changed ID/TCB,
  bounds overflow, undersized stack and both boundary cases. Kernel reads and native
  execution remain mocked; core task-lease queries remain zero. The report label
  distinguishes these two different query mechanisms.
- [Target objects](../../research/ep7/current-task-stack-target.json): query535 text
  bytes (local frames36/60), native callbacks87 (local0/12/32), reused five-instruction
  get_tid veneer17. Only original get_tid address remains unresolved in this narrow
  object group. No target link, execution, runtime publication or firmware build.

Next: use this view in a shared runtime provider whose installation state and
private semaphore lifetime cannot disappear while an owned job/ticket exists;
separate retryable contention from permanent poison before binding cleanup waits.
