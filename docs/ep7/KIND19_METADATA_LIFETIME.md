# Kind19/2001 heap metadata ACK/free boundary (bounded static evidence)

Separate notes; frozen419-witness route probe unchanged. Exact1100 read-only.
No execution of firmware, no installedadapter or nativecore changes.

## Submission and failure

602ac748 allocates148 bytes via60022700 atc74c, retainsmetadataa3. Atc846
storescallback602ac873 atmetadata+4. Command stackfields:replyhandle60040daa at
sp+4 (c857..c85e),replyevent68/0x44 atsp+8(c853/c855),kind19 atsp+12(c84f/c851),
metadataa3 atsp+16(c860). Sends16bytes to60040d72 via6020beb4 atc869.
6020beb4 invokes600514b6 and returnsitsstatusd0 atbeec; nonzero logsdiagnostic.
Producerreturnsimmediatelyatc870: no localconditionalmetadatafree orretry.
Therefore a sidecar submit hook MUST observe sendstatus. Failure is not proof
nativeheapmetadatawasfreed, and caller must not invent ownership ofa failedsend.
This localpath alone does not license freeingstockmetadata onfailure.

## Normal ACK proves metadatafree afterjobcleanup for a bounded branch

Newworker603f26a1 runswrapper603f2800, whichcleanupscapturejob at28c0.
Afterwrapper it calls603f2ad0 at2736, then603df97d at2769.
ACKhelper forms12bytes:status atsp+12,descriptor+44 atsp+16,descriptor+48 atsp+20;
usesdescriptor+32 replyhandle and603eeba4 atf9c3. For producerabove thisis
{status,event0x44,originalmetadataPointer} deliveredto60040daa.

FSMqueueconsumer60289b0e..b1f receives12bytesfrom60040daa;matchespayload event
against8-byte stateeventrows atb83..b97 and invokeshandler withpayloadpointera0.
ROMrow6042d2bc/c0=(0x44,602a3b87). Handler3b87 calls602ac46a at3b8a.
c46a readsstatuspacket[0], maps7937→0. Ife798==1 ore79a==1 it dispatchescf50
(alternatepathNOTqualifiedhere). Otherwisec496 loadsmetadata frompacket+8.
For e7af!=1, command2001 invokes6029bd60(metadata+8captureID), clearsglobal
6223e7b0, calls602ac515, then **60022732(metadata) at602ac4d2**.
For e7af==1 it skips2001helper butstillreachesfreec4d2. Latermodecallbacks do
not establish genericquiescence. The callerstate table mayvary; onlynamedrowis
pinned, not everyactualruntimeFSMstate.

For the admitted normalACKbranch this supplies a real revocationboundary before
c4d2 and confirmsnormalmetadatafree occurs AFTER freshjobcleanup. The parent
captureallocation may retireseparately; copiedimmutableHL metadata capability
need not rereadsourceafterits creation.

## Early callback: exclude or explicitlymodel, never assumeone notification

603f2ad0 invokesdescriptor+20 callback with d0=1,d1=metadataPointer,a0=0
at2b08 ifdescriptor+206==3 andcallbacknonnull. This is BEFORE ACK2769.
Materializer603e0186/0189 mapsmetadata+4→descriptor+20.
Metadata+84 pointer is recordedat603dfe3e..fe42; fordispatch2001,
603e01db/01df→0223, lowbyte(metadata+84)→descriptor+206 at0232,
upperbyte→descriptor+262 at0259.

Producer e7af==0 branchc7d2 setsmetadata+84=2 (optionalhighbit4000 atc800),
so initialdescriptor+206=2 and earlycallbacktest==3 fails. Branches withe7af!=0
canput3, thusmustbeexcluded or separatelyqualified. Otherrelaymutations of206
stillneed guardingatreader/transfer, notjustinitialproducercheck.

Callbackc873 when invokedwithstatus1 emitslogicalevent0x5c withmetadataPointer
via6020c0f0; table0x5c routes can leadto602ac70a andreadmetadata. Hence a bare
assumption “onlyoneACKnotificationexists” would befalse forotherbranches; no
claim madeofactualUAF because scheduler/handler ordering differs andisunproven.

## Sidecarhandoff consequence and remainingexactgap

Normalroute singlethreadedworkerlocalcode sendsone300byte descriptor onward per
successfulreceive, and onlyACKs afteritsjobcleanup. This is NOT an exhaustive
proofagainstduplicate queueddescriptors, cancellationcopies, or extraACKroutes.
Therefore rawmetadataPointer lookup, evenwhileregisteredwithaninternalgeneration,
cannotuniquelyidentifyanoldqueuedcopy aftersameaddressisreallocated. A generation
heldonlyinside lookup table does nottravelwiththeoldpointer.

Usableimplementationboundaries withoutTLS:
1. Originalnode/associatedrecord capability copied to independentlyregistered
   metadataallocation beforec869; recordexactcapturedID + immutable24HL + epoch.
2. Eachknownmaterialization/relay can carryanexplicit independentdescriptorcapability,
   or retainmetadata-capability untilqualifiedACK AND establishone-owner/no-old-copy
   transportcontract. The latter proof isstillmissing, so donotclaimitcomplete.
3. Atfreshctor283e attachonlymatchingcapability; missing/consumed/earlydescriptor
   becomespermanentlyneutral, neverlaterfilledwithcurrentUI/sourcegeneration.
4. Revoke metadata-capability beforec4d2, withidempotentnormal/failedsend states.
   Failuretorevoke cannotbe treatedaspermission forreusinganexperimentalcapability.

A deliberatelyboundedfail-neutral design could refuseeverreadmittinganypreviously
seenmetadataaddress duringoneboot (finite tombstonetable; overflowneutral), which
wouldavoidABAwithoutglobalqueueabsenceproof, butthis is a NEW restrictivepolicy,
not nativeownership evidence or a substitute forpointervalidation. Explicit
per-relaycapabilitytransfer remainsmoregeneral. No suchpolicyimplementedhere.


## Reproducible scope

`tools/ep7_kind19_lifetime.py` checks254 instruction witnesses in8 windows plus
the event44 handler row. [Actual result](../../research/ep7/kind19-lifetime-1100.json).
This pins the cited reads/returns and bounded ownership edges; it does not prove
all transitive writes, every queued copy lifetime or native installation safety.
