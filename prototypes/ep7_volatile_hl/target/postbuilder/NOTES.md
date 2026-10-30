# Native COLOR post-builder → GCC observer seam

Exact E-P7 1100 stock, SHA2569d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb. Self-authored, compile-only ABI candidate, no installation/linking/target execution. `seam_probe.py` verifies33 exact instruction/operand witnesses in6windows and hashes the windows. `check_bridge.py` compiles/assembles self-authored code and checks all16 bridge instructions and2 unresolved relocations; host arithmetic stack model is NOT instruction emulation. Nine tests pass, including target-only actual observer and current compiled-object loop-state checks.

## Proven native seam

Selector603b0252 keeps setup in a2; request=setup+4. On the exact COLOR branch it loads native output=setup+12 into d1 at603b02c5, points a1 to request+1816, loads original scalar/table arguments, then603b02d9 CALLs603b0068 with[d2,d3,a2,a3],96. Original builder returns at603b0244 using RET[d2,d3,a2,a3],96, so setup a2 is restored. Proposed replacement is at this **call site only**, not a replacement for every entry to603b0068.

Wrapper first calls ORIGINAL unresolved builder with the SAME tuple96, forwarding d0/d1/a0/a1 unchanged. It then passes restored setup froma2 tod0 into an unresolved ordinary GCC observer, and finally uses native RET[d2,d3,a2,a3],96. The real target-only translation is now `native_observer.c`: it byte-loads setup+4/request and setup+12/output, then calls ep7p_direct_apply on an external initialized core runtime. Runtime initialization/admission remain unbound. `observer_probe.c` is retained solely as an earlier nonleaf ABI probe, not the real observer. No native memory is read during compilation/tests.

## Liveness findings and conservative choice

At603b02de d0 is overwritten fromsetup+60;603b02e1 BTST establishes the subsequent branch condition. All paths reachable from this continuation either return at603b02ed or load/store viaa2 and return603b0342. d1/a1/MDR are not consumed in these selector tails; a0 is either overwritten or passes through until parent603b14f8 overwrites it. Parent's nextcallee603b0a70 overwritesd0/d1, but one early branch can leavea1 unchanged until it returns, so an all-transitive a1-dead argument would require more code. This pass deliberately does NOT make that broad claim.

Instead wrapper saves post-builder d0,d1,a0,a1,MDR at ownframe+12,+16,+20,+24,+28 and restores them after observer. This avoids needing full volatile-register liveness. PSW is NOT saved/written: the exact continuation overwrites the relevant condition viaBTST before any conditional use, and writing fullPSW would add unjustified privileged/interrupt-mask semantics. No all-purpose transparent-midfunction claim is made. d2,d3,a2,a3 are restored by native finalRET; GCC callees independently preserve these registers per verified compiler ABI.

MDR finalreturn MUST use RET, not RETF: observer call replacesMDR with inner return. Saved post-builderMDR is restored but final returnPC comes from native outer stack slot. This does not establish arbitrary hardware flag/control state preservation. Observer/build use baseMN10300, with `-mno-setlb -mno-liw`; the actual emitted observer has no LIR/LAR/SETLB use. Every eventual helper must stay within this reviewed CPU ABI and loop/control-state contract, or additional preservation analysis is required. Unknown native helpers are not silently admitted.

## Stack layout and proof

Use the already verified pinned GNU simulator CALL/RET semantics from ../GET-TID-BRIDGE.md (source SHA355754c61879dc24bf6128bbba5a7931355731000e8cb213082b9b9cd4df0129, read-only reference only).

Let C=selector's SP before its original CALL96; wrapperentryS=C-96. Outer native saves are at S+92(d2),+88(d3),+84(a2),+80(a3); original returnPC atS+96. Wrapper nested CALL96 writes its own return at[S], saves its callee registers[S-4..S-16], and enters originalbuilder atS-96. Original builder's 0..76 locals remain below these inner saved slots; its RET96 restoresSP=S and setupa2. This adds96bytes of native call depth versus original execution; **actual task-stack headroom is unqualified**.

GCC observer call uses[],0, so returnPC goes at[S], caller-provided register-flush area is[S+4..S+11]. Saved post-builder volatile state[S+12..S+31] is disjoint from both that area and native outer savedregs[S+80..S+95]/return[S+96]. GCC observer owns its own downward stack frame; actual observer savesd2/d3 then reserves20 and returns28, returningSP=S. Final native RET96 advancesSP=C, restoresoriginalcallee registers fromC-4..C-16 and reads originalPC[C]. No outer return slot is reused by either innercall.

Stack model substitutes arbitrary native/observer values and checks restoration/slot separation. It cannot prove target stack capacity, interrupt safety, locks, scheduling, target execution or external helper adherence.

## Remaining actionable installation boundaries

- Real observer must recover independently qualified live allocation membership and decode only bounded buffers before the CPU scalar writer; setup alone is NOT fresh allocation provenance. For this strictly synchronous seam, direct live-allocation lookup under the same lock can replace task-scoped lookup if request stability, lifetime/free ordering and ABA exclusion are established. Task ID/epoch is not inherently mandatory for that alternative; neither alternative is implemented by this bridge. Invalid/unsupported path must leave original builder output unchanged.
- Preserve only allowed coefficient lanes; do not mutate setup flags/pointers/request/lifecycle fields in the observer. Call must finish synchronously; never retain stack/source pointers or pass H/L storage toDMA.
- Native original call603b02d9 is a5-byte relative16 CALL. Unresolved bridge calls assemble as7-byte relative32 instructions, but no installer exists. Hook placement must satisfy actual relative range or independently reviewed trampoline/displaced-instruction logic; never overwrite following instruction blindly.
- Actual stack budget, concurrency, compiler register/control-state restrictions, exception/unwind behavior, relocation/cache/installation recovery remain unbound. This concrete seam reduces the generic midfunction-ABI concern; it does not make firmware flash-ready.

Deliver self-authored sources/checkers/tests/reports/notes only; no firmware listings or object files for publication. Published sources are under prototypes/ep7_volatile_hl/target/postbuilder; all compile artifacts are temporary and removed. Reports are under research/ep7/postbuilder-*.json. No installer is provided.

## Follow-through: LAR/LIR and the actual compiled objects

Native builder SETLB603b00cf and LLT603b01c5 are now explicit SHA-guarded witnesses. SETLB writesLIR/LAR; therefore the original call already does not preserve the caller's incoming loop state. The exact post603b02de continuation paths to603b02ed/603b0342 contain no loop instruction, LIR/LAR read, or nestedcall; RET masks are onlyd2/d3/a2/a3, not`other`. They cannot consume stale loop state. This local proof is sufficient for the bounded immediate tail; we do not claim a universal transitive loop ABI for every future native helper.

`check_loopstate.py` now recompiles AND disassembles actual current actual observer/core/UI/decoder/memory objects with explicit base target `-mno-setlb -mno-liw`, -ffreestanding/-fno-builtin/-fno-tree-loop-distribute-patterns. None contains SETLB or loop-conditional instructions, LIR/LAR operands, or extended-register operands. `research/ep7/postbuilder-loopstate.json` records source/object hashes and actual mnemonic sets. Thus these reviewed compiled bodies do not introduce loop-state changes; no extra LAR/LIR save is needed for them. The historical probe sink is not installed; unknown lock/unlock callbacks or future helpers remain unqualified. Future real observer call graph must resolve only qualified helpers, or rerun/review the state-use check as it grows. Avoid claiming generic C calls preserve hardware loop state.

No PSW restoration was added: exact site establishes a fresh branch condition before any consumer, so a fullPSWwrite is unnecessary. No blanket extended-register preservation requirement was imposed: current compiled bodies avoid them, and their scope remains explicit.

## Actual target-only observer and direct live admission

`native_observer.c` has both pointer-width static assertions (uintptr_t andvoid* must be32bits). The current64bit host compile is explicitly rejected; the adapter is never executed on the host. It requires a real readable stable setup of>=16bytes, and native-owned output with>=976bytes lifetime throughreturn. It reconstructs little-endian setup+4 and+12 using bytes, so it does not require alignedword loads. The request integer is handed to ep7p_direct_apply, which performs same-lock live-registry matching and bounded decoding before job reads; the setup/output readability/lifetime preconditions cannot be proven by that function. No stale/retained invocation across free/addressreuse is allowed.

External `ep7_native_runtime_unresolved` is a private initialized ep7p object, never a global last-job pointer. No currenttask query appears in this observer or directreader path. The external runtime must be populated by separately qualified lifecycle admission and share revoke-before-free locking; this adapter does not fabricate those capabilities. Returnstatus is intentionally ignored so rejection leaves original coefficient output unchanged.

Bridge relocation now names `_ep7_gcc_postbuilder_observer` (without the old probe's `_unresolved` suffix); actual C defines that underscored symbol. Bridge remains a separate unlinked object. Actual observer object has exactly2 unresolved symbols: `_ep7_native_runtime_unresolved` and `_ep7p_direct_apply`. `check_native_observer.py` checks these symbols, eachof8 byte loads, outgoing output/length argument slots, exactreturn28, absence ofloopops, and host64bit compilation failure. Source/header/tool/object hashes are in research/ep7/postbuilder-native-observer.json. Nothing is linked or installed.

## Compiler-reported stack usage, not a device headroom certificate

`check_stack_usage.py` uses GCC-fstack-usage on actual frozen observer/core/decoder/memory and reports emitted direct/indirect callnames. Current static frames: observer28, direct_apply132, decoder16, shape24, apply_local16, memcpy4, memset0. Hence one known local path observer→direct_apply→shape accounts for28+132+24=184bytes belowwrapper entry. The nested original builder's extra96bytes occur BEFORE the C observer, not simultaneously: do not add96+184 as if those callees overlap. Counting wrapper's preexisting native96 frame, the largest reported known path here reaches280bytes below selector pre-callSP, but this is not an actual worst-case taskstack bound. Unknown lock/unlock callbacks, interruption, compiler changes and othernativeframe obligations remain unmeasured. No kernel-stack search or taskheadroom claim was made.
