# Two exact state-service seams — compile-only candidate

`bridge.s` is a native wrapper for **both** CALL instructions at 60289c5e and
60289d02, each originally calling6028a882 with [d2,d3,a2,a3],32. It is not a
replacement for helper entry60289c5e, not a global detour of6028a882, and does
not provide installation bytes or a linked target. It executes original service
exactly once before observing current/pending state. Original service can dispose
nodes or request another state, so observing before it would be incorrect.

## ABI and stack

Let incoming wrapper SP=W; caller RA is W+32 and saved d2,d3,a2,a3 occupy
W+28,W+24,W+20,W+16. The nested original CALL writes its RA atW and its saved
registers belowW, then usesW-32. Original RET32 restoresW and original callee
register values. Wrapper next reserves32, B=W-32, for observer invocation:
B+0..8 is GCC return/argument spill area; postservice d0,d1,a0,a1,MDR are stored
atB+12/16/20/24/28. None overlaps incoming saved registers. GCC callee preserves
d2/d3/a2/a3. Restore volatile values and MDR, add32 toW, then native RET32 restores
outer registers/PC. Stack model checks this arithmetic, not execution/emulation.
Actual assembled source is17instructions/47bytes with two checked unresolved
PCREL32 relocations. Observer itself has a generated20byte static frame; added
callback frames are unknown. Neither these figures nor nested frame32 prove native
task stack headroom. No link-register shortcut/RETF is used.

Native continuation recreates branch flags with CMP at60289c6d or60289d0d before
using them; no full PSW restoration is asserted or implemented. Actual GCC observer
uses no loop/control-register instruction (-mno-setlb/-mno-liw). Original service
already invokes callbacks; the unresolved sidecar must be qualified for the same
base ABI and supported controller continuation, not arbitrary extended state.
The service body initializes its localSP+4/8/12; no explicit caller-stackargument
was found. This is not proof arbitrary registered callbacks never introspect stacks.

## Observer and hard unresolved gate

Target-only C byte-loads little-endian16bit current62234fc0 and pending62234fc2.
Sentinel255 produces no callback. Every other pending value invokes normalized
`ep7_sidecar_transition_unresolved(old,pending)`, INCLUDING33->33. It neither
writes native state nor implements a registry. A future callback must synchronously
revoke old33 admissions on every actual commit and establish a fresh generation
when entering33. It MUST guarantee fail-closed before returning: this void interface
cannot report failure or veto native commit. Calling a fallible invalidator and
ignoring its result would be unsafe. Controller-local, infallible revoke/generation
logic is a possible design, not implemented/proven here. It must not alter native
state words/reenter controller/asynchronously retain this observation.

Both byte reads and the following native reload/commit require explicit controller
exclusion/stability. Volatile is NOT atomicity or inter-core synchronization.
This seam does not cover nodes disposed within unchanged33 before commit; those
need separate lifetime coverage. No claim of successful installation or complete
sidecar safety follows from this compiled callback scaffold.

## Reproduce

`python prototypes/ep7_volatile_hl/capture_state_guard/check.py > prototypes/ep7_volatile_hl/capture_state_guard/report.json`

`python -m unittest discover -s prototypes/ep7_volatile_hl/capture_state_guard -p test_check.py`

Checker guards local compiler/assembler/objdump hashes, compiles self-authored C,
assembles wrapper, pins instructions/frame tuples/relocations/text size and exact
undefined sets, observer frame20 and absence of loop-state instructions. Tests
assemble their own temporary fixture, so no prior local dump is required.
Only optional test-temporary self-authored disassembly is emitted; no vendor payload.
Native evidence remains frozen separately in [docs/ep7/NODE_STATE_GUARD.md](../../../docs/ep7/NODE_STATE_GUARD.md)
(36witnesses,21directstate references), independently reviewed; this checker is
not a substitute for that exactstock provenance check. No native execution/link.
