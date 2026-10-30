# Concrete counterexample to five-site revocation sufficiency

Exact decoded main SHA `5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190`; trusted GNU objdump2.45, static-only. Probe checks73instructions plus4 eventrows.

## Original fresh-node normal route

3116 initializes associated+6=0 at3197/3198 and associated is linked as node+8 at319b. 31bb publishes this node to queue via3204, then population31ea/31f7. The same controller registered queue-pop callback2d43 and selected callback3042 (registration2755..27e4). 2d43 peeks queue, takes actual pointer d3 at2d72, pops at2ea9, returns d3 at2ec2. 3042 sends event0x4b with caller node a0 unchanged; event table6042d2dc=(0x4b,602a281a). The selected handler281a reads packet+8→d2=node and writes node into associated+8 at2903. ROM6042d814 points to this same table6042d28c; matching event rows are4b(selected),42(2937),4c(2a66),4d(2a1a).

**New normal free at602a2a00**: event42 handler2937 loads packet+8→d2=associated and associated+8→a3=node at294a. Associated+6 !=1 takes29c6 normal path. At29e4..29ea it ORs0x10 into node+4; if(node+4 &0x18)==0x18 then29ff→2a00 frees original node a3. It then recycles associated via60297328 at2a0f. This is NOT an envelope free, and is absent from five prior sites.

**Complementary normal free at602a2ab5**: event4c handler2a66 packet+8→d2=node. Under existing globals e33c!=0 and dd4c!=0, it ORs0x08 into node+4 and, when0x18 complete, frees node d2 at2ab5. Thus callback completion ordering chooses either2a00 or2ab5. This establishes a concrete static counterexample to five-site sufficiency for normal flag0 nodes, not arbitrary event timing or whole-runtime reachability proof.

Event42 actual producer in associated path:281a calls c141 at291e with associated pointer; c141→c1e1 retains it in a2. With paired queues available, c2e4 sets event66(0x42), c2e6 puts associated in d1 and c2e8 calls d656. d656 constructs12-byte event packet with event at stack+8 and data pointer atstack+12, sent fromstack+4 atd670, i.e. receiver packet+8 carries associated. Other branches can defer/queue; do not assume every capture immediately takes this branch.

Event4c actual local producer: callback2f91 setsnode+4 bit4 then calls302b; callback2ec7 setsbit0x20 and calls302b. 302b tests0x24 and emits0x4c with node a0 retained. Both callbacks are in controller callback registration at2763 and27ae; this is finite specific table/registration evidence, not a scan claiming all possible callback writers.

## Additional conditional sites

602a29ab is another node free(a3) in event42 associated+6==1 branch; predicate is(node+4&0x30)==0x30. 602a2a48 frees node a2 in event4d handler; known local emitter2edd sends4d only when node's associated+6==1. These are real additional nodefree instructions, but original31bb fresh path initializes flag0; independent transitions/alternatecaller qualification is needed before claiming these two occur for the sealed normal subset. Do not classify all callers of event4d solely from its one local emitter.

## Consequence and remaining boundary

At least2a00 and2ab5 must be included in any normal selected-node revocation proof; merely adding existing five sites leaves registry entries live after native frees. A finite table exists, but a complete closure proof still requires all callbacks/routes for the supported controller and aliases plus queue teardown. No globalheapfree hook proposed. No claim that absence of another directxref establishes no stale pointer. A registry remains unsafe until complete supported free/reuse coverage and explicit pointer lifetime assumptions are established; a trailer tag is not allocation-size proof.

## Probe correction and validation

The probe now takes explicit trusted objdump argument, records executable hash/version, writes only the SHA-validated bytes argument into a temporary local image, and disassembles that same image (not a second read of a global path). Uses shared require_instruction. Added missing node+4 inc4 witnesses and callback registration/event emit witnesses. Three checks pass: wrong-input rejection, exact-stock temp-input integration with global IMAGE deliberately invalidated, and a reference bitmask-order model. The bitmask model is NOT firmware branch execution; no test here executes MN103 instructions.


## Reproduce

Run `python tools/ep7_node_disposal.py --decoded generated/ep7/main.decoded.bin --objdump toolchains/binutils-2.45-build/binutils/objdump`. The decoded image is a private local input and is not included. `tests/test_ep7_node_disposal.py` skips its actual-stock integration check when the private input/tool is absent; guard/table tests remain available. No firmware code is executed.
