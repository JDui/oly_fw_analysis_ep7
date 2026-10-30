# Compile-only GCC-to-native get_tid adapter

`get_tid_bridge.s` is a self-authored **real ABI-translation candidate**, not the previous native tail-forwarder. C declaration: `int ep7_gcc_get_tid(unsigned short *out)`. Caller supplies valid writable aligned output; output is valid only when status==0. The native symbol deliberately remains unresolved, with no literal camera address or installer. This does not supply task epoch/TLS/locking or safe task-ID reuse.

## Exact bridge and rationale

GCC-facing symbol `_ep7_gcc_get_tid` (leading underscore). Five instructions /17bytes:
1. `movm [a2],(sp)`
2. `add -12,sp`
3. `mov d0,a0`
4. `call ep7_stock_get_tid_unresolved,[a2],4`
5. `ret [a2],16`

The own-save/reserve/return envelope is exactly the generated GNU13.4.0 `_probe_query` nonleaf envelope. Only argument routing and the inner call's native save/frame tuple change. The C caller proof `bridge_caller.c` compiles to `call _ep7_gcc_get_tid,[],0`, then tests d0 and reads its preserved output pointer on success. No native API or compiler-produced target code was executed.

Audited E-P7 API600317ac..600317f0 writes d0/d1/a1/a2, not d2/d3/a3. It ends at600317ed with **RETF[a2],4**, and its observed native caller612c78ef uses CALL[a2],4. Native a2 is restored by that call/return pair; bridge's independent saved a2 is restored again at the GCC boundary. d2/d3/a3 are untouched. d0 retains native status (0 or-25 in reviewed paths). a0/a1/d1, MDR and condition flags are GCC call-clobbered and **not promised preserved**. This is callable-function translation only, never a transparent arbitrary mid-instruction observer. Extended-register preservation and alternative native versions are not admitted.

## Return-frame proof, not a guessed RET

Independent static semantics source: GNU binutils-gdb simulator `sim/mn10300/mn10300.igen`, revision `87ffb882e0f4d73401a0746177ffabb8e8bbe4ac`, SHA256 `355754c61879dc24bf6128bbba5a7931355731000e8cb213082b9b9cd4df0129`. Retrieved read-only from https://gnu.googlesource.com/binutils-gdb/+/87ffb882e0f4d73401a0746177ffabb8e8bbe4ac/sim/mn10300/mn10300.igen ; hash matches pinned original in repository tools/prepare_mn103_sim.py. No simulator was built or run, no firmware executed, and no upstream source needs redistribution.

CALL32 block atlines4276..4381 stores next_pc at oldSP, saves selected registers below it, decrements actualSP solely by immediate, and setsMDR=next_pc. RET block4385..4485 first adds immediate, restores selected registers below resultingSP, and reads returnPC from[resultSP]. RETF block4490..4588 instead returns viaMDR after the same stack adjustment/restores. GCC verified source mn10300.h INCOMING_RETURN_ADDR_RTX likewise places incoming return at[SP].

Let entrySP=S and original GCC return address be[S]. Own MOVM saves caller a2 atS-4; add-12 givesS-16. Inner CALL saves its return atS-16 and a2 atS-20, then native entrySP=S-20. Native RETF[a2],4 restoresSP=S-16, a2 fromS-20 and jumps back viaMDR. Final **RET[a2],16** restoresSP=S, a2 fromS-4 and returnPC from[S]. Final RETF would be wrong because MDR now holds the inner return. No allocation touches the original return slot. Required stack reserve below entry is20bytes for this exact path; target stack sizing/interrupt margin still not qualified.

## Reproduction and boundaries

`check_get_tid_bridge.py` hashes trusted compiler/cc1/gas/objdump, assembles bridge to temporary relocatable ELF, checks exactfive instructions/native mask4/onePCREL32 relocation/text17, compiles the C caller, and performs a self-authored host integer stack model for success and-25 paths. It does NOT emulate instructions or validate silicon. Temporary objects are deleted. `research/ep7/get-tid-bridge-compile.json` records the actual successful run; `test_get_tid_bridge.py` checks tool/RET-mutation rejection as well.

Before any target use: independent review of this contract and exactstock API hash; explicit relocation/link policy; native context and stack safety; task-instance lease provision; caller-owned output and serialization; installation/recovery approval. This candidate is useful concrete glue, not an installed callback and not flash-ready firmware.
