# Kind19 capture-to-job route and historical RecView scope

Exact1420/1100 only, read-only static analysis. This closes a conditional
selected capture-ID → kind19/0x2001 metadata → descriptor → fresh-job chain.
It does not establish runtime branch selection, generation propagation or camera HSL.

## Closed selected-node callback registration and first ownership handoff

602a2731 sets a1=sp+4. 2755/275b stores callback602a2d43 in firstword; subsequent
words hold2ec7,2ef7,2f57,etc. At27de a0=6223d8a0;27e4 calls6029ad23.
6029ad23 copies17words froma1 into6223d134 atad2d..ad32 and initializes engine
state at6223d0d0/d2/d4/d8. Thus the firstcallback's ROM→RAM registration is
explicit, not merely a pointerxref.

6029ae61 saves its incoming a1(workrecord) atsp+4. If workrecord+4 low16==0,
it calls callback pointer6223d134 at aeb8, then restoresworkrecord and stores
returned a0 into workrecord[0] at aebc. Therefore actual selected56-byte node
returned by2d43 flows into a generic engineworkrecord. This is an earlier concrete
sidecar capability transfer point than the downstream materializer's rawIDlookup.
A generation capability can be associated with independently ownedworkrecord
without TLS, but only after matching node lifetime and its original allocation.

One directcaller6029afce peeks an engineworkrecord fromlist6223d0dc. Atb018/19
passes workrecorda1 and enginea0 toae61; afterreturn it testsworkrecord[0], marks
workrecord+4 and storesworkrecord at engine+40 pointee+440. Atb047 loads callback
6223d13c (thirdtableword=602a2ef7), passes workrecord[0] as a1, engine as a0,
original d2event as d0, callsindirect atb058. So selectednode remains actualpointer,
not merelyID, through this firstgeneric callback.

2ef7 receives nodea1 intoa3 and usesnode+8 associatedrecord andnode+44 sequence.
This callback modifies native capture-stage parameters; it does not itself build
kind16 commandmetadata. Other sameworkrecord callbacks are installed in the table.
No engineworkrecord lifecycle/generation guarantee is inferred frompointerstorage.

The current continuation binds [engine reset epochs and callback qualification](ENGINE_WORKRECORD_EPOCH.md):
both callback-table initializers and the workrecord-pool initializer now revoke
capture admission before native writes. The normal selected-before-complete order
is established only for a serialized cycle; callback execution-domain/exclusion
and mailbox delivery still require review.

## Concrete event-envelope identity transport and later mutation

ROM event pairs at6042d2dc/e0=(0x4b,602a281a),6042d2e4/e8=(0x4c,602a2a66),
6042d2fc/300=(0x55,602a2b56). These rows establish mapping entries, not every
runtime dispatcher/state. Callback602a3042 emitslogicalevent0x4b via6020c0f0.
That helper forms12-byte payload {u16eventstatus,d1eventcode,a0pointer} atsp+4;
6020c101 later copies3words from receivedrecord+8 to its destination.
Eventhandler281a reads incomingpacket+8 as56-byte nodepointerd2. Associated
record isnode+8. At2903 it storesnodepointer into associatedrecord+8.

281a calls602a4d34 at292e with d0=nodepointer,a0=6223d41c,a1=global6223d414.
4d34 allocates an8-byte callbackenvelope and12-byte argumentblock. Stores context,
IDcontext and nodepointer at arg+0/+4/+8 (4d4b/4d4d/4d50), callback4d7f at
 envelope+0, argpointer at+4. Queues via6020beb4 to handle60040e58 at4d75.
4d7f reloads these exactthree arguments and calls602a9647 at4d92, then sends
logicalevent0x55 with callbackenvelopepointer. Handler2b56 follows envelope+4,
arg+8(node),node+8(associatedrecord), calls602ac6d8 and frees bothenvelopes.

This proves another explicit pointer-preserving asynchronous transport boundary,
but also proves capture data is written AFTER earlier8dbd. 9647 resolvescapture
at9678 then writes manyfields; e.g.99b7 calls60300068 and9a03 copies32bytes to
capture+1972. Therefore “sealafter8dbd means wholecaptureimmutable” is false.
ImmutableH/L snapshot can still remain fixed, but a wholecloneepoch protocol must
track relevantlatermutators or qualify a morelimitedmatching-data contract.
These envelopes are not the downstream300-byte descriptor; do not conflate them.

## A distinct branch: kind19, not kind16

281a calls602ac141 with associatedrecordpointer at291e onassociated+6!=1;
c141→c1e1 onits ordinarybranch. One branch c3de calls602ac748. c748 allocates
148-byte metadata, stores captureID atmetadata+8, dispatch0x2001
at+72. Atc84f stores commandkind19 atsp+12; c869 sends16-byte command through
handle60040d72 using6020beb4. Thus despite matching148-byte metadata size and
samequeue, this is **kind19**, not the auditedkind16 capture-ID branch.
The precedingc3d9 calls602ac8d0, which dereferencesassociatedrecord[0] atc8dc,
so the actual c748 inputd0 is captureID (correction to initial exploratorynotes).
Do not automatically attach H/L through kind16 handling. Several other c1e1 branches queue or emit completion
and were not expanded into all capturemodes.

The previously auditedkind16 producer602eea84 writes its incomingd1 atmetadata+8
and dispatch0x100d at+72, but no node→that incomingargument join was established
here. Its presence is not evidence that0x100d is the initialnormalcapture route.

## New direct sourceID→kind19 descriptor→freshjob closure

Fresh producer3116 writesID toassociatedrecord[0] at3196. Later selectednode
holds thatassociatedrecord atnode+8; handler281a carries it throughc141/c1e1.
On admittedbranchc3d7..c3de: a2=associatedrecord; c8d0 returns[a2] captureID;
c748 receivesID, storesmetadata+8. Kind19 materializer0466 copiesdescriptor+56
into+116;048b resolvesID via6029b9d1;0494 storescapturepointerdescriptor+28.
This now closes a realcapture-ID chain, although generation transfer is stillnewcode.

Routingtable6053adbc+19*4 (6053ae08)=603dfbcb. Kind19 dispatch2001 isnot2008,
thereforec25/c26 selects60040d74. Relay603ef892 after preprocessingfb6d tests
kind19 atf92b and selects60040e32, NOTthekind16 e34route. Receiver603ef94a
calls603f04b9 preprocessing atf973, thenforwards300-bytedescriptor to60040d7a
atf984/f98c. Receiver603f26a1 obtainsit at26b4, calls603f28da admission/preparation
at26ee, requiresreturn0 at26f6. Dispatch2001 differsfrom2005/2002/2008 and
selects603f2800 at2722.

603f2800 is a distinct wrapper aroundthe SAME nativejobfamily:
- 2832 helper603e611e fillsconstructorparameters;
- 283e calls603537eb, storesreturnjob into descriptor+36 at2845;
- onlyzero errorhalfwordsp+12 entersconverter603e62d1 at2850;
- onlyzero converterresult + nonzero603ed4bd enters603e61b8 at2890;
- successpostprocess603e6b83 at28b8;
- cleanup603e6c8d at28c0, then603ed7e2 at28c8; resultstored+192.
This is NOT constructorcall603e6d3e orwrapper603e6d04. ActualCPUstage/type0/raw11/
owner0 eligibility must stillpassnormalreaderpredicate; no claim everykind19job
runsCOLORorCPU. A new allocationveneer admission would explicitly whitelistthis
provenwrapper/callsite, not pretendtheoldsitecoversit.

603ed4bd returns1 exceptthecompound descriptor+262 bit2000,+250==ffff,
and60bd82cf returning0. 603f28da computesdescriptorfieldsandcanreject; preserve
itsresult, don'tpatchaway. Nativepreprocessing/sourcevalidity remainsstockcontract.

## Kind16/100d historical scope identified (not normalcapture proof)

Only a caller toinnerbody602eea8a was foundat6088ac70; entryeea84 itselfappears
in tracingmetadataat6088ac7e. Wrapper6088abd5 getsplayhandle throughobjectvirtual+4
then602e0469, andtakehandle throughotherobjectvirtual+4, passesd0play/d1take.
Diagnosticstring60b03e6e explicitlyreads
`[RecView] createAfFineTune nPlayHandleID,nTakeHandleID %d, %d  `.
This labels the concrete100d producer RecView/createAfFineTune; it must notbe
presented as a demonstratednormalcapturepath. No guessaboutUI availability or
specificbodyAFfeatures followsfromthelabel. Existingkind16researchremainsvalid
foritsconditionalroute, butinitialnormalcapturequalification shouldusekind19chain.

## Same-ID and new wrapper arguments checked, reproducible candidate

No equality assumption is needed for the freshproducer:3116 keepsallocatedIDd2,
316f writesd2 atnode[0];318f calls602972e3 with nativecallmask[d2,a2], obtains
associatedrecorda0;3196 writesd2 atassociatedrecord[0];319b writesa0 atnode+8.
The two identities are explicitly initialized equal on this route. Laterreuse or
mutation still needs the capabilityprotocol, not equality ofcurrentintegerID.

Atnewctor283e: a0=32-byte zeroed parameterblocksp+16 (filledby603e611e),
a1=&halfworderror atsp+12, d0=0. Resultd0 becomesdescriptor+36. Errorhalfword,
notpointertruthiness alone, gatesconverter. Converterresult becomeserrorhalfword;
zero gatesprocesspredicate. Originalprocess/cleanupreturns preserved. 603e611e
usesdescriptor+28 source, installs callback603e7b83 and source-derived flags;
constructorparameters are not invented constants or blindly copiedfromPENF.

The worker's post-wrapperpath calls603f2ad0, thenACK603df97d at603f2769.
ACK occurs AFTER wrappercleanup28c0 onthisroute. Exactmetadatafree/abort ownership
notclosed: do not retain rawheapmetadata pointer indefinitely or assumeACKfreesit.
A proposed capabilitycopy atmetadataallocation must carrya nonreusedmetadataepoch
beforequeue. Materialization can copyimmutableHL into a descriptor-associated
capability, but every300-byte relaycopy needs explicit capability propagation;
alternatively retainindependentmetadata-capability untilqualifiedACK, with guarded
lookup usingdescriptor+48 and metadataepoch, notrawID. Early/missingtoken→permanent
neutral; oncefreshjobhasitsownimmutablecopy it no longer needs sourcecapturealive.
Noneofthese newsidecar/lifetime operations is suppliedbynativecode.

Reproduce with `tools/ep7_kind19_capture_route.py --stock /local/stock.BIN
--objdump /trusted/mn10300-objdump`. The [actual report](../../research/ep7/kind19-capture-route-1100.json)
and `tests/test_ep7_kind19_capture_route.py` preserve the evidence checks.
21windows/419instructionwitnesses,kind19routingtable+RecViewlabelchecks,
8tests pass andexactstockrun passes. This qualifies conditionalcall/dataflow,
not actualruntimebranch selection. Prior frozen372-witnessprobe unchanged.
