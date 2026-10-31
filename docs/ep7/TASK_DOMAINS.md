# GUI task birth and kind19 worker domain: one bounded static chain

Exact stock1.1 only, no firmware execution. This finds a real GUI creation chain
and kind19 worker configuration, **not proof that the two run on the same core**.
It avoids treating shared instruction space as a scheduler/domain guarantee.

2026-10-31 update: [bootstrap-entry audit](BOOTSTRAP_ENTRY.md) now verifies the
actual kernel task-table consumer60032998, root+124/table600389d0 and the six-word
copy intoTCB+68..+88. The earlier6005b447 traversal below is not a task-creation
proof. The kind19 task006c is explicitly started at60191618 by domain0-configured
Usr3; live task/domain checks and teardown/alternate-start closure remain required.

## GUI birth is dynamic and inherits its creator's domain

GUI constructor60cfceba builds a four-word task spec atsp+12:
entry60dd5067, priority-class1, stack16384, parameter0; name pointer60f94108 is
`GUI_TASK`. At60cfcee5 it invokes607a791e. The entry60dd5067 calls60cfd311 at5079,
which continues through known GUI initialization/dequeue/preprocess/engine chain
and parent virtual0 dispatch. These are actual control transfers, not a name match.

607a791e obtains subsystem object through60779102, returns component+16 via
6077925e, then invokes virtual+4 at607a7979. Constructor607791cd constructs that
component via6077a4ab, which installs vtable60a80150; slot60a80154 is6077a542.
This closes the relevant indirect factory call, conditional on the initialized
subsystem object retaining its constructor-established table (not arbitrary RAM
corruption or replacement).

Provider6077a542 maps priority-class1→native55, passes entry as a1, parameter as
d1, priority/stack/pointer in stack slots, then calls named native task create
60051d66 at6077a601. The input d0=0 is **not a CPU selector**: wrapper stores it
atsp+12; later compares it to2 to decide whether to call task-start6003071f.
Raw task attribute byte is independently forced0 atsp+16. Do not derive core0
from either zero or priority1.

60051e53 calls raw task creation60030619, which allocates through60034e3f.
Allocator60034ee3 reads current-core word8050;34ee8 shifts it12;34eeb ORs selected
index into encoded task ID. That ID is stored in task control block+16. Therefore
this dynamically born GUI task inherits the creation execution domain. The
specific caller/task/core that reaches GUI constructor60cfceba is **not closed**
in this bounded pass. No task affinity/migration theorem is inferred.

## Kind19 processing worker has a concrete static configuration row

28-byte ROM row at600395a0 is:

| Field | Value |
|---|---|
| Configured task ID |0x006c|
| Attributes / parameter |0 /0|
| Entry |603f26a1|
| Priority |26|
| Stack bytes / supplied pointer |8192 /0|

The shared table base is600389d0. Consumer6005b447 reads first halfword as task ID
and calls60034ae3; its loop advances28bytes at6005b52d. Configuration pointer
60041220 points to this table. The ID's encoded domain bits are zero, but this
pass does **not** close the boot loader's mapping from this configuration to a
live task, nor all alternate worker entry callers. Consequently the report keeps
worker runtime domain unqualified rather than quietly treating a ROM table row
as a running-task observation. Existing kind19 route independently proves that
603f26a1 receives the descriptor then reaches603f2800→fresh native job→CPU stages
when its normal gates pass.

## Actual stop point and minimum qualification input

One dynamic task creation chain and its allocator encoding are resolved. A next
static question could target the caller of60cfceba or the specific boot consumer
of configuration60041220; this pass does not expand into the whole RTOS/boot map.
For the current same-domain provider, a tiny **future authorized** observation
would directly settle the important fixture without a broad memory dump:

1. successful raw get_tid status +16-bit task ID at the admitted GUI H/L write;
2. same pair at the exact capture-snapshot producer (selected-node/capture-bound
   point), because capture need not share GUI task;
3. same pair at supported kind19 fresh-job registration and synchronous COLOR
   observer, plus descriptor/capture capability correlation and admitted mode;
4. repeat across admitted lifecycle transitions (not merely one matching ID).

Do not log private images or dump arbitrary RAM. No such instrumentation is
installed/executed here. A numeric ID is not a lifetime generation token. Context
failure must still decline admission; a matching domain sample is not proof of
all callbacks, interrupt safety or migration invariance.

## Cross-domain result would not force a shared global lock

The current single-runtime host prototype is a design choice, not a stock rule.
If GUI/settings and image processing domains differ, a bounded alternative is:

- GUI/settings runtime and its new private semaphore remain in their domain;
- a **capture-bound value snapshot** is copied into independently owned metadata,
  not a retained UI pointer, task ID or last-job global;
- downstream processing domain registers that copied snapshot in its own runtime
  and private semaphore, then its synchronous reader uses the local registry;
- sequence/generation/admission and metadata lifetime are explicitly transported,
  with qualified native handoff visibility. Do not invent implicit cache coherence.

This can remove a cross-domain shared-mutable-runtime requirement, but does not
by itself solve the GUI→capture-producer boundary. That snapshot source must
still be serialized in its settings domain or use a qualified value handoff.
Likewise, existing pointer/metadata transport is not already an H/L value-copy
implementation: extension ownership, copying and release have their own open
contracts. No per-domain runtimes or new transport writes are implemented here.

`tools/ep7_task_domains.py`: pinned stock+objdump,59 exact operands/15 windows plus exact row and
vtable-slot checks. `report.json` metadata only; three harness tests pass.
Reproduce with the same `--stock` and `--objdump` arguments as other stock probes.
No firmware mutation, target execution, lock creation or device access occurred.
