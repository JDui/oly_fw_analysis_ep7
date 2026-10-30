# E-P7 1.1: GUI bridge and request ownership

This continues the [first bounded trace](INPUT_AND_PROCESSING_TRACE.md) using
exact stock SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`.
All addresses are decoded-main CPU addresses. Static inspection only: no camera
access, firmware execution, image generation or flashable patch. User-reported
installed version is 1.1; that does not constitute a device readback.

## Application events reach GUI through state-dependent forwarding

The missing namespaces now have an actual code/data bridge:

1. Mapper `0x60cf91d8` uses table `0x60f6dca8`: app OK `0x43` → OLY
   `0x0100001a`, Delete `0x53` → `0x01000026`, INFO `0x57` → `0x0100002a`.
2. State-table consumer `0x60cf304c` selects a 16-byte event row, placing its
   second word (GUI enum) into context+32. A callback in the fourth word may
   change the outcome. `0x60cf310b` transfers this packet to FSM object+12.
3. Main loop `0x60cc82b2..0x60cc82ee` obtains the packet using `0x60cf2f20`,
   then calls adapter `0x60cfcb2a`. The adapter's interface at +32 is bound to
   GuiCaller by calls at `0x60cc7348` and `0x60cc7352` (setter `0x60cfccc8`).
4. `GuiCallerImp::sendEvent`, `0x60dd4ba9`, indexes table `0x6113e938`:
   enum `0x14` → local `0x900c`, enum `0x27` → `0x9016`, enum `0x25` →
   **`0x9014` (INFO, not `0x9012`)**. Ordinary delivery goes through
   `0x60d0ffb4` / `0x60d0ffe0`.

A concrete no-callback forwarding table belongs to state **`0x2006`** (descriptor
`0x60f522f4`, table `0x60f50dcc`, 70 rows). State **`0x5701`** has another table
with forwarding callbacks (descriptor `0x60f5e648`). Other states suppress keys
or override results. **Neither state has yet been proven to be the selected
application state while COLOR editing is active.** This is a verified conditional
bridge, not an unconditional GPIO-to-COLOR claim.

## Mode selection, callbacks and native INFO/hold behavior

Selector path `0x60e266a9..0x60e26789` reads property 111. On selector value 1
it searches the eight mode/key rows at `0x61189278`; its COLOR subset maps
54/55/56/64 to `0x13b3/0x13b4/0x13b5/0x140c`. It passes the selected key to
factory `0x60dd518e` with kind 7 at `0x60e2677d`. The meaning of the enclosing
selector object and its application-state identity remains to be joined.

Initializer `0x60e20760` finds the key in 56-byte handler records, installs
nonzero callbacks at parent+48 onward, and calls its init function. The four
COLOR rows bind default `0x60e22191`, local `0x900c` callback `0x60e223ae`, and
local `0x9014` callback **`0x60e22579`**. Vtable `0x61187534` binds parent local
dispatcher `0x60dd5250` and callback wrapper `0x60e20cdc`.

The `0x9014` callback guards modes 54/55/56/64, reads cursor properties
1091/1096/1097/1686 and companion properties 1098/1099/1100/1687. One branch
writes **255 (ALL)** to the corresponding cursor (`0x60e22731..0x60e22733`);
other branches restore a remembered cursor or set 1. Global flags and additional
guards affect the path. This is concrete support for **preserving native INFO
single/all selection**, rather than taking INFO for H/S/L axis switching.

Local `0x900c` is both a GUI event and an internal child commit message; the
namespaces must remain distinct. The parent dispatcher can arm timer 537 with
pending event `0x903e` on the appropriate guard. Timer event `0xf802` dispatches
that pending event back through virtual slot 0. COLOR default handler
`0x60e22191` handles `0x903e` by visiting all children and sending a child
`0x900c` after a handled response. This exposes a **hold/reset propagation path**;
it is not proof of the exact physical hold duration or every child reset effect.
The ordinary `0x900c` callback does not install H/L persistence or transaction
rollback. Do not describe OK as the only time stock edits become saved.

The existing Delete-based axis proposal remains conditional: local `0x9016`
has a real parent dispatch arm, but an end-to-end COLOR-active state join and
noninterference with its guards/repeat path still need qualification.

## Current saturation data is transported, not read at ISP-write time

The inspected path joins these independently identifiable layouts:

```text
current typed record 0xf6ea, indices 0..11, getter 0x6005e971
  → capture block +24058: 12 halfwords (0x602a85c4 onward)
  → converter 0x603e62d1 / 0x603e8af1, descriptor+28 source
  → job parameter block +5538: 12 bytes (mode 11)
  → job +36 parameter base, absolute job +5574
  → request producer 0x60354ce4
  → request +1816: 12 bytes
  → stock COLOR builder already traced in the first report
```

A compact representation converter `0x60324071` separately copies 12 bytes
from source+2119 into parameter+5538. Job constructor `0x603537eb` requests
15488 bytes; the wrapper `0x60355409` places its 1884-byte request at job+11364.
This disproves the assumption that adding only an on-screen H/L value would
necessarily carry that value into the image processing request. New H/L state
would require a demonstrated snapshot/transport contract for every supported
processing route; these offsets are occupied stock structures, not free space.

## Generic table override is a borrowed resource

The producer copies job+13252 to request+1524. The stock selector may then use
that owner/table path instead of the fixed COLOR table. It is **not spare H/L
extension storage**:

- Job initialization sets the pointer to null.
- Acquisition wrapper `0x6035109b` calls `0x60351156`: increments a halfword
  reader count at resource+15436 and returns the pointer stored at resource+15416.
- A processing scope at `0x6036884d..0x603688ed` assigns the borrowed pointer,
  invokes processing, releases via `0x603510a5` / `0x60351167`, then clears it.
- Selection `0x603510af` examines three candidate slots (base +2408, stride
  operand 4184), excluding pointers at resource+15416/+15420/+15424.
- Publication `0x60351103` waits for zero readers before changing the active
  pointer. These routines alone do not establish atomic cross-core correctness.

A local extension must respect existing ownership and in-flight readers; neither
mutating a shared active table nor fabricating request+1524 is justified by this
research. Full async completion, buffer reuse and all processing entry paths
remain unqualified. H/L pixel interpretation remains uncalibrated.

## Capture storage has a pool lifetime, not an unbounded tail

Capture population entry `0x602a7ea0` obtains its block via `0x6029b9d1`.
That getter checks IDs 1..25, indexes registry `0x6223d178` (stride operand 24),
requires flag 4, and returns entry+12. Allocation-like entry `0x6029bdec` obtains
a handle with selector **0x1500**, stores it at entry+16, resolves entry+12 via
`0x603dba87`, and sets flag 4. Selector 0x1500 resolves ROM descriptor
`0x6053a300` to RAM pool object `0xa269d980`: **5376 is a type selector, not an
allocation byte count**. Release `0x6029be33` releases the handle and clears flag
4, but does not clear the stale entry+12 pointer in the inspected window.

Consequently capture+24058 has a real stock snapshot lifecycle. Unknown trailing
bytes cannot be called free space. Further static tracing found the initializer
at `0x603daf36..0x603daf58`: it passes count **25**, backing **`0xaf6037c0`**,
stride operand **41984 (`0xa400`)**, and selector **`0x1500`** to `0x603dda0e`.
Base constructor `0x603dd1d8` stores backing at object+8, stride at +12, count at
+20/+24, and selector at +22. Vtable `0x6053a868` resolves handles via
`0x603ddbdb`, using low-byte index minus one and those fields. GNU's multiply
opcode decoding remains qualified; no independent ISA arithmetic proof is added.
This establishes static pool configuration, not live pool state or usable extra
space. All retain/completion edges for descriptor+28 remain open.

## Reproduction

[GUI bridge report](../../research/ep7/gui-bridge-1100.json) and
[request ownership report](../../research/ep7/request-ownership-1100.json) contain
exact table checks, instruction operand witness counts and window fingerprints.
The [editor report](../../research/ep7/editor-contracts-1100.json) also validates
the four complete callback rows, mode/key subset and local dispatch table.
Code-window hashes identify the reviewed bytes; they do not automatically prove
all prose control-flow interpretation or a device result.

```sh
python3 tools/ep7_gui_bridge.py --stock /local/stock.BIN --objdump /trusted/mn103-objdump
python3 tools/ep7_request_ownership.py --stock /local/stock.BIN --objdump /trusted/mn103-objdump
python3 -m unittest discover -s tests -p 'test_ep7*.py'
```

Both instruction tools require a separately trusted MN10300 objdump (reviewed
GNU Binutils 2.45 was used). Wrong stock fails before invoking it; decoded bytes
exist only in a temporary directory, deleted after the run. Only JSON metadata
is emitted. Do not supply an executable from an untrusted firmware archive.

## Evidence boundary and next experiments

The table and instruction reports are reproducible from the exact local stock;
they publish addresses, operand checks and hashes, not firmware or bulk listings.
The GUI bridge narrows the next question to **which app FSM state is selected
while the COLOR factory-kind-7 object is active**, rather than searching arbitrary
key tables. Ownership work narrows the other question to **where a per-image H/L
snapshot can safely live and be transported without sharing mutable state**.

Useful static work does not require a button video. If these specific joins
cannot be established in the stock graph, the minimum future device evidence is
selected app-state ID / outgoing enum for OK, INFO and Delete in COLOR, and
observed capture/preview buffer lifetimes. No instrumentation or firmware write
is authorized by this document. A normal stock-camera interaction video could
check visible ergonomics only, not prove those internal joins or H/L correctness.


## Further static join: COLOR GUI machine admission

The object-creation chain can now be continued without a device log:

```text
GUI machine table 0x611317c4, slot 3 → descriptor 0x611a3bc8
  machine 4 / state 29 (one-based; packed 0x041d)
  init slot 28 at 0x611a3b50 → 0x60e5dae9
  controller group 8, key 0x1cf → factory 0x60e4cea8
  descriptor 0x6119cb3c → whole-actuator type 0x34
  factory row 0x61140354 → creator 0x60e260c7
  selector property 193 → COLOR child factory 7
```

The initialized controller is stored at global `0x61fc436c`; exit callback
`0x60e5db01` disposes and clears it. This GUI machine/state is **not** application
FSM state `0x5701`; the app→GUI context selection join is still separate.
The machine descriptor has 29 states, 112 events and 138 handlers. Engine
`0x60d11448` selects a byte-matrix entry using event index and one-based state.
As elsewhere, the multiply opcode is not independently decoded beyond the
reviewed operand pattern and table dimensions.

For state 29, OK `0x900c`, INFO `0x9014` and `0x9015` select handler 137,
`0x60e5da87`, which reads that controller and calls `0x60e4d032`. Its dispatcher
calls actuator virtual slot 0. **The complete 112-entry event table at
`0x611a2888` does not contain `0x9016`.** Lookup `0x60d1158b` returns `0xffff`
for a missing event; the engine returns 3 before calling a handler when the index
is outside the event count. Thus this identified table route does not directly
admit Delete's local event to the COLOR controller.

This is a concrete compatibility risk, **not proof that Delete can never arrive**.
Preprocessing, event recoding, alias/controller queues or direct-object delivery
have not been exhaustively excluded. A bottom-level `0x9016` handler is therefore
insufficient justification for copying PEN-F's axis hook. The controls proposal
now treats Delete as conditional on end-to-end routing qualification, possibly
requiring an E-P7-specific upper-level admission change.

The same table also lacks `0x903e`, but this does **not** invalidate the stock
hold path: parent timer event `0xf802` directly dispatches pending `0x903e` through
its virtual slot 0, without necessarily returning through this machine lookup.
Do not infer “no reset” from that table absence.

The common app callback `0x60ceac44` was also narrowed: its first callee only
special-cases packet event `0x01070002`, not the reviewed OK/Delete/INFO events;
the following call writes a separate global. This callback is not itself an enum
override for those three reviewed keys. Other state callbacks remain unqualified.

[GUI-machine report](../../research/ep7/gui-machine-1100.json) checks descriptor,
factory/init/exit links, all 112 event entries for the relevant absence, handler
selection and reviewed instruction operands. Reproduce with:

```sh
python3 tools/ep7_gui_machine.py --stock /local/stock.BIN --objdump /trusted/mn103-objdump
```

## Further capture join: allocation size is not clone extent

The reviewed processing-loop predecessor `0x603e5d57` receives a **300-byte**
transport-filled descriptor at stack+16 through `0x603df9f1`. In a selected path
it invokes `0x603edb9a`. That helper reads descriptor+260: if nonzero, descriptor+116
is consumed as a capture registry ID by `0x6029b9d1`; otherwise source is the
existing descriptor+28. The producers of +116/+260 remain unknown.

The helper requests **41984 bytes**, stores the returned clone pointer in global
`0x622933dc` and descriptor+28, but copies only **27332 bytes (`0x6ac4`)** from
the selected source. The observed S halfwords at [24058,24082) are within that
copy. A hypothetical extension in the allocation's trailing bytes would not
therefore be transported automatically. The allocator helper's +24776 check is
based on its **incoming descriptor+28**, which need not be the separately selected
registry source; those bases must not be conflated.

Helper `0x603edbd8` provides a local paired release and clears the global; the
loop calls it after a nonzero result from `0x603e16f1`. This is **not proof of
completion of all asynchronous consumers**. The transport producer, allocation
failure semantics and processing/completion contract still need evidence.

[Capture-clone report](../../research/ep7/capture-clone-1100.json) checks the
conditional source binding, allocation request, actual copy length, pointer write
and local release operands. Reproduce with:

```sh
python3 tools/ep7_capture_clone.py --stock /local/stock.BIN --objdump /trusted/mn103-objdump
```

A future host-only ownership model should distinguish registry-borrow and
local-clone provenance, require generation/lease identity under address reuse,
explicitly transfer an H/L snapshot across clones, and reject unknown routes or
completion-after-release. Passing such synthetic tests would validate a proposed
design only—not identify free firmware storage, establish real queue lifetime,
or qualify ISP behavior. No hook, extension address or firmware artifact is
provided by these additional findings.


## Top-level task check: no observed Delete rewrite on this route

A focused caller trace found the actual GUI task, avoiding enumeration of every
machine getter. Registration at `0x60cfd41c..0x60cfd431` initializes fixed machine
object `0x6246684c` and publishes its pointer at `0x61fb2564` / `0x61fc1848`.
The task dequeues a packet at `0x60cfd4e7` via `0x60d10133`, calls preprocessor
`0x60e9fa88` at `0x60cfd53a`, and either consumes it on return 1 or rereads the
packet and calls the engine at `0x60cfd558`. That call targets **`0x60d1144d`**,
an entry inside the previously inspected engine window starting `0x60d11448`;
scanning only calls to the earlier address misses this concrete caller.

For local `0x9016`, the preprocessor uses key `0x12` (`event - 0x9004`) in its
128-slot table at `0x611ec960`. There is no matching key. The actual linear probe
starts at slot 18, traverses 21 slots, and reaches the empty/default slot 38 at
`0x611eca90`. Its generic tracking table has 41 events, also without `0x9016`.
The inspected default and state-gating branches may consume this event, but no
rewrite into another event or direct actuator dispatch was found for it along
this reviewed route. If passed through, the task reloads unchanged `0x9016` and
the identified COLOR machine table rejects it before the controller handler.

This strengthens the **normal task-route admission gap**, not a whole-program
or physical-button absence claim. Diagnostic callees were not all recursively
audited; other event producers, alias/direct paths and the app-state selection
are not globally excluded. The local `0xf802` → pending `0x903e` timer path is
unaffected. The GUI-machine probe now includes this task chain, the bounded hash
probe and generic tracking-table check, plus fingerprints of the inspected gates.

This completes the focused top-level-consumer question. Further input work should
start from a specifically justified alternate producer or observed app-state
selection, rather than blindly enumerating every machine getter. It remains
unsafe to install only PEN-F's leaf Delete hook or to claim E-P7 HSL is working.
