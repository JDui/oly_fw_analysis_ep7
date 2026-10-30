# E-P7 HSL port: research status

Status: **incomplete; no E-P7 firmware patch, install image, device execution or
claim of flash safety**. Initial source review: 2026-10-30. Baseline:
[`539fcf1fa9eda5fdef8ede4deeab94a4691d94c3`](https://github.com/fishcu/oly_fw_analysis/commit/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3).
The substantive upstream source arrived in
[`422e415`](https://github.com/fishcu/oly_fw_analysis/commit/422e415); the next commit
only links PEN-F releases. No E-P7 HSL implementation was found in that tree.

## Evidence levels

- **Reviewed source:** verified that the cited repository contains the contracts
  below. This does not mean its proprietary firmware probes were rerun here.
- **Actual stock validation:** the exact official 1.1/1100 file was obtained and
  the selected assertions below were checked against its bytes. This remains
  static analysis, not execution of firmware or an ISP/pixel test.
- **Upstream exact-build finding:** other mappings remain inherited unless named
  in the local audit result or static-analysis report.
- **Proposal / unknown:** not an address, hardware fact or working feature.

The bare URL in upstream provenance initially returned HTTP 403. Further review
found that upstream deliberately strips temporary signature query parameters.
The documented **public official catalog** returned a fresh download URL, which
successfully supplied the exact stock file. No authentication was bypassed and
no third-party mirror was needed. Only the unsigned source attribution and
hashes are retained in [the source record](../../research/ep7/stock-source-1100.json);
the signed response and firmware remain local. The catalog offered 1100 during
this query; **1.1/1100 is our pinned research target**, not a statement about
the user's installed version or every regional updater result.

### Locally verified milestone

[Actual stock audit](../../research/ep7/stock-audit-1100.json), 2026-10-30:
111017984 bytes; exact full-file SHA, five decoded component hashes/checksums,
full decode/encode round trip, main runtime mapping, unique 3028-byte COLOR table,
selector-to-builder call, default accessor, and COLOR1–4 defaults and dispatch
pointers all passed. Public profile modes are **54,55,56,64**, not four contiguous
values. Address-window fingerprints are recorded without redistributing code.

### Actual profile/cursor disassembly

[Static path result](../../research/ep7/static-paths-1100.json) was reproduced with
[GNU Binutils 2.45](https://lists.gnu.org/archive/html/info-gnu/2025-07/msg00009.html),
built locally from official source whose SHA-256 matched the release announcement:
`c50c0e7f9cb188980e2cc97e4537626b1672441815587f1eab69d2a1bfbef5d2`.
This is source-checksum verification, not a claim of GPG signature verification.

- All four profile cases read the expected contrast/sharpness/tone/shading and
  twelve saturation property IDs through `0x602b2237`. The first three case
  windows contain 17 direct calls and share their final getter in case 4; case 4
  contains 18. These are settings **read** paths, not commit/persistence proof.
- Cursor window `0x60de83b7..0x60de857f` checks property IDs
  **1091,1096,1097,1686**, then reads related IDs **1098,1099,1100,1687**.
  The fourth pair is noncontiguous again. The routine compares **255** and **12**,
  calls virtual methods through helper `0x607f9062`, and writes a halfword at
  child offset **+90**. This is a concrete starting point for the ALL/remembered
  cursor model; the related IDs' full storage semantics and physical callers are
  still not proven. Do not relabel them as GPIO/keycodes or free H/L storage.
- The actual operand checks are pinned to instruction addresses, not substring
  matches anywhere in a firmware blob. Complete disassembly stays local.

Reproduce after building a trusted MN103 objdump using the existing
[GNU build instructions](../../patches/hsl/pen-f/README.md):

```sh
python3 tools/ep7_static_paths.py --stock /local/path/OLY_E_142_1100_0000_0000.BIN \
  --objdump /trusted/path/to/mn10300-elf-objdump > generated/ep7/static-paths.json
python3 -m unittest discover -s tests -p 'test_ep7*.py'
```

The tool checks the stock identity before invoking the explicitly selected
disassembler; it uses a deleted-on-exit temporary decoded input and emits no
code listing. Never point `--objdump` at an untrusted executable. No firmware is
executed by disassembly. Seven E-P7 synthetic/guard tests and nine container tests
pass; the separate exact-stock and static-disassembly runs both pass.

## Why this is plausible, but not a simple button remap

[`compare_color_generations.py`](../../tools/compare_color_generations.py) records
a shared 3028-byte COLOR table and corresponding MN103 builder across PEN-F,
E-P7 and OM-3. Hue/lightness coefficients existing in a table do **not** establish
editable stock H/L arrays or equivalent ISP behavior. The existing source calls
out this limit explicitly. E-P7 has four profiles; PEN-F patch code hardcodes
three, disjoint storage contracts and different image/request layouts.

### Exact-build compatibility matrix

All addresses below are **upstream research landmarks**, not approved injection
sites. PEN-F column is build 3101; E-P7 column is build 1100 only.

| Contract | PEN-F | E-P7 | Port consequence |
| --- | --- | --- | --- |
| Public/build/model | 3.1 / 3101 / 1220 | 1.1 / 1100 / 1420 | Reject other identities before analysis |
| Main CPU analysis base | `0x60021020` | `0x60020020` | Do not use container address as code base |
| Main container address | `0x403a0000` | `0x406a0000` | Separate address spaces |
| COLOR source table | `0x60622d74` | `0x6051de2c` | Shared table SHA below, not shared address |
| Stock builder | `0x604f7272..0x604f746a` | `0x603b0068..0x603b0247` | Requalify ABI and displaced instructions |
| Stock selector | `0x604f747f..0x604f7572` | `0x603b0252..0x603b0345` | E-P7 table load `0x603b02d3`, call `0x603b02d9` |
| Coefficient writer | `0x604b5006..0x604b51de` | `0x6034667e..0x6034677b` | Different ISP register interface |
| Request S byte offset | 1076 | 1816 | Do not copy image/job offsets |
| 12×24-byte records / control offsets | 676 / 964 | 688 / 976 | Recalculate field access |
| MMIO bases | `0x9e001800`, `0x9e005800` | `0x9f001000`, `0x9f805000` | Never transplant peripheral writes |
| MMIO records / control offsets | 728 / 1016 | 752 / 1040 | Hardware validation still required |
| COLOR profile S starting IDs | 931, 943, 955 | **927, 939, 951, 1655** | COLOR4 cannot use `base+12*profile` |
| Profile defaults table | `0x603c8bb0` | `0x604a8774` | Four-profile resets must preserve factory S |
| H/L saved cells | Validated PEN-F part-1 reuse | Unknown | No assumption that padding/part 1 is free |
| Editor/input hooks | PEN-F mapped | Physical UI documented; event/ABI map unknown | Read [controls proposal](CONTROLS.md) |
| Capture/job H/L ownership | PEN-F mapped | Unknown | Live-view-only success is insufficient |
| Updated-image acceptance/recovery | PEN-F-specific evidence | Not established | No E-P7 install instructions |

Additional E-P7 leads from
[`compare_color_profile_defaults.py`](../../tools/compare_color_profile_defaults.py):
getter `0x602b2237`; profile dispatch table `0x60460458`; COLOR1–4 cases
`0x602b814e`, `0x602b823c`, `0x602b832a`, `0x602b8418` (end `0x602b850d`);
cursor window `0x60de83b7..0x60de857f`. These are candidates for static analysis,
not confirmed hook boundaries. Shared table SHA-256:
`a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531`.

## Actual PEN-F patch dependency map

See [`patches/hsl/pen-f`](../../patches/hsl/pen-f/README.md). Its modules are not
independently switchable; copying just the color hook would lose ownership.

1. `src/image_parameters/image_parameters.s`: `hl_override` calls the stock
   builder, preserves registers/MDR, validates one of 16 operation records and
   its parent, then reads 24 H/L bytes from the image-owned job extension.
   `layout.ld` pins the hook at **PEN-F-only `0x604f7506`** and extension at
   `0x6069b2b0`. E-P7 job size, callback identity and record layout remain unknown.
2. `src/editor_storage/editor.s`: common dispatcher intercepts `0x9016`
   (documented Delete), validates COLOR state/children/modal/held controls, cycles
   axes and refreshes cached child indices and viewer. `layout.ld` pins dispatcher
   **PEN-F-only `0x60bcba63`**, setter `0x6073659d`, wheel `0x6081b83a`.
   It derives profile properties from 931 and three profiles—wrong on E-P7.
   This is GUI-event handling, **not a portable physical keyscan driver**.
3. `settings.s`, `settings_lifecycle.s`: tagged/complement-checked H/L cells,
   bank copies, active/staged publication and defaults. PEN-F uses part 1 of
   IDs931–966 only after a usage audit; E-P7 needs a fresh nonvolatile-store audit.
4. `image_transport.s`: snapshots for capture/compact/recording ownership and
   conversion to jobs. Never read a later UI profile for an already captured frame.
5. `raw_development`, `orf_metadata`, `settings_backup`, `wifi`: independent
   consumers/serialization surfaces must be mapped, deliberately unsupported, or
   neutralized safely—not accidentally supplied stale H/L.
6. `extended_range`: PEN-F's ±7 touches enums, numeric text, wheel, ALL and backup
   conversion. Start E-P7 S at native range; no H/L limits are qualified yet.

The detailed [PEN-F state/lifetime map](../color/pen-f/EDIT_AND_CAPTURE_MAP.md)
and [structures](../color/pen-f/STRUCTURES.md) distinguish saved values, effective
parameters, editor scratch, capture owners and processing jobs. Internal commit
event `0x900c` is **not necessarily a physical OK press**. A new menu's “Cancel”
cannot be promised without staging/rollback semantics.

## Reproduce the safe first stage

Obtain the stock input separately under its applicable terms. Expected filename
`OLY_E_142_1100_0000_0000.BIN`, 111017984 bytes, SHA-256
`9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`.
Its decoded main SHA is
`5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190`.
Source URL and all five component identities are retained in
[`provenance/firmware-inventory.json`](../../provenance/firmware-inventory.json).

```sh
python3 -m unittest discover -s tests -p test_ep7_stock_audit.py
python3 -m unittest discover -s tests -p test_oly_container.py
mkdir -p generated/ep7
python3 tools/ep7_stock_audit.py --stock /local/path/OLY_E_142_1100_0000_0000.BIN \
  > generated/ep7/stock-audit.json
```

The new E-P7-only audit does not require PEN-F/OM-3 images or GNU objdump. It
checks exact identity **before parsing**, all component identities/checksums,
decode/encode round trip, runtime-base witness, shared table uniqueness,
selector-to-builder call, default accessor and all four saturation defaults and
dispatch pointers. It records static-window hashes. It emits hashes and
non-payload metadata, no extracted firmware strings or disassembly. It produces no
patched BIN and exposes no relaxed-hash/force option.

Seven E-P7 input-free tests and nine existing synthetic container tests pass.
The real-stock audit also passed separately; these are different evidence levels.
Native emulator/ISP, full camera boot, real input, capture and flashing checks
have not been run.
Keep all stock/decoded files and private captures local and ignored.

## Gated port plan and acceptance criteria

1. **Identity / static reproduction:** acquire exact input, run audit and retain
   its hash-only report. Disassemble reviewed ranges with a trusted MN103 toolchain.
   Pin any different firmware as a separate target; never weaken identity checks.
2. **Editor / input map:** trace switch/u entry through E-P7 FSM, resolve Delete,
   INFO, dials and arrow events, four profile selectors, held-key timers and modal
   passthrough. Establish stock edit/commit/reset behavior before hooking anything.
3. **Settings / ownership:** map four-profile get/set/default callbacks, effective
   refresh and all bank lifecycle paths. Prove extension storage unused, versioned,
   bounds-checked and neutral on invalid data; identify capture/compact/job copies.
4. **Offline H/L prototype:** only after ABI/storage evidence, design E-P7-specific
   hooks with expected old bytes, nonoverlap/size/hash checks and fail-closed unknown
   owners. Validate neutral equivalence, every sector, every profile, saturation
   unchanged, stale-owner reuse and profile changes during capture. No flash output
   before separate updater/recovery review.
5. **Integration:** text+polygon+axis indicators, ALL bounds/reset, power/profile
   transitions, JPEG/RAW/ORF semantics, backup/restore, remote edits, movie/unsupported
   contexts. Document intentionally unsupported paths explicitly.
6. **Hardware gate:** separately authorized camera tests and independently reviewed
   update/recovery procedure, then neutral pixel comparison and bounded H/L image
   effects across sectors. A checksum or MN103 probe is not ISP qualification.

The exact-stock acquisition blocker is resolved. The user's current camera
version is still needed before any device-specific compatibility claim; a different
firmware must be scoped and audited separately. This does not block continued
static research. No camera writes are authorized by this research milestone.

## Rights

Preserve upstream attribution and component notices. No broad license is inferred
from a public repository. No firmware blobs or bulk disassembly are added. Hashes
establish identity, not redistribution rights. See
[RIGHTS-AND-PROVENANCE.md](../../RIGHTS-AND-PROVENANCE.md).
