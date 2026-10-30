# Compile-only target C and native ABI boundary

These are self-authored probes, a proposed GCC/native `get_tid` bridge, and
freestanding byte operations. **No linked target executable, installer or firmware
image is produced. No target or firmware code is executed.** Host memory tests
execute only self-authored code under the host compiler.

The verified local GNU GCC13.4.0 / binutils2.45 toolchain is not committed.
`build-manifest.json` records official source URLs, SHA512 verification, build
options and exact local tool hashes. GNU source/build trees and compiler binaries
remain ignored. No system installation was performed. A rebuild on another host
may have different tool hashes: independently establish provenance and review
those identities rather than bypassing the guards.

From repository root:

```sh
python prototypes/ep7_volatile_hl/target/check_target_compile.py
python prototypes/ep7_volatile_hl/target/check_get_tid_bridge.py
python prototypes/ep7_volatile_hl/target/check_memory.py
python prototypes/ep7_volatile_hl/target/test_target_compile.py
python prototypes/ep7_volatile_hl/target/test_get_tid_bridge.py
```

Checkers use temporary directories and emit JSON metadata, not assembly dumps or
objects. Published runs are `research/ep7/target-c-compile.json`,
`get-tid-bridge-compile.json`, and `freestanding-memory-host-target.json`.

The target checker covers the portable core, normalized UI, bounded job-buffer
decoder, self-authored memory functions and ABI probes. Core/UI references remain
unresolved in separate objects; memory/decoder have no unresolved symbols. No
link is attempted, and no native memcpy/memset address is substituted.

See [ABI-NOTES.md](ABI-NOTES.md) for concrete GCC/native calling-convention
mismatches, [GET-TID-BRIDGE.md](GET-TID-BRIDGE.md) for the five-instruction bridge
and stack proof, and [MEMORY.md](MEMORY.md) for host memory-operation tests.
Native task-instance generations, synchronization, capture attachment, hardware
execution and installation remain separate unimplemented boundaries.
