# Narrow CPU semaphore ACK/result follow-through

Separate extension; base probe frozen. `tools/ep7_semaphore_transport.py` reuses its exact-stock
and objdump guards, overriding witness sets only within a synchronous try/finally.
This harness is single-threaded, not a runtime/firmware implementation.
`research/ep7/semaphore-transport-1100.json`: actual 60 instruction witnesses in six hashed windows.
Three extension tests plus base six tests pass. Reproduce with the same stock and
objdump arguments as `tools/ep7_private_semaphore.py`, substituting `tools/ep7_semaphore_transport.py`.

## Normal result is not merely queue acceptance

CPU signal60053c5e and wait60053c92 allocate a 52-byte record, set kind7/8, arguments
at+20/+24, originating domain at+12, then call60053fb2. The allocator sets record
state+48=1 and distinct bitmask+16=1<<slot. There are31 ordinary slots; record
reservation-full branch returns NULL after diagnostic, conditional on diagnostic
return. The task-based submitter gets current task ID (without locally checking
status), records handle+40/taskID+44, marks state3, notifies a handle-selected
0/1/2 domain using MMIO, then waits for its origin event flag and bitmask.

Receiver dispatcher60053e48: kind7→raw signal60035b62, kind8→raw wait600370af;
return status is written record+8 at60053f18 **after** the raw call returns.
It then sets state5 at60053f22 and notifies origin based on+12. The reviewed core0
origin handler60054197..d0 scans records: state5→6, then sets that record's event
bit via60038422. Similar adjacent core1/2 handlers exist but are not needed for
this bounded witness set and not asserted as independently qualified.

Submitter60053fb2 calls60037261 at60054065 with event handle d0, recordbit d1,
output pointer a0, mode1 a1. That API checks matching event bits or enqueues the
current task at60037376. It has no timeout argument in this call shape, and can
return context/errors. A successful origin event wait followed by record+8 load
is consistent with synchronous remote-operation completion, not merely enqueue.
**Consequently raw semaphore timeout0 does not make the entire cross-domain call
nonblocking**: transport event join is a separate potential wait.

## Why exact status zero is still insufficient without a qualified ACK

6005406d saves event-wait status. It clears the event bits, then checks status at
6005407d. Nonzero status logs diagnostics; both paths converge at600540bf and
return record+8, without checking record state6 or separately returning the wait
error. The CPU helper then calls60054549 regardless of this ambiguity. That
helper invokes the existing 52-byte zero/fill routine4700115e under its critical
helpers. The proof here is the exact call and arguments; teardown's full cache,
interrupt and lifetime semantics are not established.

Thus the normal ACK chain is concrete, but **rejecting the earlier +255 alone
is not enough**. If event wait fails and diagnostics return, the result load
and cleanup occur without a demonstrated ACK; record+8 could be unqualified and
record reuse could race outstanding work. Neither reachability of that failure
under an admitted hook context nor camera hardware consequences are proven.
Do not label this a reproduced firmware bug or assert it always races.

60054546, called around publication/result, is RETF-only in this build. This is
not proof of absent system-wide memory ordering: caches, mapping, MMIO ordering
and other critical helpers have not been qualified. Do not infer unsafe hardware
solely from an empty helper.

## Design consequence and stop point

A same-domain, allowed-task fixture may use a separately qualified raw pair;
a cross-domain provider needs explicit successful completion evidence and record
lifetime ownership, not just Oly wrapper return0. A modified provider must not
release/reuse record or free protected owners following ambiguous transport
failure. Borrowing or repurposing the native transport records is not proposed.
Actual wait/signal contexts, allowed lock order and poisoning after void-unlock
failure remain missing integration contracts. This is a justified bounded stop:
receiver raw operation→status→state5→origin event→submitter result is identified;
error ACK/lifetime qualification, not another broad OS map, is the next need.
No native APIs, MMIO or firmware were executed. No lock adapter or flash image
was created.
