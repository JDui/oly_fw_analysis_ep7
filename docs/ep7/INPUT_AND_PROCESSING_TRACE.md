# Bounded E-P7 input/editor and H/L processing trace

2026-10-30; exact E-P7 1.1/1100 stock and trusted GNU MN103 Binutils 2.45.
This is **static analysis, not firmware execution, device input testing or a
working HSL port**. It deliberately stops at missing joins instead of treating
matching numbers or similar PEN-F functions as proof.

> Continuation: [GUI bridge and request ownership](GUI_AND_REQUEST_OWNERSHIP.md)
> resolves the conditional app→GUI bridge and request producer/lifetime paths.
> The open joins below describe the first-pass boundary, not a claim that these
> questions cannot be investigated statically.

## 1. Logical key input is not a COLOR GUI event

The E-P7 table at `0x60adc1f8` is consumed by mapper `0x60825002`:
the loop at `0x60825020..0x60825044` compares the incoming d3 with each row's
first word and loads the second word into d2. Reviewed OK/Delete/INFO values
do not match the later special-case branches; d2 returns at `0x608251dc`.
Independent event-name rows at `0x60a6eef0` onward corroborate these labels.

| Logical input | Application ID | Meaning | Translation row |
| --- | --- | --- | --- |
| `0x02000004` / `0x02010004` | `0x43` / `0x44` | OK press/release | `0x60adc290` / `0x60adc298` |
| `0x02000084` / `0x02010084` | `0x53` / `0x54` | Delete press/release | `0x60adc2c0` / `0x60adc2c8` |
| `0x02001205` / `0x02011205` | `0x57` / `0x58` | INFO press/release | `0x60adc2d0` / `0x60adc2d8` |

This establishes an actual **logical-input-to-application translation**, not
the physical switch/GPIO source or an end-to-end delivered button event. In
particular, it does **not** prove E-P7 Delete becomes GUI-local `0x9016`.
Application IDs, editor-local events and child commit messages occupy different
namespaces. Coincidentally adjacent values in unrelated tables are not a join.
The application-to-COLOR dispatcher and physical acquisition route remain open.

## 2. Actual COLOR editor construction differs from PEN-F

Constructor path `0x60e20a54 → 0x60e20aca` reads the editor key from parent+100,
searches 47 eight-byte descriptors at `0x61186ba4`, sets child count at parent+120,
then calls child factory `0x60dd518e` at `0x60e20b0f`. Created child pointers are
stored starting at parent+124. This is a concrete static constructor/table join.

| Profile | E-P7 editor key | Descriptor | Child 0 cursor | Children 1–12 |
| --- | --- | --- | --- | --- |
| COLOR1 | `0x13b3` | `0x61186c7c` | 1091 | 927–938 |
| COLOR2 | `0x13b4` | `0x61186c84` | 1096 | 939–950 |
| COLOR3 | `0x13b5` | `0x61186c8c` | 1097 | 951–962 |
| COLOR4 | `0x140c` | `0x61186c94` | 1686 | 1655–1666 |

These are not PEN-F keys `0x13b2/0x13b3/0x13b4`. Checking only a consecutive
three-key range would misidentify or omit E-P7 profiles. CRT key `0x13a9` uses
the same general family but **two** children, properties 617/618. A hook must
qualify the full COLOR descriptor/child contract rather than shared code alone.

Handler records at `0x61185bdc`, `0x61185c14`, `0x61185c4c`, `0x61185c84`
bind those four keys to the common increment/decrement candidates
`0x60e20e0a` / `0x60e2107a`. Their code reads property 111, checks public modes
54/55/56/64 and chooses the corresponding cursor property. The increment path
sends local child step `0x9004`, then child commit `0x900c`; the decrement path
uses `0x9006`, then `0x900c`. The ALL path iterates twelve value children.
This confirms why a child commit must not be equated with a physical OK press.

The handler's origin in a physical dial/button event and the exact meaning of
every guard are not established. No Delete handler is installed by this work.
INFO/OK short/hold behavior still requires mapping their E-P7 GUI dispatch and
timer context. The control proposal remains a proposal, not compatibility proof.

## 3. Stock COLOR has a dynamic S path, not a demonstrated H/L editor API

The inspected conditional processing chain is:

```text
context processing 0x603b1466
  predicate 0x603aade3 at call 0x603b14b4 (semantic meaning unknown)
  selected branch → call 0x603b14f3 → selector 0x603b0252
  no override owner / supported mode path → compare mode 11 at 0x603b02c1
  call 0x603b02d9 → builder 0x603b0068
```

The COLOR arm loads output=context+12, sets a1 to **request+1816**, and passes
the fixed ROM table `0x6051de2c`. The builder reads twelve signed S bytes in
index order `2*inner+outer` (two groups of six). Source records are 28 bytes;
packed output records are 24 bytes at output+688.

At instructions `0x603b015b..0x603b017a`, source-record halfword +12 is packed
into output-record halfword **+18**, and source halfword +16 into output halfword
**+22**. Their H/L interpretation comes from the upstream shared-table research,
not a new E-P7 pixel calibration. All twelve stock COLOR records have zero in
both fields. Thus this inspected arm has per-request S but fixed-table H/L;
there is no demonstrated hidden per-request H/L array simply waiting for keys.

An earlier branch reads a nonzero owner pointer at **request+1524** and can
obtain a table through owner+16, calling generic packer `0x603afb94`. Its type,
allocation, lifecycle and eligibility are unknown. It is **not a safe public HSL
setter** and is not permission to synthesize an arbitrary pointer or mutate a
shared table during capture.

Builder control is at output+976. The writer `0x6034667e` is called by
`0x60345f8f` and `0x60345fb1` with two different MMIO destinations
`0x9f001000` and `0x9f805000`. Its enabled path transfers **292 bytes**:
twelve 24-byte records plus the four-byte control, from source+688 through
source+976 into destination+752 through destination+1040. This proves the CPU
copy intent, not how the ISP interprets those fields or whether a live upload
succeeds. GNU renders some multiply opcodes as `udf00`; no new exact S arithmetic
or native multiply semantics are claimed here.

## Reproduction and evidence scope

[Table-check report](../../research/ep7/editor-contracts-1100.json) includes the
verified editor children, logical key translations, and fingerprints of inspected
code windows. The report checks tables; prose control-flow interpretation came
from disassembly of those exact windows. No bulk listing or firmware is published.

```sh
python3 tools/ep7_editor_contracts.py --stock /local/path/OLY_E_142_1100_0000_0000.BIN
python3 -m unittest discover -s tests -p 'test_ep7*.py'
# For each named code window, after separately decoding the exact input locally:
/trusted/path/to/mn10300-elf-objdump -b binary -m mn10300 -D -z \
  --insn-width=16 --adjust-vma=0x60020020 \
  --start-address=0x60e20aca --stop-address=0x60e20b2d /local/main.decoded.bin
```

## Explicit stopping point and next safe experiment

This bounded pass established two incomplete chains: logical-input translation
and COLOR construction/child operations; it did **not** bridge the dispatcher
between them. It also established the stock COLOR coefficient path, not the
producer/owner lifecycle. Further arbitrary address searches would not justify
a camera-safety claim.

Next offline experiment should map **one** E-P7 input through the selected GUI
FSM, including release/hold and non-COLOR passthrough; separately trace producers
of request+1816 and request+1524 through capture/preview/RAW copies and reuse.
Any CPU fixture requires E-P7 ABI/state evidence and reviewed opcode semantics;
PEN-F checkpoints are not interchangeable. Only after those joins can an
image-owned H/L prototype be scoped. No flashable output is needed for that work.

For physical validation the minimum missing user evidence is the camera's
installed firmware version and a short read-only recording of native COLOR1–4
entry, INFO, short/held OK and Delete behavior. Existing diagnostic logs, if the
user already has a safely obtained set, can help; no diagnostic modification,
memory dump, connection or firmware write is requested or authorized here.
