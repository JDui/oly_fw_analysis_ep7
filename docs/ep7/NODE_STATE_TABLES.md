# Finite tables are established, lifecycle closure is not

Independent bounded review of exact E-P7 1100 main. No firmware execution or firmware patch. This batch adds four concrete node-free sites, finite table identity, and a specific callback-state exit obligation.

## Actual controller table identity / default

Main event loop60289852 loads ROM base6042d570 at89861. A state record is20bytes: currentstate62234fc0 indexes it; +16 is ordinaryevent table. State33 record6042d804=(33,nameptr,entry602a26aa,secondarytable6042d26c,eventtable6042d28c). State34 record6042d818=(34,nameptr,entry602a2b82,secondarytable6042d324,eventtable6042d344).

State33 ordinary table is exactly18 rows atd28c..d31b, sentinel(0xffff,0) atd31c, exclusiveendd324. State34 has22 rows atd344..d3f3, sentinel atd3f4, endd3fc. Complete event/handler lists are in report. The dispatcher scans8-byte rows, compares event ID, and calls row+4; sentinel yields d2=65535, diagnostic path, then state-processing routine89c5e. This is **not** a destructor/defaultfree. State-specific secondary event tables (+12) and deferred-callback service are separate channels; ordinary table completeness is not complete event-system coverage.

## Additional frees reachable from this controller

* **602a427d**, event43 handler41df second queue drain. Existing first loop frees node at4220. Second loop pops queue6223e2f0 into d2=wrapper;425b dereferences wrapper[0]→a3=node;427d frees node;4286 separately frees wrapper. Actual producer is event4c's2a66 branch:2afa allocates4bytes,2b04 writes original node d2 to wrapper[0],2b0d enqueues wrapper. Therefore4286 must NOT be registered as another nodefree.
* **602a44d8**, helper446d reached directly by event4c handler2b32(node d2→a0)/2b34(call446d). At446d a0→a3=node;44ba/bb computesnode+4, OR8 then mask24 and conditional44d8 free(a3). Distinct from event4e's4461; sharing bitmask logic does not merge callsites.
* **602a2cb9**, state34 event42 handler2c8c: packet+8→a3=associated,associated+8→a2=node, updates node+4 OR0x10/mask0x18, free(a2).
* **602a2d0d**, state34 event4c handler2cd2: packet+8→d2=node, updates node+4 OR0x08/mask0x18, free(d2).

Thus a list of prior nine distinct node-free instructions is still incomplete. These four arise from finite supported controller routes, not a globalheapfree scan. In contrast event55 handler2b56 frees envelope/args at2b6f/2b77, and event44's c4d2 frees metadata; these must not be confused with nodes.

## Concrete state escape, not hypothetical arbitrary callback replacement

Event4e (433c) requests state34 at43cf/43d2. The secondary cancel/control handler452f likewise requests34 at4585/4588. Setter89c18 writes desiredstate62234fc2, updater89c5e installs it into62234fc0 then calls the new record's entry+8. Therefore pending node-related event42/4c can be dispatched through the different state34 handlers; hooking only state33 entries is insufficient. This static trace does not force a particular runtime ordering.

State34 entry2b82 registers four completion callbacks through6028a74c. One explicit exit is602a2d33: registration2be6 suppliescallback2d33,2bec suppliesmask49280(0xc080),2bf5 calls registrar; callback2d36 setsstate19 and2d39 invokes89c18. Registrar stores callback in a 12-row RAM array62234ff8,20bytesperrow. Service6028a882 requires all four mask intersections with runtime groups62234fe4/fe8/fec/ff0 to be zero, invokes row[0] via indirect calls(a0) at8d9, then clears callback. This is a bounded, concrete deferred callback mechanism, not an unconstrained claim that every global callback can change.

The finite local state set is33→34→19 at this observed exit. **No assertion that these are all reachable camera states**, or that the callback mask intersections being zero proves nodequeue/currentnode/associatedrecord quiescence. Establishing that invariant requires mapping the exact flag producers and callback order, or an install policy that revokes the supported registry/context generation before this explicit exit and safely handles any subsequent native free. Both approaches require review; merely pinning the ROMtable does not itself revoke still-live registrations.

Node also escapes to global6223dd54 at3052/3064 and an asynchronous descriptor6223df64 at2f91/300b (callback6029e8f1 stored at2fff/3005), already visible in earlier read-only disassembly. No proof that these are dangling; they are ownership paths requiring completion/reuse accounting. They are not evidence of free space or justification for reading a trailer without allocator membership.

## Verification / bounded stopping point

`tools/ep7_node_state_tables.py` pins both full tables and exact state records; checks91 selected instructions on a temporary copy of the SHA-verified input with explicit trusted objdump argument/hash. Local actualstock static test passes plus two input-free guard/table-shape tests. Actualstock test skips when proprietaryfixture or trustedtool absent; skip is not pass evidence. This does not execute MN103 branches.

Bounded remaining obligations: secondarytable cancel path plus fixed callback-mask quiescence at34→19; classify all transitive node aliases in the documented33/34 handlers; cover explicit four new revocations without counting wrappers/metadata. No broad no-free/no-stale assertion is made, and no unrelated-camera-FSM exploration was undertaken.

## Safer bounded admission/revocation seam (policy not installed)

The [subsequent guard review](NODE_STATE_GUARD.md) corrects the initial exit-only
proposal: same-state33 reentry also commits and invokes entry logic, so it must
revoke the old generation. Two native deferred-service CALL boundaries, not only
the first one, are required by the compile-only bridge.

There is a concrete common state-commit seam, distinct from request setter89c18. At89c79 old currentstate is d2;89c7f new pendingstate is d0;89c85 stores oldstate to62234fc8;89c8b writes d0 to62234fc0; subsequent89cfa invokes newstate entry. A callsite-specific adapter before89c85 can receive these exact old/new operands, revoke all supported admissions on every actual commit with old==33, including33→33, then let native commit proceed. Revoke means registry validity/context generation only, not free vendor objects. Preserve all live native registers/flags/stack obligations; no placement/assembler patch established here.

This can intentionally end qualification before state34 disposal. Existing node memory may stay live and native processing may continue, but no new H/L capability may be derived from that revoked node. An already-copied immutable image snapshot can remain valid under its separate metadata/job lifetime contract; this guard does not globally erase captured-image H/L. Never requalify an old node on state33 reentry using pointer or tag alone. New node admission needs reviewed fresh-allocation/population provenance and a new generation; an independently qualified sidecar need not enlarge the native node. Registry init must clear at controller initialization (direct currentstate store897d7), not just normal exit.

The exact-literal scan found21 references to currentstate62234fc0. Reviewed absolute store opcodes occur at897d7(initialization) and89c8b(commit); other reviewed literal references read. This is a bounded direct-reference observation, not proof that no indirectpointer/storealias or otherCPU can modify that memory. The supported installation therefore needs an explicit controller-thread/entry contract and coverage of reset/reinitialization; do not bypass this remaining requirement with an absence claim.

The observed eventloop dispatches one handler then calls89c5e;89c5e first runs deferred service8a882, then commits requested state, possibly iterating for new requests. This establishes local sequential instruction order only. It does NOT establish a global lock or that arbitrary foreign calls to89c5e cannot race registry readers. A same-controller admission/revocation contract plus neutralization on context mismatch is the bounded design; cross-context allocationregistry operations still require their own synchronization evidence.


## Reproduce

Run `python tools/ep7_node_state_tables.py --decoded generated/ep7/main.decoded.bin --objdump toolchains/binutils-2.45-build/binutils/objdump`. The decoded image is a private local input and is not included. `tests/test_ep7_node_state_tables.py` skips its actual-stock integration check when the private input/tool is absent; guard/table tests remain available. No firmware code is executed.
