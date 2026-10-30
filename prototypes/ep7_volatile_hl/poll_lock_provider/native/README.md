# Compile-only raw-semaphore ABI closure

Self-authored, unresolved GCC-callable bridges plus actual normalized C provider
callbacks. No semaphore creation, native API invocation, target linking or
firmware modification. This extends the independently reviewed restricted
same-domain poll provider; it does not relax that provider's private1/1,
no-other-users, poll0/no-waiter contract.

## Interfaces now concrete

`raw_callbacks.c` produces an `ep7s_native` callback table. ctx is unused; get_tid
routes its output pointer through existing `ep7_gcc_get_tid`; poll passes the
qualified handle; the assembly veneer enforces timeout0; signal passes the handle. Target compiler
checks confirm ctx/second-argument d1→first bridge argument d0 translation,
unsigned-halfword extension, and bridge poll d1=0. The source has a 32-bit pointer static
assert and deliberately cannot compile as an ordinary 64-bit host adapter.

The actual bridge assembly:

```
_ep7_gcc_raw_sem_poll:
 movm [a2],(sp)
 add -12,sp
 clr d1
 call ep7_stock_raw_sem_wait_unresolved,[d2,d3,a2,a3],24
 ret [a2],16
_ep7_gcc_raw_sem_signal:
 movm [a2],(sp)
 add -12,sp
 call ep7_stock_raw_sem_signal_unresolved,[d2,d3,a2],16
 ret [a2],16
```

Poll is16bytes/five instructions; signal15bytes/four instructions; two PCREL32 unresolved relocations.
No camera address is resolved. Scalar handle arrives GCC d0, matching raw native wait600370af and signal60035b62. The poll veneer clears d1 immediately before the native CALL, so timeout0 is structural even if a caller left an arbitrary d1 value. Both return status d0. Public poll declaration has only one argument; no generic blocking-timeout interface is exposed.

## Register/return contract

The outer envelope matches verified GCC nonleaf MOVM/reserve/RET behavior already
used for get_tid. Inner native masks match all reviewed raw wait/signal RET paths.
Wait restores d2/d3/a2/a3 through its inner tuple. Signal restores d2/d3/a2;
a3 is not written directly in the reviewed signal function. Its nested calls
that may need a3 use save masks including a3; the context check is a read-only
leaf, critical-enter saves its own d2/d3 and its a3-using calls save a3,
critical-exit preserves its own a2 and scheduler call saves d2/d3/a2/a3.
This is the audited native callable-function convention, not an all-program
proof against arbitrary callee corruption. Extended-register ABI not admitted.

The bridge restores its independently saved GCC a2. d0/d1/a0/a1, MDR and PSW
condition flags are GCC call-clobbered and are not promised preserved; no PSW
write is added. Final RET, not RETF, is mandatory because MDR was replaced by
inner calls. No claim of transparent mid-instruction use or stock loop-state
preservation. Native APIs can use scheduling/loop machinery; these are ordinary
callable ABI veneers, not the post-builder observer wrapper.

Let original GCC entrySP=S with return[S]. Own MOVM puts a2 atS-4, reserve12 gives
S-16. Native CALL writes inner return atS-16 and mask saves below it, then adjusts
SP by its full native frame. Wait entrySP=S-40; signal entrySP=S-32. Their native
RET restoresSP=S-16 and original selected registers. Final RET[a2],16 restores
SP=S,a2[S-4],PC[S]. Minimum nested envelope depths40/32 do NOT include deeper
kernel calls, scheduler/interrupt frames or prove task stack headroom.

Semantics source is the previously verified GNU binutils-gdb
`sim/mn10300/mn10300.igen` revision87ffb882e0f4d73401a0746177ffabb8e8bbe4ac,
SHA355754c61879dc24bf6128bbba5a7931355731000e8cb213082b9b9cd4df0129.
Read-only source, not simulator execution. CALL saves return and mask at oldSP,
then subtracts immediate; RET adds immediate and reloads saved return. The
self-authored host arithmetic model checks addresses/register restoration/status
for representative results; it is not instruction emulation or silicon testing.

## Compile-only result and reproduction

`python prototypes/ep7_volatile_hl/poll_lock_provider/native/check_raw_abi.py`
`python -m unittest discover -s prototypes/ep7_volatile_hl/poll_lock_provider/native -p 'test_*.py' -v`

All6 tests pass, including mutated poll-zero/RET/native-frame and untrusted-tool rejection.
Runner verifies trusted compiler/cc1/gas/objdump hashes, exact nine instructions,
31-byte .text, two relocation targets, compiler-generated scalar argument paths and mandatory bridge clr d1,
GCC caller d2 preservation, and expected object undefined sets. Native callback
object UND is exactly `_ep7_gcc_get_tid`, `_ep7_gcc_raw_sem_poll`,
`_ep7_gcc_raw_sem_signal`; bridges remain separate unresolved objects, not linked.
Existing get_tid bridge remains at `prototypes/ep7_volatile_hl/target/`.
Temporary objects/listings are deleted; report records hashes and metadata only.

The provider now has concrete compile-only callback→GCC bridge→native-ABI entry
interfaces. A NEW private semaphore's creation/init, exact relocation/admission,
context/domain fixture, task stack, native memory ordering and lifecycle error
policy remain unbound. No attempt to borrow shared handle60040a26, use CPU routed
transport, or claim a native-working lock/HSL firmware.

## Selected CPU reader/provider dependency closure — still no linking

`check_dependency_closure.py` separately compiles/assembles exactly nine objects:
actual core, bounded decoder, self-authored memory helpers, selected no-CAS poll
provider, these raw callbacks, actual native observer, get_tid bridge, semaphore
bridges and post-builder bridge. It reads ELF global-definition/undefined-symbol
tables, rejects duplicate globals and unexpected missing references, and resolves
self-authored undefined references **as a set**, without invoking a linker.

`research/ep7/poll-reader-dependency-closure.json` records the actual result. Five
external symbols remain, exactly:

- `ep7_stock_color_builder_unresolved`
- `ep7_stock_get_tid_unresolved`
- `ep7_stock_raw_sem_wait_unresolved`
- `ep7_stock_raw_sem_signal_unresolved`
- `_ep7_native_runtime_unresolved`

There is no CAS helper dependency in this selected graph. The CAS alternative,
GUI installer, camera initialization and capture-hook installation are excluded.
The external runtime object is **not instantiated or initialized**. Callback
assignments/constructor admission still need real initialization: finding symbol
definitions does not prove indirect callback wiring, ABI compatibility of all
future callers, relocation reachability, source-job lifetime, native atomic memory
ordering, stack headroom or camera end-to-end behavior. This is object-symbol
closure, not a target image or emulator run.

```
python prototypes/ep7_volatile_hl/poll_lock_provider/native/check_dependency_closure.py
python -m unittest discover -s prototypes/ep7_volatile_hl/poll_lock_provider/native -p 'test_*.py' -v
```

All12 tests (six ABI + six closure) pass, including local-not-global definition,
missing definition, duplicate global and unexpected atomic-helper rejection.
`research/ep7/poll-native-abi.json` is the integrated31-byte/9-instruction bridge
report. No object, assembly dump, decoded firmware or large toolchain file is
included in this source/report integration.
