# GNU MN10300 compile-only ABI study (local build passed)

All source archives fetched from gcc.gnu.org over HTTPS; GCC13.4.0 archive SHA512 verified against official release sha512.sum. GMP6.2.1/MPFR4.1.0/MPC1.2.1 verified against contrib/prerequisites.sha512 inside that verified archive. No signature verification claimed. Local cross C compiler only, no system installation or target execution. Build manifest records hashes/options.

Primary sources: https://gcc.gnu.org/onlinedocs/gcc-13.4.0/gcc/MN10300-Options.html and https://gcc.gnu.org/install/prerequisites.html ; local verified source gcc/config/mn10300/mn10300.{h,cc,md}.

## Source-established mismatch confirmed by generated probes

- Backend function_arg uses only first two argument words in d0/d1, irrespective of pointer type. Additional words use stack; REG_PARM_STACK_SPACE=8, STACK_POINTER_OFFSET=4, FIRST_PARM_OFFSET=4. Compare E-P7 native get_tid a0, constructor a0/a1 with d0 scalar: NOT an ordinary GCC C ABI call.
- Pointer results normally emitted in a0 plus d0 (default -mreturn-pointer-on-d0); consumers rely on a0. Native constructor caller consumes d0; native UI factory consumes a0. Matching one output register does not establish entire ABI compatibility.
- CALL_REALLY_USED_REGISTERS: d0/d1/a0/a1/MDR/condition code are call-clobbered; d2/d3/a2/a3 callee-saved. Compiler saves used callee-saved registers in its own prologue. Direct call instruction pattern is `call symbol,[],0`; indirect `calls (areg)`. Native callers often encode callee save-mask/frame size in call instructions, so these cannot be mixed without an explicit boundary adapter.
- Backend permits RETF only for optimized leaf without MDR use; otherwise return linkage differs. MDR and flags are not transparent across arbitrary compiled C. Loop registers are not promised preserved by generic C API.

No native compiler compatibility, microarchitecture choice (base MN10300 vs AM33/AM34), syscall ABI, lock implementation, target runtime memcpy/memset/libgcc, installation or flash readiness is inferred. Compile base MN10300 first; AM33 features are not enabled speculatively. All externals stay unresolved.

## Actual compilation outcome

C-only GCC13.4.0 cross build completed successfully (`all-gcc`, no target libraries or installation). `probe.c`, current portable `ep7p.c`, and `ep7p_ui.c` compile with strict C11, -O2, -ffreestanding, -fno-builtin to base MN10300 assembly; trusted GNU gas assembles ELF32-MN10300 relocatable objects. No target executable was linked or run. Locally supplied string.h contains ONLY self-authored standard declarations, not runtime implementations.

Generated probe observations:
- Pointer argument p arrives in d0: `_probe_load` starts `mov d0,a0`; integer second arg remains d1.
- Third/fourth 32-bit args load from ENTRY sp+12/+16 (not sp+4/+8). Nonleaf with28-byte frame reads its third argument at sp+40 then stores outgoing third arg at sp+12.
- `_probe_query` self-saves a2 using `movm [a2],(sp)`, reserves12bytes, calls `_foreign_query_unresolved,[],0`, returns `ret [a2],16`. Native query caller instead passes output in a0 with `call 600317ac,[a2],4`. A tail-forwarder previously assembled for NATIVE callers cannot be used as a GCC-facing function.
- `_probe_pointer` leaves p in d0 and copies to a0. `_probe_pointer_call` consumes returned pointer in a0 explicitly.
- `_probe_div` saves d2, writes zero to MDR, issues divu, returns `ret [d2],4`; nonclobbering leaf integer addition returns `retf [],0`. Caller return linkage/MDR must be handled in veneers, not assumed transparent.
- C symbols acquire a leading underscore. Previous standalone forwarder symbols lack it. This is another link-level mismatch, not fixed by copying native addresses.

Core object has only `_memset` and `_memcpy` unresolved, no libgcc arithmetic helper in this exact build. UI object has `_memset`, `_ep7p_axis_read`, `_ep7p_axis_adjust_result` unresolved. This absence is specific to current source/options; future builds must re-audit. Native memcpy/memset addresses must NOT be bound as ordinary GCC calls because argument ABI differs. Self-authored freestanding implementations and a GCC-to-native get_tid bridge are now included with compile/stack-contract tests; they remain unlinked and uninstalled. No native task-instance generation/lock/ownership adapter exists yet.

`check_target_compile.py` rehashes xgcc/cc1/gas/objdump before compiling, verifies ELF architecture and exact unresolved sets, asserts generated ABI witnesses, emits hashes only, and cleans temporary artifacts. `research/ep7/target-c-compile.json` records successful run and no target execution. The integrated target checker also compiles frozen ep7p_decode.c and reviewed self-authored memory.c; both have zero unresolved symbols. Build log remains local toolchains/gcc-13.4.0-mn10300-build/build.log. SHA512 sources and build options in build-manifest.json. This directory publishes only self-authored probes/scripts/metadata/notes, not GCC trees, binaries, build objects or vendor firmware.
