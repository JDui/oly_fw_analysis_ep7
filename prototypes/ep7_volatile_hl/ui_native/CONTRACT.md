# Native parent event → GCC routing candidate (uninstalled)

## Exact selected seam and observed status meanings

This candidate replaces ONLY the callable parent virtual0 entry normally implementing `60dd5250`. Its reviewed caller is container `60e4d0ff`: native `CALLS(a1)`, `a0=parent`, `d0=local event`, `d1=packet parameter`. It is not a transparent midfunction hook or GCC function pointer. `bridge.s` saves/restores d2,d3,a2,a3, and returns its native result in d0. It never enters the original implementation at its inner body5255.

The container (`60e4d0ee..d141`) makes these distinctions when its viewer pointer exists:

| Parent virtual0 result | Observed next operation |
|---|---|
| 0 | No viewer callback/result translation |
| 1 | For non-AF-special event, call viewer virtual0 atd123; container result remains0 |
| 2 | Container result1 |
| 3 | Container result2 |
| 4 | Container result3 |

Handler137 (`60e5da87`) checks **container** result1; only then calls60ea26fb/60ea114b and returns packed0x0104. Therefore blindly returning portable DELEGATE=2 could take that branch. `4` is not a universal "handled" value: parent wheel paths545d/547f also treat4 specially by calling5857, which invokes timer535 cancellation helper and clears61fc1bbc.

Native9032 value handler60e21cae returns its final repeated child result (zero count initializes0). Native9031 sector handler60e21efb returns1 even for zero repetitions. INFO60e22579 has result1 and result3 branches; wrapper60e20cdc additionally schedules500 when parent+4==1 and result1. These are contextual native effects, not portable enum meanings.

The new **parent-seam-specific policy** is deliberately explicit: CHANGED→native1 to request the already-bound H/L viewer callback; UNCHANGED or REJECTED/unknown→0 without stock S fallthrough. DELEGATE→internal action256, consumed by assembly to call the full original parent and return its exact native result. No action256 or normalized2 escapes to native caller. Stock category0..3, UP/DOWN, OK, Delete and unknown events are delegated unchanged. The H/L-owned branch intentionally does not call the original INFO/child setter or its timers; it is not claiming to preserve a native long-hold gesture inside new H/L categories.

## Implemented held input transaction

`bridge.c` calls `ep7i_route`, which qualifies actual MVC/session/display receipt,
then holds MVC and native owner membership through the real existing
`ep7p_ui_raw_dispatch`. Five original setter calls copy their full local delta
inside a complete preprocess/engine scope. Parent caller PC/container and current
machine4/state29/handler137 must match. Packet d1 never substitutes for delta.
Known-stock/unowned parents delegate; inconsistent formerly-owned graphs stop
before delegation. See [current binding](../../../docs/ep7/UI_INPUT_BINDING.md).

No borrowed mutable UI/session pointer escapes an admission callback. The engine
scope remains active through subsequent original viewer consumption; each event
can attempt H/L editing only once. Receipt readiness requires the joined native
text renderer, but is not LCD acceptance or installation proof. H/L masks remain
disabled until COLOR gating and normalization are implemented.

## Native/GCC call frame

EntrySP=S with native caller return at[S]. MOVM saves four callee registers belowS
and decrements16; ADD-32 givesSP=S-48. Five input words occupySP+12..31, including
caller PC fromSP+48 and container fromA3. Outgoing0..11 is reserved; saved native
registers occupy32..47. GCC receives a pointer inD0 via CALL[],0. Action256 restores
originalD0/D1/A0 and invokes the full original parent via CALLS(A1), whose prologue
owns80. Final RET[f0],48 uses the original stack return. No volatile/MDR/flags
preservation is promised at this parent entry; stock also clobbers them.

The current target checker validates20 instructions/52 bytes and the same three
relocation targets. The new preprocess/engine/sample/drop bridges have84 checked
instructions and preserve their own distinct caller-frame contracts. No target
link/execution or complete firmware build is performed. Frame arithmetic is not
an instruction emulator; total native stack and interrupt margins remain G6.

The earlier UI-status audit and `ui-native-bridge.json` are historical evidence.
Current results are `ui-input-binding-{current,host,target}.json`; current checks
use explicit installed tools and input structure/instruction qualification,
without running legacy SHA guards.

### Parent-entry interception caveat

Owned H/L now reproduces parent+24/+28 and conditional+36 bookkeeping and checks
the actual zero-only61fc1bac gate for both wheels andINFO. AcceptedINFO reuses the
native queue drop helper. It intentionally does not create INFO hold timers or
reuse stockS setters. Stock categories retain their complete original dispatcher.
COLOR gating/normalization, associated timer-state handling, native exclusion and
cold installation remain necessary before enabling H/L.


## Integrated reproduction and ABI checker review

```
python3 prototypes/ep7_volatile_hl/ui_native/check_input.py
python3 tools/ep7_sidecar_target_check.py --tool-prefix /work/install/bin/mn10300-elf- --ui-input-only
```

The current host test reuses19 viewer/MVC/content groups and adds8 input groups;
strict/ASan/UBSan pass with real core/runtime/renderer C and modeled native
boundaries. `check.py` and its unit tests remain the legacy tool-specific path;
only its pure assembly validator is reused by the current target check. Target
C uses `-mno-setlb -mno-liw`. MOVM ordering is:
d2 atS-4, d3 atS-8, a2 atS-12, a3 atS-16. CALLS stores a new return at currentSP
and setsMDR without adjustingSP; the original parent owns its nested80-byte
frame. This was checked against the previously pinned GNU MN10300 semantics
source (CALLS block3492 onward), not by running a simulator.
