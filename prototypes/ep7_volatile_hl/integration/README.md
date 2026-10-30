# Actual portable UI routing integration (host only)

This closes a specific test gap in the existing native UI bridge fixture. The
executable links the **actual** `ui_native/bridge.c`, `ep7p_ui_raw.c`, `ep7p_ui.c`,
`ep7p.c` and decoder dependency. Native admission and the text setter are mocked;
there is no stub `ep7p_ui_raw_dispatch` and no replacement editing arithmetic.

A real portable UI session drives H/L settings. Assertions cover missing renderer
and modal rejection, stock delegation, full signed delta3 despite packet parameter1,
sector wrap, negative edits, zero deltas, oversized/INT_MIN rejection, INFO ALL,
uniform ALL saturation preserving relative values, unchanged-at-bound result0,
axis separation, untouched settings on delegated events, lock failure, invalid
profile, closed and reused-generation stale sessions, and no task identity query.
The native result policy is exercised: changed1, unchanged/rejected0, internal
stock-call action256. Assembly itself is not executed, so this test does not call
the original native parent when action256 is returned.

`renderer_ready` and modal state are fixture booleans in the mocked admission
provider, not a new field or guarantee in the production core. The fixture owns
all UI execution in one host thread; it does not qualify native serialization,
full-delta acquisition, actual object lifetimes, widget creation or rendering.
No S setter or camera API is called. The portable core stores only H/L, so this
suite does not claim to test a live native S presentation.

Run from repository root:

```
python3 prototypes/ep7_volatile_hl/integration/check.py
```

Strict C11 `-Wall -Wextra -Werror -pedantic` and ASan/UBSan both pass. Any compile
or runtime failure fails the runner. LSan is disabled in this ptrace environment;
the lifecycle fixture owns and frees its host allocations. Temporary host executables are
removed. The JSON records hashes of all actual sources and headers. No target
linking/execution, proprietary object, firmware modification or installation.

The report is `research/ep7/vertical-slice-host.json`. This is source-only host integration, not an installation package.

## Real text payload continuation

The extended fixture additionally links frozen `prototypes/ep7_volatile_hl/text_viewer/text.c`.
It takes the actual portable UI frame after routed edits and presents UTF-16
payloads `H 01 +3`, `H ALL MIX` and `L ALL -7` through a copying host setter mock.
It verifies setter failure propagation and invalid frame rejection before setter
invocation. Native admission **and native text setter** remain mocks; only the
router/raw/UI/core/formatter/present C chain is real. No widget creation, font,
visibility, native text allocation or hardware draw behavior is tested. The
mock copies before return, rather than retaining the formatter's stack pointer.

## Actual immutable capture/direct-reader vertical slice

The same executable now links the real `ep7p_lifecycle.c`, captures H+3/L-2 from
profile56 through actual routed events, then changes both current UI values to0.
Sixteen subsequent fresh jobs, one for each embedded operation slot, all use the
earlier immutable snapshot. Host constructor callbacks own malloc and real extent;
converter callbacks populate exact bounded decoder fields. The actual lifecycle
registers the job, calls the actual direct reader through the processing callback,
revokes admission and only then calls cleanup/free. Cleanup asserts all registry
entries are absent. No constructor reads current GUI state.

Each output contains captured comparative H=-3000 and L=-50 at bin0, even though
current UI is0. Every other byte is unchanged, including all native S lanes and
zero-H/L native lanes. Mock process status-123 is preserved independently of the
successful H/L application. All16 operation slots pass strict and ASan/UBSan.
Native constructor/converter/process/cleanup remain host mocks; this establishes
only a software integration slice, not camera allocation provenance, native
snapshot timing, actual request stability or completion/lifetime qualification.
The fixture never retains a reader callback after process returns. A padded host
allocation avoids common sanitizer low32-zero synthetic wire addresses; remaining
32-bit wire overflow fails an assertion rather than weakening the decoder.

## Sidecar-to-job continuation (2026-10-30)

The fixture now uses the real controller sidecar for fresh registration, current
live token resolution, authorize, seal and copyout. It retires the node and commits
33->33 before further UI edits and all16 job operations. The copied snapshot keeps
captured H+3/L-2 and only the expected coefficient bytes change. A second, reused
node is consumed before population: subsequent seal is rejected and a NULL
snapshot reaches the actual lifecycle, which preserves native status/cleanup and
leaves every output byte unchanged.

This closes the self-authored software join between two previously separate
fixtures. Node labels, exclusive ownership, and the by-value handoff are host
fixtures; no native metadata transport, queue lifetime or hook is implemented.

Reproduce without optional source-hash recording:

```sh
python3 prototypes/ep7_volatile_hl/integration/check.py --no-hash
```

[Current strict and ASan/UBSan report](../../../research/ep7/sidecar-vertical-slice-host.json).
LeakSanitizer remains disabled. No target code or firmware was executed.
