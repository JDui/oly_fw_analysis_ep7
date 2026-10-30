# Native post-builder → actual target C observer

Compile-only integration: native-frame bridge → 32-bit setup decoder adapter →
`ep7p_direct_apply`. The latter performs locked live-allocation lookup and bounded
request decoding before CPU coefficient writes. Neither an initialized native
runtime nor hook installation is supplied; trusted synchronous lifetime and
request stability remain required. This direct path does not need a task-ID or
universal task-epoch prerequisite.

Only self-authored source, tests and notes are here. No firmware data, object,
linked image or executable target output is committed or executed.

From repository root, using the locally verified toolchain described in
[`../build-manifest.json`](../build-manifest.json):

```sh
python prototypes/ep7_volatile_hl/target/postbuilder/check_bridge.py
python prototypes/ep7_volatile_hl/target/postbuilder/check_native_observer.py
python prototypes/ep7_volatile_hl/target/postbuilder/check_loopstate.py
python prototypes/ep7_volatile_hl/target/postbuilder/check_stack_usage.py
python prototypes/ep7_volatile_hl/target/postbuilder/test_postbuilder.py
python prototypes/ep7_volatile_hl/target/postbuilder/seam_probe.py \
  --stock /path/to/locally-owned-EP7-1100.BIN \
  --objdump toolchains/binutils-2.45-build/binutils/objdump
```

Checkers compile only into temporary directories; the stock probe reads only
exact-hash firmware and invokes trusted static disassembly. Reports:
`research/ep7/postbuilder-{bridge,native-observer,loopstate,stack,seam}.json`.

[NOTES.md](NOTES.md) distinguishes proven instruction/frame facts from native
flags, loop-state, stack-budget and installation limits. `observer_probe.c` is
an earlier ABI-only demonstration; **`native_observer.c` is the actual adapter**.
Neither has been run on a camera. The bridge's stock-builder and observer targets
remain symbolic relocations in separate, unlinked objects.
