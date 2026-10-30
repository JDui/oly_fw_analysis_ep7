# E-P7 1100 storage and CPU-owned H/L design

Status: read-only static evidence and host-only contracts. **No E-P7 patch,
firmware build, device write, or demonstrated HSL image output.** All addresses
below refer only to the exact 1.1/1100 stock identified by the
[source manifest](../../research/ep7/stock-source-1100.json).

## Storage is not one interchangeable array

| Representation | Typed key | Elements | Width |
| --- | --- | --- | --- |
| Effective S, property IDs 915–926 | `f6ea` | 12 | signed 16-bit |
| Four profile S groups | `f6fa` | 48 | signed 16-bit |
| ACTIVE alternate cells | `8b64` | ROM header count 3560 | 32-bit |
| Alternate banks | `85d4` | ROM header count 32040 | 32-bit |
| Raw property staging | `8b54` | ROM header count 1780 | 32-bit |

The property map at `604d6c14` maps COLOR1/2/3/4 respectively to IDs
927–938 / 939–950 / 951–962 / **1655–1666**, and `f6fa` indices 0–47.
The `f6fa` ROM header at `600bddec` therefore describes **96 payload bytes**,
not 48 bytes and not unused H/L space. Its next record starts at `600bde50`.
Typed reader/writer `6005efbd` / `6005eadf` distinguish 16-bit and 32-bit cells.
ROM headers do not prove every runtime registration source or durable storage.

`602cc0a7` / `602cc0d0` read/write ACTIVE indices
`part * 1769 + property`; `602cc076` adds `bank * 3538` for bank reads.
`602cbffe` / `602cc03a` copy 3538 cells between bank and ACTIVE.
The discrepancy between ROM capacity and runtime stride is **not spare-space
proof**. Nine internal bank slots are not nine user-facing custom modes.

All 70 mode/submode filters at `604a8420` contain all 48 profile S IDs once,
with part 0. This makes their part-1 cells a specific *ownership research
candidate*, not an approved allocation. Stock reset `602b962f` writes both
parts for properties 0–1768 and copies ACTIVE into the internal banks.
Therefore part 1 is already touched by native lifecycle operations.

All 48 profile callback records at `604317ac` dispatch mode-appropriate
refresh through `602b8916` to `602b7b71`; the latter writes effective IDs
915–926 via the registered setter. A raw profile/alternate write is not
identical to effective S publication. The typed writer's address-alias double
write is **not evidence of two durable NVM copies or a completed flash save**.

### Recall has an intermediate inconsistent window

On the reviewed conditional recall path, `602b33ec` loads bank 0 into ACTIVE,
`602b33f7` stages selected parts, and `602b3408` conditionally loads the target
bank into ACTIVE. The destination can therefore be in ACTIVE before effective
settings have been committed. This is not an unconditional trace for every entry.

`602b3529` sets inhibit byte `62257b04`; `602b3530` stages context-1 values.
`602b3577` calls `602cc540`, whose main loop commits properties 0–1768 through
inner setter `602cbc74` and collects changed IDs. `602b3587` releases inhibit,
then `602b3597` invokes changed-ID postcallbacks through `602b1ea0`.
Ordinary setter `602cbc5d` skips typed writes while inhibited; the commit loop
intentionally uses the inner setter. This byte is not a proven mutex, and
this commit is not a proven physical NVM flush.

Any future H/L storage design must respect staging and effective publication,
not publish a newly selected ACTIVE value on an arbitrary notification.
The complete context-1 callback expansion, additional commit ranges, concurrent
consumers and physical save/backup semantics remain open.

### Reproduction and format experiment

```sh
python tools/ep7_s_storage.py --stock /local/OLY_E_142_1100_0000_0000.BIN \
  --objdump /trusted/mn10300-objdump
PYTHONPATH=tools python -m unittest discover -s tests -p 'test_ep7*.py'
```

The [report](../../research/ep7/s-storage-1100.json) checks 22 disassembly
windows / 120 instruction witnesses, schema maps, 48 callback records and
70 filters. It rejects wrong stock before invoking objdump. No firmware
bytes or bulk disassembly are included.

[`ep7_hl_storage_design.py`](../../tools/ep7_hl_storage_design.py) models the
upstream PEN-F [H1 format](../../patches/hsl/pen-f/src/editor_storage/settings.s)
(`0x4831CCVV`, complement byte, signed four-bit H and L) with E-P7's four
noncontiguous profile groups. Invalid tag/complement, reset zero, or -8
nibble decodes neutral. It never writes a bank. The ±7 serialization range
is **not an E-P7 pixel calibration**. A 32-bit H1 word must not be packed
into the 16-bit `f6fa` record. Attribution and scoped upstream notices remain
in force; this does not add a repository-wide license.

## Narrower image-owned design: inline values, not a new DMA pointer

An independently reviewed research alternative is to allocate and initialize
24 **new** bytes in the native job, copy immutable capture-time H/L values
there, read them synchronously in a qualified CPU color-builder window, and
write only the existing native coefficient output. No H/L address would be
passed to hardware, queues or asynchronous callbacks.

This is not implemented. Its advantage is a smaller proof obligation:
new H/L storage must survive its last CPU read, while existing native output
continues through its original hardware lifecycle. Global DMA/RTOS quiescence
is not automatically a prerequisite for this *non-escaping value* design.
The earlier external-buffer lifetime warnings still apply to any design
that actually retains or transmits an H/L pointer.

Concrete constructor evidence (`603537eb`): allocation requests **15488**
bytes at `603537f0`; `60353906`–`6035390e` explicitly clears the last 16
bytes at offset 15472. Those bytes are occupied, not padding. The constructor
copies only a 32-byte input header to job+4. Its final destructor free at
`60353ce9` receives the original base pointer, without an explicit size
operand. This supports investigating an enlarged allocation, but alone proves neither allocator class compatibility nor all
constructors/copies/error paths. The dispatcher class question is narrowed below.

### Actual pool class and synchronous builder evidence

The allocator at `60022700` selects classes by upper bounds 128, 2048 and
16384. Both stock 15488 and hypothetical 15512 select class 2 and call
`600228b6`. Its ROM stride table at `60026e34` is `(192, 2112, 16448)`.
This closes the narrow *would +24 cross this dispatcher class?* question: no.
It does not make the stock tail available, initialize new bytes, qualify all
pool/free error paths, or establish allocation provenance. Explicit enlarged
allocation/initialization remains the design requirement, not an implicit
assumption that any pointer into this pool supports a trailer.
See [pool report](../../research/ep7/job-pool-1100.json).

A conditional CPU call chain is now joined:

```text
operation submission 603558ce → 60334ba8 → 60334db4
  → configuration 603396dd → type-0 builder 603397db
  → 60339870 → 603aaced
  → 603b17e6 or 603b1819 → 603b1466
  → selector 603b0252 → COLOR builder 603b0068
```

The configuration call at `60334ded` precedes the driver's slot installer
call at `60334e1b`. The path includes predicates: the type-0 builder's local
predicate must be nonzero; `603aaced` checks request type and request+28's
high byte (1 or 2); the selector's native COLOR arm still requires its own
mode/override conditions. This is not every capture or every stage. It does
establish an actual synchronous CPU coefficient-building path **before** slot
installation, rather than treating event 10 as the time H/L must be read.

Constructor return at `603e6d3e` is stored directly to descriptor+36 at
`603e6d45`; the embedded wrapper forms job+11364, and the operation submission
forwards operation+8's request pointer. These are pointer transfers, not
whole-object copies at these sites. External requests and other constructors
remain separate admission cases.

Stages can overwrite initialized headers: `6035d35c` calls the request wrapper,
then `6035d368` writes request+12=`0xf005`. Thus an initialization value of
zero is **not** a universal submission invariant and cannot select one hardware
slot for all `0x100d` processing. The
[CPU-chain report](../../research/ep7/cpu-builder-provenance-1100.json) validates
14 windows / 52 witnesses and the type-0 dispatch word.

```sh
python tools/ep7_job_pool.py --stock /local/stock.BIN --objdump /trusted/mn10300-objdump
python tools/ep7_cpu_builder_provenance.py --stock /local/stock.BIN --objdump /trusted/mn10300-objdump
```

Required before any trailer reader can be considered:

1. Independently establish expanded allocation provenance and extent **before
   reading any trailer bytes**. Callback/operation/backlink shape alone is
   insufficient; an out-of-bounds magic read cannot establish its own safety.
2. Initialize every new byte, bind the immutable snapshot to the correct
   image/profile capture, and explicitly transfer it on admitted clone paths.
   Reading later UI state is not a valid capture-time snapshot.
3. Qualify supported constructor → reader → release paths, including failure,
   retry, preview/RAW and cancellation. Unknown/old jobs must bypass H/L
   without reading their nonexistent extension.
4. Preserve CPU ABI, native S/output bounds and neutral H=L=0 equivalence.
   Prove no trailer pointer escapes; hardware may then retain only the native
   output, not the H/L snapshot.

Address/capture-ID reuse requires ABA protection for an external lookup table.
A fully proved direct job-owned value lifetime does not inherently need an
extra generation field. Neither host shape tests nor a fabricated provenance
flag establish actual firmware allocation provenance.

### Capture-time coherence is a separate obligation

Population routine `602a7ea0` resolves the capture pointer, then `60300055`
copies 6833 template words; this helper is not a lock. The S region
`602a85c4`–`602a86b7` calls getter `6005e971` **12 separate times**, with
`a0=0` and `f6ea` indices 0–11, storing halfwords at capture+24058.
The getter repeats registry lookup; this is not an established atomic 24-byte
snapshot. No spanning lock was identified in the reviewed contiguous windows.
This does **not** establish global absence of serialization or an actual race.

Immediately before S, property 111 (`9481`) supplies raw mode at capture+24053;
raw value 6 is replaced from property 211 (`9d11`). Raw mode 11 chooses
property 908 (`f6b1`) and raw mode 12 chooses property 973 (`f731`) for the
selector at capture+24083. These are separate observations. Raw mode 11 must
not be confused with public COLOR mode 54, nor the selector blindly indexed
without its native mode/range conversion. The subsequent
[raw-profile trace](CAPTURE_ADMISSION.md#captured-raw-selector-is-1-based-on-the-accepted-color-rows)
now identifies accepted selectors 1–4 and the full composite getter boundary.

One exact immediate caller `602a446d` gates population on `6223e33c==0`, a
nonnull `602a3116` result, and zero from `602a3204`. Its earlier helper's
possible synchronization pair has returned before population at `602a44a3`;
no spanning lock is established by that pair. External scheduler/writer
serialization and other callers remain unqualified.

Post-S address `602a86b7` is a **design admission candidate**, not a usable
hook: merely adding H/L reads there does not prove consistent S/profile/H/L
publication or extra storage. A minimal extension can preserve the native S
read semantics while sampling
an internally coherent H/L vector for the **already captured raw profile**,
then freezing it for that image and supported clones. It must define that
sampling point and handle or exclude unsupported recall/profile transitions.
This does not guarantee S and H/L represent the same edit instant; stronger
cross-axis atomicity is an optional product contract, not a universal safety
prerequisite. No actual stock race is established by this inspection. The
[snapshot report](../../research/ep7/s-capture-snapshot-1100.json) checks
9 windows / 139 instruction witnesses and the mode/profile maps:

```sh
python tools/ep7_s_capture_snapshot.py --stock /local/stock.BIN --objdump /trusted/mn10300-objdump
```

### Host-only allocation contract

[`ep7_inline_job_design.py`](../../tools/ep7_inline_job_design.py) models an
opaque allocation ticket as an **explicit test assumption** of independent
constructor evidence. It does not discover provenance in stock firmware.
Old-sized, unknown, failed, uninitialized, released or mismatched allocations
are rejected before any simulated trailer read. Tests cover all 16 operation
slots, explicit snapshot cloning, UI changes between images, address reuse,
overlapping allocations, and scalar-only output surviving job release.
The identity coefficient transform is not camera mathematics. This fixture is
single-threaded; it proves neither allocator compatibility nor native concurrency.

## Remaining boundaries

Storage ownership across all S-part1 users, reset/recall/backup/migration and
physical NVM save/checksum is not yet closed. Inline-job allocation provenance,
immutable capture binding and the exact admitted CPU hook are also open.
Hardware testing will eventually be needed for pixel semantics, timing and
recovery; it is **not** a prerequisite for the remaining bounded static work.

The [capture-admission continuation](CAPTURE_ADMISSION.md) narrows the dynamic
stage family and embedded submission sites, while documenting request rebuilds
and binder overrides that prevent stage identity alone from granting access.
