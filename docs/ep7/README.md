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
- **Upstream exact-build finding:** independently revalidation-ready, but currently
  inherited from upstream. Requires the matching stock file to confirm locally.
- **Proposal / unknown:** not an address, hardware fact or working feature.

The official stock URL listed in upstream provenance returned HTTP 403 during
this session; no image was downloaded. We did not bypass it or substitute an
unverified mirror. The exact current public firmware version is not independently
established here; **1.1/1100 is the pinned research target, not a latest-version claim**.

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
selector-to-builder call and all four saturation defaults. It emits hashes and
non-payload metadata, no extracted firmware strings or disassembly. It produces no
patched BIN and exposes no relaxed-hash/force option.

Input-free guard tests and existing synthetic container tests can pass without
firmware. They **do not** mean the real-stock audit passed. Native emulator/ISP,
full camera boot, real input, capture and flashing checks have not been run.
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

Next needed input is the exact stock file (or a different file plus its identity
for a separately scoped audit), and eventually the user's current camera version.
Neither blocks continued static research. No camera writes are authorized by this
research milestone.

## Rights

Preserve upstream attribution and component notices. No broad license is inferred
from a public repository. No firmware blobs or bulk disassembly are added. Hashes
establish identity, not redistribution rights. See
[RIGHTS-AND-PROVENANCE.md](../../RIGHTS-AND-PROVENANCE.md).
