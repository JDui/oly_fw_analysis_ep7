# Bounded capture-sidecar admission: new exact-1100 joins

Read-only stock analysis; no native code execution or patch. Source stock SHA256
9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb.
This extends prior ownership/capture clone notes, not a complete lifetime proof.

## Allocation to actual populated capture

- `6029b4e7` is a registry allocation wrapper: saves incoming mode d0 in d2,
  loads signed halfword handle60040a26 and calls6005168d with d1=-1 atb4f2;
  invokes6029b512 atb4fa, saves returned ID, then60051762 atb507 before returningID.
- `6029b512` calls6029bdc9 with d0=0. That scans IDs1..25, flag halfword at
  registry6223d178+24*ID equal zero, returning26 if none. Allocation returns255
  on failure. Mode-dependent auxiliary allocation precedes6029bdec atb655;
  success returnsID atb682, failure runs cleanup includingbe33 atb66c.
- `6029bdec` allocates pool selector1500, stores handle record+16 and resolved
  pointer record+12, resets pointer+27078, sets flag4, returns0. Existing pool
  evidence establishes25 configured slots of41984 bytes, not spare capacity.
- Actual ordinary producer602a3116: capacity helper6029ba1e, call6029b4e7
  at3145 with d0=0, rejects255. Additional6029bc8b failure releasesID through
  b686 at315e. Allocates56-byte transport node at3167, storesID[node+0] at316f,
  writes sameID through global6223d414 at31a4. Returns node in a0.
- The already-reviewed immediate population paths are now connected to allocation:
  602a31c7 calls3116, stores node a2, tests3204, then reads globalID at31e3/31e9
  and invokes602a7ea0 at31ea. Also440a→442c and4480→44a3 do the same pattern.
  Failure calls31a9 on the node instead. Population resolves registry pointer
  into d3, copies the stock template, rawmode/selector and12S halfwords.

This is an actual fresh-slot→transportID→population join, not proof the global
cannot be replaced by another task between calls. The native allocation envelope
ends before population. Do not read current GUI H/L only at later job construction.

## Retirement and reuse

- Node cleanup602a31a9 readsID[node+0], calls6029b686 at31ab, then frees node via
  60022732 at31b1. Another successful-consumer cleanup at602a4459 callsb686
  conditionally on node+44>1 before freeingnode at4461: not every node free means
  capture retirement. Revoke at capture retirement, NOT blindly on every node free.
- b686 validatesID1..25; checks record+18 (diagnostic path when1), then brackets
  b717 with6005168d/51762 on samehandle60040a26 (b6ed,b701).
- b717 callsbf01,bfe7,be33,c0d6,c1a0. be33 checksflag4, releases auxiliary
  capture+27078 ifnonzero, then record+16 via603db89e atbe5d, and clearsflag4 atbe6a.
  It leaves record+12 stale. Proposed sidecar revocation must happen BEFORE
  be5d pool release/reuse, while oldidentity is still valid, not afterflagclear.
- Allocation-failure cleanup callsbe33 too, so revoke must be idempotent and
  tolerate no registered sidecar. Entry/pointer alone is not an allocationgeneration.
- API6005168d is supported by diagnostic strings OlySmWtCpu/OlySmWt and calls
  60053c92 or600370af;60051762 uses OlySmSiCpu/OlySmSi and calls60053c5e or60035b62.
  This supports a semaphore wait/signal interpretation, NOT qualified H/L locking:
  allocation/release wrappers do not branch on returned status; actual scheduler,
  failure policy, lock order and population spanning critical section unproven.

## Clone identity transfer boundary

Previously reviewed603edb9a selects source via descriptor+116 registryID when
+260!=0, otherwise descriptor+28. Source is kept a3;603ed63d requests41984;
returned clone pointer published global622933dc and descriptor+28 BEFORE
27332-byte memcpy at603edbce. After copy return603edbd5 still precedes function
return and is a possible explicit clone-sidecar transfer boundary, not an installed
hook. A3 identifies source and descriptor/global identifiesclone, but no snapshot
transfer happens in stock. Do not append to uncopied tail or infer raw pointergeneration.

Paired603edbd8 releases globalclone via603ed6c4 atdbde then clearsglobal.
Proposed revoke must precede release; asynchronous consumer completion remains
unqualified. Existing worker loop pairing is not sufficient to assert quiescence.

## Actionable installation contract, not yet a safe native hook

1. Reserve sidecar identity on successful capture poolallocation; key includes
   registryID, pointer, independently nonreused generation. No H/L snapshot yet.
2. Populate immutable24H/L values at capture-time seam after rawmode/selector/S
   copies (602a86b7 candidate), validating the reserved generation and raw11,
   selector1..4. Capture settings under a separately qualified lock. Repeated
   population of an alreadysealed generation must fail closed or explicitly create
   a new snapshot revision; this pass does not prove eachID populated exactlyonce.
3. Clone must copy the sealed snapshot into a separate clonegeneration before it
   may feed a freshjob; later source revocation cannot invalidate that copiedvalue.
4. Revoke source before poolreleasebe5d, clone beforedbde. On lock/revocation
   failure, do NOT allow reuse as though cleanup succeeded; native quarantine or
   abort policy still needs implementation.
5. Descriptor→job constructor may consume only this attachedsnapshot, not a fresh
   currentGUI read. Direct descriptor paths, additional population callers,
   cross-task publication, all release alternatives and liveness remain gates.

A scan found ten candidate directcalls to602a7ea0; only the three above were joined
here. This result does not certify burst/movie/playback or every capture producer.
No native ABI veneer, synchronized sidecar store, allocation failure recovery or
safe spare region is supplied. The useful closure is concrete lifecycle sites and
one actual fresh capture route; the remaining blocker is ownership propagation and
serialization, not absence of a capture pointer or need for more UI videos.

## Follow-up: earlier publication disproves a simple postpopulation assumption

602a3204 actually enqueues node (a2) in list6223e314 via6020b98b at323d,
inside6006a922(2)/6006a96b envelope. The caller invokes this BEFORE population31ea
(and before442c/44a3). Thus the fresh route publishes a node pointer before the
snapshot is initialized; this alone does not prove a race, because consumer task
ordering is not qualified. It does rule out claiming publication-after-population
from those callsites. 602a3256 pops a node via6020b9ff at327b; its sole directcall
found at602a27f0 immediately destroys the returnednode via31a9 on nonnull.

Actual selection callback602a2d43 inspects the list using6020b968, peeks via
6020ba9f at2d6b, checks node+0 and associatednode+8/+6 state, eventually removes
via6020b9ff at2ea9 and writes node+44 at2ebf. It returns the selected node in a0.
This is a concrete earlier capture-node admission point, NOT yet the downstream
300-byte processing descriptor or proof of immutable metadata transfer.
602a8dbd afterpopulation resolves the sameID again at8dca and writes additional
capturefields, including a conditional rawmode8→4 conversion; it is not a pure
publish call and must not be mistaken for the processing descriptor builder.

### Initial subset policy and exact remaining join

Shared allocationb512 success + retirebe33 can support a monotonic sidecar for
this reviewed fresh route without task-local storage: ID/pointer/generation is
explicit registry state. But a consumer must carry the generation, not retrieve
'current generation for this ID' after potential reuse. Proposed states:
RESERVED→POPULATED→SEALED/TRANSFERRED→REVOKED. Only RESERVED/POPULATED can receive
another population snapshot; SEALED repeatedpopulation is excluded/neutral. A
node exposed beforepopulation is not admitted until POPULATED; consumer entry
must atomically bind node lifetime to that generation and markSEALED before copy.
These are new synchronization requirements, not native behavior established here.

For this initial subset, 602a2d43's successful node selection is a concrete place
to bind/seal a generation capability to a separately owned transport identity,
provided caller ordering proves populationcompleted. Existing downstream
materializer603dfc7a kind16 chooses registryID from copied metadata; no generation
is present. This pass has NOT joined selected56-byte node→that metadata producer
with a qualified lifetime, so installing onlyb512/be33 and looking up generation
atmaterialization is insufficient (ABA on reusedID). Until that transfer join is
qualified, reject/neutral rather than currentGUI read or raw-ID rebinding.

Reproducer generated/ep7/capture_attachment_candidate.py validates16 bounded
windows/372 exact instruction witnesses after stockSHA guard, including the
prepopulation enqueue. Eightfocusedtests pass; outputcapture-attachment-candidate.json.
Only metadata/window hashes, not extracted firmware or listings, are published. The selected-node callback exploration above remains notes, not yet
added to the frozen probe's evidence set.

## Clone copy race boundary: before/after epoch, not postcopy-only

The clone helper gives a concrete bracket without task-local context:
- At603edbb3 the chosen source pointer is still a3, before allocatorcall and copy.
  A full-function adapter could hold an independent capability and copied24HL
  snapshot in its own invocation frame. It must not find a capability by rawID
  alone: require the descriptor's previously bound allocation+population identity.
- At603edbcd a1=a3 passes that same selectedsource to memcpy; destination was
  already published in descriptor+28/global. At603edbd5 the copy has returned.
  Compare the original capability/revision with current sidecar state under lock;
  require stillSEALED, sameallocationgeneration, samepopulationrevision, notrevoked.
  Only then attach the previously captured H/L value to a freshclonegeneration.
  A change, missingcapability, failedlock, or already exposed unqualifiedclone
  permanentlyneutralizes that clone/descriptor; no later retry using newsettings.
- The source must become MUTATING before the FIRST stocksource write, e.g. entry
 602a7ea0 before60300055 templatecopy, not merely when H/L is sampled at86b7.
  Otherwise pre/post reads could both see oldSEALED while stockcopyinterleaves.
  No counter wrap/reuse is allowed. An overlapping population invalidates the
  transfer even if it finishes before postcopy. Original capturevalues remain
  independently copied in the invocation frame; no late UI read is involved.

These checks can fail neutral without proving scheduler serialization, provided
ALL relevant admitted-source mutations enter the epoch protocol before writing.
The freshroute also calls602a8dbd AFTER602a7ea0. 8dbd resolves capture at8dca and
writes further fields until return91eb. For this narrowly admitted producer, seal
only after that call returns (31fc /4443 /44ba), with24HL sampled for the
owned captured profile at the population boundary described below, not from a
later job-time current GUI selection. Node was enqueued earlier; any earlyconsumer
must be permanentlyneutral, never backfilled. The three return addresses differ
because they belong to separate producers; start by admitting one, e.g. the call31ea route.

No exact adapter is supplied here. Required open joins: sidecarcapability transfer
from selectednode to commandmetadata/descriptor, writes to capture after8dbd on
that route, source retirement coverage, and clone publication-before-validation
policy. Prefix-copy epoch guards would detect tracked sourcewrites but cannot
certify untrackedones. This is an actionable fail-neutral integration contract,
not proof the existing source is immutable or an unconditional hookready claim.


## Whole-function return envelope refinement

Population normalreturn8874 follows the final typedgetter886a andstore8871.
There is no Boolean/error return contract: d0 remains typed data. Postpopulation
8dbd normalreturn91eb follows605e61d7 at91e4; caller31ea/31f7 neither tests d0.
Admission must use normal control return plus independently valid generation,
not d0==0. An alternative avoiding86b7 midfunction instrumentation is to sample
all24HL under the portable settingslock after602a7ea0 normalreturn, selecting the
profile from ownedcapture rawmode24053/selector24083, then leave stateUNSEALED
through8dbd. This gives coherentHL for that capturedprofile, not sameinstantS.
Seal only on matchedpostpopulation normalreturn; allunknown/missing/error/unwind
paths stayneutral. Earlier suggestion to require86b7 sampling is not mandatory;
late jobconstruction/UI currentprofile selection remains forbidden.

Probe now includes population entry/templatecall, populationreturn andpostpopulation
return windows (16windows/372witnesses). Full functions/callees are not reaudited
for memoryfaults or globalatomicity by these bounded operand witnesses.

## Reproduction

`tools/ep7_capture_attachment.py` verifies the exact-stock hash before invoking
trusted objdump; the [published report](../../research/ep7/capture-attachment-1100.json)
checks 372 instruction/operand witnesses in16 bounded windows. The corresponding
tests reject wrong stock and altered operands. No proprietary image/listing is included.

### Epoch checks are not a native source-lifetime guarantee

Pre/post epoch checks do **not** pin the source or cure a memcpy that read freed
storage. The native caller must keep the source live for the complete copy.
Because the destination pointer is published before the copy, clone consumers
must remain H/L-neutral until the copy and sidecar validation finish; an earlier
consumer must not be retroactively attached to a later snapshot. This qualified
fallback is not a proof of scheduler serialization or complete mutation coverage.
