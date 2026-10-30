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

## Implemented glue versus unresolved admission/rendering

`bridge.c` calls the real existing `ep7p_ui_raw_dispatch`, not a replacement arithmetic model. `ep7_ui_native_admit_unresolved` must first qualify exact live parent/session, COLOR category4/5 and a correctly bound H/L viewer, then supply a synchronized full signed delta associated with this event. Packet d1 is never substituted for delta. An unowned/known-stock object delegates; an invalid formerly-owned context rejects without invoking stock. Existing raw adapter rejects stale sessions and oversized counts. No native ownership provider or viewer implementation is supplied here.

All UI state and input must remain serialized through routing and the subsequent native viewer consumption. A provider cannot briefly lock, return borrowed mutable state, and pretend that establishes this contract. The provider must not mutate H/L on a delegation/rejection path. Qualifying H/L without its renderer is forbidden: requesting viewer v0 is not evidence that a stock S viewer can render H/L.

## Native/GCC call frame

EntrySP=S with native caller return at[S]. MOVM saves four callee registers belowS and decrements16; ADD-32 givesSP=S-48. Input words occupySP+12,16,20; GCC outgoing/argument-flush areaSP+0..8 is reserved; saved native registers occupySP+32..47. GCC receives one pointer in d0 and is called with `CALL [],0`. Internal action256 restores original d0/d1/a0 and invokes unresolved original entry with `CALLS(a1)`. Original parent owns its nested prologue/frame. Final `RET [d2,d3,a2,a3],48` uses the original stack return (NOT overwritten MDR). No flags/MDR/a0/a1/d1 preservation promise; stock parent also clobbers those. Caller arguments/entry behavior and return-frame arithmetic are bounded to this seam; stack capacity/interrupt margins remain unqualified.

`check.py` validates trusted local tool hashes, actual17 assembled instructions /46-byte text, exact three relocation targets (router CALL, local final-RET branch, original parent pointer), and four external unresolved symbols across two objects; it compiles C with target GCC13.4 and never links or executes target code. Host boundary tests use stubs for ownership and raw dispatch to test conversion/delegation, not native concurrency/rendering. Strict and ASan/UBSan pass; LSan is disabled because this execution environment uses ptrace and the test performs no allocation. The host arithmetic frame check is not an instruction emulator or silicon validation.

The separate UI-status stock audit independently pins167 exact-stock instruction witnesses in10windows, with8tests. Existing SHA guard rejects other stock builds before disassembler execution. No firmware modified, no native S setter called, no install address emitted, no flash-ready output.

### Parent-entry interception caveat

The owned H/L branch bypasses the original parent's event bookkeeping (`60dd525a/525d` writes parent+24/+28), input blocking checks against61fc1bac (wheel5445/5467 andINFO55bb), and INFO hold-timer machinery. Admission therefore also requires qualified native modal/input-block state; a blocked H/L event must reject0, not mutate or fall into stock S. The new H/L viewer must consume the portable frame rather than assume these bypassed stock event fields were updated. This candidate does not silently recreate those native side effects. Stock categories delegate through the complete original parent and retain them. These requirements are part of the unresolved provider/viewer contract, and are an explicit reason the bridge is not install-ready.


## Integrated reproduction and ABI checker review

```
python prototypes/ep7_volatile_hl/ui_native/check.py
python -m unittest discover -s prototypes/ep7_volatile_hl/ui_native -p 'test_*.py' -v
```

`research/ep7/ui-native-bridge.json` records actual compile/host results. Nine
checker tests pass, including wrong router/native/branch relocation, wrong final
RET label/frame/text extent, and tool-hash rejection. Target C is compiled with
`-mno-setlb -mno-liw`. The stack model follows actual MOVM ordering:
d2 atS-4, d3 atS-8, a2 atS-12, a3 atS-16. CALLS stores a new return at currentSP
and setsMDR without adjustingSP; the original parent owns its nested80-byte
frame. This was checked against the previously pinned GNU MN10300 semantics
source (CALLS block3492 onward), not by running a simulator. No bridge C/ASM
behavior changed in checker hardening.
