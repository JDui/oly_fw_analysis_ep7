# E-P7 packaging, updater and recovery feasibility — bounded stock audit

2026-11-01 update: the [candidate004 research container](CANDIDATE_PACKAGE.md)
has now been built using the inherited fishcu workflow, without SHA checks.
All five E-P7 components are retained. The older unchanged-stock audit below
remains historical evidence; its “no modified image built” statement is no longer
the current packaging status. Updater acceptance and recovery remain unproven.

## Useful engineering conclusion

Packaging is not currently a demonstrated cryptographic roadblock: the exact E-P71.1 file can be decoded/re-encoded byte-identically and every observed component checksum can be independently recomputed. E-P7 native code itself contains the matching additive-sum check and local main-checksum failure0x3211. **This does not prove absence of authentication elsewhere, acceptance of modified code, or a recoverable device.** The highest-risk remaining installation gates are E-P7-specific updater acceptance/physical entry and recovery after main corruption, not writing another generic packer.

No modified or flash-ready image was built. The audit compares each unchanged reconstructed component in memory to the original bytes, streams a whole-file hash, and emits JSON only. Native code is disassembled but not run. Temporary decoded input is removed. This is stronger than merely observing that a generic packer exists, but is not a camera update test.

## Actual stock and component restrictions

Exact source SHA256:9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb;111017984bytes; model identifier bytes1420 in all five headers. Preserve model bytes literally, not decimal formatting guesses. Public1.1 corresponds to main headerbuild0x1100. Other component build fields differ and MUST NOT all be rewritten to1100.

|Kind|Container address|Payload bytes|Header build|
|---|---|---:|---|
|0100|406a0000|26214336|1100|
|0101|421a0000|26214336|0100|
|0106|43aa0000|45219776|0100|
|010e|00000000|262080|0001|
|0102|467e0000|13107136|0100|

Main disassemblybase60020020 is not containeraddress406a0000. Small component010e ataddress0 is not, merely by size/address, proof of an immutable recovery ROM or complete reset image. Existing ep7_stock_audit establishes a main entry mapping, not power-on boot selection or independent rescue.

## Integrity versus authentication

Each component has32byte header,16-byte-aligned scrambled payload,32byte trailer. The first28 header/trailer bytes agree; trailing u32 checksum makes little-endian sum(header+decodedpayload+trailer)=0 modulo2^32. Reversal is fixed byte-permutation plus XORff, not keyed encryption. The five recomputed checksum words match stock and every no-op encoded component is byte-identical, producing original whole-file SHA. No payload change is needed for this proof.

In exact E-P7 main, helper600fa454..462 sums u32 words (d2 accumulator, d0 length>>2) and returns sum. Local checker60c95a43..b09 uses payloadlength+64 on ordinary packaged branch, compares header/trailer words in a five-iteration loop, invokes sumhelper at5abc, accepts zero locally, and returns0x3211 for nonzero sum with second magic byte'E'. Host parser's seven-word metadata equality is deliberately stronger than this particular five-word native loop; do not equate their entire acceptance policies. Wrapper60c9718c conditionally calls in-place byte decoder60c95b0c, then checker5a43. Decoder's inversion loop5b9d..ba0 is also pinned. These are static local operands, not an executed validation experiment or a complete callgraph proof that no separate signature/version/model/hardware check occurs earlier/later.

SHA256 values here establish equality to the audited input, not a vendor digital signature. Vendor HTTPS download provenance is separate from on-device authenticated boot. No E-P7 cryptographic-authentication requirement or absence thereof has been established by this bounded pass.

## E-P7-specific updater leads versus recovery evidence

Exact stock strings include S142????BIN at60f2cb24, E142????BIN at60f2cb30 and60f2d81c, and DCOLYMP at60f2cd07. Some pointer references are data tables, not executed instructions. These support investigating a model-specific SD-client route, **not** instructions to rename a file or hold a PEN-F button combination. They do not prove physical entry, same-version acceptance, downgrade, partial-component acceptance, automatic rollback, boot-ROM immutability or rescue when main cannot start.

Upstream docs/boot/pen-f/RECOVERY.md and docs/format/CONTAINERS.md document PEN-F3101 native fixtures/physical reports for partial updates, same-version/restoration and specific failure recovery. Those explicitly retain limits even on PEN-F. They do not qualify E-P7. tools/penf_repack_preflight.py and PEN-F HSL patch packaging likewise remain model-specific. Do not transplant E122 filenames, offsets, BOOT destinations, taskIDs or OK+power assumptions.

Official [firmware index](https://support.jp.omsystem.com/jp/support/cs/dslr/fw/index.html) lists E-P7 version1.1 dated2022-02-28 and the OM Workspace route. Official [Workspace update guidance](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/contents/ow/ow_a2.html), checked2026-10-30, describes normal USB updates, reports latest-version systems as needing no update, requires sufficient power and waiting for the camera's OK display, and warns interruption can make the camera inoperable. It supplies no E-P7 custom-image or dead-main rescue guarantee. Normal vendor update availability is not same-version modified-image acceptance.

## Gates and next bounded work

1. **Done offline:** exact stock identity, five additivechecksums, unchanged byte roundtrip, local E-P7 decoder/checker landmarks. Generic same-size payload replacement exists but is not an E-P7 safety qualification.
2. **Still open static:** identify complete E-P7 validation/model/build/length/service-mode pipeline and write dispatch, test acceptance semantics in a separately reviewed non-writing harness, establish loaded code placement/relocations. No boot or flash effects can be inferred from source compiling.
3. **Still open physical:** independent body/version readback (the user already reports E-P7 1.1), authorized bench plan and an independently qualified recovery method for the intended failure domain. No proven E-P7 independent USB/ROM rescue or safe stock restoration after main-entry corruption in this work. Absence of proof is not proof that recovery is impossible; do not promise recoverability.
4. **Only after separate authorization/qualification:** modified-image acceptance and boot/runtime/pixel validation. Current research permission does not authorize flashing or writing camera firmware.

A credible ETA must distinguish an offline candidate from safe-to-flash/device-validated HSL. Successful container checks remove a serialization uncertainty, not the device-risk gates; no defensible safe firmware date follows solely from these results.

## Reproduction

Scratch packaging_recovery_probe.py checks29 instruction witnesses, four exact filename/path string leads, all five component sums and literal byte equality of unchanged encoded blocks. packaging_recovery_report.json contains hashes/metadata/explicit false safety claims, no vendor blob. packaging_recovery_test.py:2 tests passed locally; actualstock integration skips without private input/trustedtool. Suppliedobjdump hash is recorded, not allowlist-verified by this probe. No firmware execution or image output.


Canonical tool: `tools/ep7_packaging_recovery.py`; tests: `tests/test_ep7_packaging_recovery.py`. No image is output. Private input and trusted toolchain are optional prerequisites, not bundled.
