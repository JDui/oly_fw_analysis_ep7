# Portable E-P7 H/L prototype — host integration, not installable firmware

This is actual compile-checkable C11 processing code, not a camera patch. It has
no native addresses invoked as functions, firmware input, linker map, hook,
flash builder, NVM writes, or usable camera UI/TLS adapter. Native coefficient
layout constants are research observations; passing these tests is not evidence
of calibrated pixels, recovery, native timing or camera-safe execution.

## End-to-end host demonstrator

The normalized UI bridge is implemented in `ep7p_ui.c`, not merely declared:
category 4 edits H and category 5 edits L for public modes 54/55/56/64. It owns
monotonic per-slot UI session tokens, a selected sector or ALL, bounded repeats,
saturated values and current-axis reset. Stock categories 0–3 are rejected by
this bridge so the future native veneer must delegate them unchanged.

`test_ui_integration.c` opens COLOR4/H, edits H, switches to L/ALL, captures an
immutable profile snapshot, attaches it to a real host allocation, enters a
qualified task scope, edits/closes the UI, then verifies the **earlier snapshot**
changes only the expected H/L halfwords in a bounded output buffer. It also
checks stale UI/scope rejection, cleanup, inactive-mode gating and a new neutral
boot lifetime. This is executed host C code, not a simulated camera success.

UI bridge callbacks require a serialized UI caller. The core's lock protects
settings/capture/jobs, but the bridge does not establish native GUI scheduling.
A mode outside COLOR disables edits without erasing in-flight image snapshots.
Sector navigation leaves ALL; reset clears the entire current axis; repeat
counts outside 1–64 or repeated toggle/reset events are rejected. These are
normalized prototype semantics, **not decoded native physical-button events**.

## Run from the repository root

```sh
python prototypes/ep7_volatile_hl/check_host.py --sanitize
```

This compiles/runs the core and UI integration tests in temporary directories
and deletes their host executables. The [actual report](../../research/ep7/portable-prototype-host.json)
records source hashes, compiler identity and results. Standard Python test
discovery also runs the strict host integration when a C compiler is available.

For individual compilation, run the following **inside this directory**:

```sh
cc -std=c11 -Wall -Wextra -Werror -pedantic ep7p.c test_ep7p.c -o /tmp/ep7p_test
/tmp/ep7p_test
cc -std=c11 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined \
  -fno-omit-frame-pointer -g ep7p.c test_ep7p.c -o /tmp/ep7p_test_san
ASAN_OPTIONS=detect_leaks=0 /tmp/ep7p_test_san
```

Verified with GCC 14.2.0: both executions pass all assertions. LeakSanitizer
itself cannot run under this environment's ptrace; leak detection is disabled
for the ASan/UBSan pass, not claimed tested. The host test frees its allocations.

## Boundary contract

* Call `ep7p_init` once before sharing. It boot-zeros four RAM-only profiles;
  there is no persistence. Missing lock/unlock/current-task callbacks reject init.
  Every subsequent public operation acquires the supplied lock. Callbacks must
  be non-reentrant and synchronize *all* users, including release before free.
  The chosen native lock must also permit the current-task query while held;
  an interrupt/dispatch-disabling lock is not qualified here. The host callback
  checks single-threaded lock pairing only; this is not a
  native locking implementation or a concurrent stress test.
* `ep7p_axis_read` and atomic `ep7p_axis_adjust` use **profile indices 0..3**,
  axis 0 H / 1 L, sector 0..11 or 255 ALL, reset or saturating delta. A UI bridge
  translates public modes 54/55/56/64 to profile indices. Core does not consume
  native key events. Category 0..3 and all native S processing remain delegated.
* Capture accepts already-captured raw mode 11 and selector 1..4, copies one
  coherent H/L vector under the lock, and returns values. Later UI edits cannot
  alter this snapshot. This does NOT make native S/mode reads cross-axis atomic.
  The caller must bind this snapshot to the intended image and clones, not sample
  later UI mode, and define/exclude unsupported recall/profile transitions.
* A trusted allocation adapter must provide a fresh, genuinely writable job
  buffer and its independently known extent (at least 15512). This API does not
  discover allocation size. Registration rejects overlap with the core runtime and live jobs and
  writes exactly the 24 new bytes at 15488; it never reads magic to infer extent.
  The original 15488 bytes are untouched. Snapshot H occupies bytes 0..11 and L
  bytes 12..23. Shape checks do not issue allocation provenance. Clone admission
  requires a new qualified buffer and an explicit snapshot value copy.
* Registry-issued serials never wrap; exhaustion rejects new registration/scope.
  Release revokes that job's active scope and descendants before caller frees
  memory. Same-address registration gets a new serial. Caller must never free,
  move, resize or overwrite an admitted buffer behind the registry's back.
* `current` must return status zero plus a 16-bit task ID and independently
  supplied nonzero, non-reused task-instance epoch. Native `get_tid` supplies
  no such epoch. Trusted lifecycle adapters must revoke a task before reuse and
  supply a fresh epoch. Numerical ID alone never qualifies a reader. Task and
  depth capacities of 8 are prototype choices, not native observations.
* Scope entry and reader validate stage 2/callback 6036884d, current type 0,
  raw mode 11, matching captured selector, owner 0, no mutation callback, and all
  16 embedded operation geometries/backlinks. Observations are supplied by the
  adapter, not read from camera memory here. That adapter must obtain consistent
  observations and preserve the native ABI. Only the matching task's top scope
  reads. `unwind` revokes its frame and descendants; error teardown can use the
  independently trusted `release_task` if current-task query fails. C has no
  automatic exception cleanup: every native exit/unwind adapter remains unbound.
* `apply` copies the trailer while locked, then writes H/L scalar lanes only at
  output+706+24*j and output+710+24*j, using bins
  `[0,2,4,6,8,10,1,3,5,7,9,11]`. Output is a caller-owned writable buffer of at
  least 976 bytes, disjoint from the core runtime and registered jobs. Native S at +708 and unrelated
  bytes remain unchanged. Each zero axis value **skips its lane**, preserving
  even nonzero native coefficients. No H/L pointer is returned or queued.
  Output lifetime through the original native pipeline is a separate obligation.
* Core state/arguments must be valid caller-owned objects, not malicious aliases
  into core storage. Public struct layout permits static allocation, not direct
  mutation. These APIs are not a sandbox against a caller lying about C pointers,
  allocation extent, synchronization, task provenance or object lifetime.

Tests exercise edit→capture→real host allocation→registration→scoped reader→
output→cleanup; immutable UI edit separation; unchanged S/neutral output; all16
operation slots; nested unwind; current-gate changes; task query failure and
instance reuse; old job tokens; malformed shapes; registry/depth overflow;
lock failure; output alias/size rejection; and saturated ALL/reset axis edits.

## Attribution and rights

Comparative hue/luminance LUT values are adapted from fishcu/oly_fw_analysis,
`patches/hsl/pen-f/src/image_parameters/image_parameters.s` lines 101–104 at
upstream commit `539fcf1fa9eda5fdef8ede4deeab94a4691d94c3`. These are experimental
PEN-F comparative mappings, **not E-P7 pixel calibration**. Retain this attribution
and existing repository `RIGHTS-AND-PROVENANCE.md`. That file states there is no
repository-wide license; scoped GNU simulator/font licenses must not be
misapplied to this new code or the LUTs. This prototype adds no global license
and distributes no vendor firmware image or extracted bulk code.

## Native integration is still deliberately unbound

| Required native adapter | Evidence available | Still missing |
| --- | --- | --- |
| UI child/parent/viewer | Exact creation, forwarding, category gates and teardown sites | MN103 register veneers, independent H/L child and draw paths, transactional installation |
| Capture snapshot attachment | Raw profile mapping and post-S sampling candidate | Original-image/clone attachment with explicit sampling/transition semantics |
| Enlarged fresh-job allocation | Constructor and same allocation-class evidence | Actual size/init hook, supported error-path registration and release-before-free |
| Task-scoped lookup | Native `get_tid` candidate | Nonreused task-instance lease, qualified lock/TLS/store and all native unwind paths |
| CPU coefficient hook | Conditional synchronous builder and exact output lane map | Native live-register/MDR/flags/stack preservation and post-builder placement |
| Output behavior | Host lane/bounds/neutral tests | E-P7 pixel calibration, timing, hardware and recovery validation |

The [native UI contract](../../docs/ep7/NATIVE_UI_ADAPTER.md) explains why changing
only the list length can destroy the child then leave null content. The
[hook/ABI contract](../../docs/ep7/NATIVE_HOOK_ABI.md) describes four self-authored
**unresolved tail forwarders**, not C-callable adapters or installed hooks.
`check_native_forwarders.py` is an optional compile-only check using the separately
built, hash-pinned GNU assembler; its object is temporary, unlinked and never run.

No firmware packer, patch offsets to apply, linker image or camera installer is
provided. Native calls must not be made by casting the normalized C callbacks
or these headers onto firmware addresses. Host sanitizers do not close these
native proof obligations.
