# Category4/5 portable UI adapter: native seams and remaining installation work

Exact E-P7 1.1/1100 static analysis; no firmware modification or native execution. `ep7_ui_adapter_contract.h` is a compile-checkable proposed portable interface only, NOT an address-cast API, native ABI definition, or working installer. Existing core owner may adapt names/types. All H/L is volatile, boot-neutral; stock S properties and callbacks remain stock.

## Concrete construction / forwarding / rendering / teardown seams

| Seam | Native observations | Adapter responsibility |
|---|---|---|
| GUI041d entry | 60e5dae9 passes group8/key463 to60e4cea8; result a0 stored61fc436c | Create a new UI lifetime token only after successful controller construction; never infer generation from pointer reuse. |
| Parent creation | factory0x34→60e260c7 allocates100bytes (d0=100→60a4ec03); constructor60e26108 installs vtable6118957c | Do not append fields past100. Extension ownership needs independently allocated storage or a bounded, generation-qualified owner registry. |
| Selector child | parent+76, ID193 initialization60e26188; native list4values/mask allocation count4 | A six-entry implementation needs six actual value/mask slots and normalized focus, not just count overwrite. Preserve0..3 order. No unused bytes claimed. |
| Content rebuild | 60e266a9 accepts parent in a0, saves it d3; destroys old parent+80 before selection; reads selector via virtual+4 into d0/d2 | Close old H/L child session before destruction; new4/5 must construct independent child, never reuse S writing handlers. Failure must not leave null+80 reachable by forwarding. |
| Public mode |60e266e9 gets service607f9062; calls its virtual+8 at60e266fb with d0=111,a1=sp+8; result stored caller memory | Veneer passes observed publicmode54/55/56/64 to portablecore. Category4→H,5→L; outsideCOLOR disable both and normalize focus. No raw11/public54 conflation. |
| Hard switch |60e266fd..60e2670b supports0..3 only; default60e2670d returns after oldchild destruction | Newcategories require replacing/expanding this branch, not merely changing list193. Stock paths0..3 call their original factories unmodified. |
| Content forwarding |60e26270,60e262c0,60e26397 load parent+80 intoa0 and call child virtual0, preserving incomingd0/d1 | Observed message shape is a0=child,d0=event,d1=argument, d0 returned. Portable API takes normalized events, NOT these raw register assumptions as a C ABI. |
| Extra parent gates |60e2622f and60e2627f forward onlycategory0;60e262cf explicitly branches0/1/3;60e263a6 branches1/2/3 | Installing a new child alone is insufficient: parent category guards must admit intended H/L input. Need per-event veneers that preserve stock behavior0..3 and intentionally route4/5. |
| Viewer |factory0x84→60e26a3d alloc408bytes; viewer vtable61189ba8 draw60e26ab0/dtor60e26a7c | Do not append viewer fields. Newlabels/grid must use explicitly owned storage and a qualified draw adapter. |
| Viewer observations |creator stores parent atviewer+384; draw calls parent virtual+28 withd0=0/1 to obtain selector/content, stores+388/+392; selector virtual+4 stored halfwordviewer+396; public111 via servicevirtual+8 toviewer+400 | A viewer veneer can pass category/publicmode to `frame`, render copied scalar values/selection, and avoid direct core pointer persistence. Native categories0..3 retain original draw. |
| Draw switch |60e26b68..b76 only0..3;category1 COLORdraw60e27289,MONOdraw60e27162 | NewH/L requires new4/5draw arms; stockCOLORdraw reads stock data and is not automatically an H/Lrenderer. No touch hitbox proven. |
| Child teardown |rebuild60e266bb..dc invokes child virtual+40 to perform destruction, then calls its returned deallocator if nonnull, otherwise60a4ec17; clearsparent+80 | This slot performs destruction now; it is not a side-effect-free destructor query. Preserve the native destructor/deallocator ABI and close the owned UI session before object free. |
| Parent teardown |60e26130 iterates two pointers parent+76/+80 with same destructor/free pattern then calls base60dd50d8 | Idempotent revoke of associatedUItoken; preserve stock selector/content cleanup and allocator pairing. |
| GUI exit |60e5db01 reads61fc436c; calls containerdestructor60e4ce26, thenfree60a4ec17; zeroesglobal | Exit/exception rollback revokes onlyUIownership. VolatileH/L may survive UIclose until boot/reset, but image-owned snapshots must remain independently owned. |
| Viewer teardown |60e26a7c calls60e9ec14 thenbase60df2474 and returnsa0=0 | Newdraw state must be revoked before owned storage freed; do not reorder unknown stock renderer cleanup. |

## Observed calling contracts, not a compiler ABI certification

Native factory creation returns object in a0; parent constructor60e26108 receives a0 object,d0 numericargument, and returnsa0. Rebuild60e266a9 receivesa0 parent and uses stack locals+4 factorykey,+8 publicmode; callers encode `call ...,[d2,d3,a2,a3],28`. Native event forwarders receivea0 parent,d0 event,d1 argument and forward tochildvirtual0, returningd0; wrappers have `add -4,sp`/`ret [],4`, while guarded handlers use different register-save masks and frame sizes (20/36/48etc). These per-site conventions must be implemented in real MN103 veneers and verified against compiler output/ISA. A normal C function-pointer cast is not justified. GNU's undecoded multiplication opcodes remain qualified. Portable C compilation proves only portable types/logic, not native linkability, relocation range, cache synchronization, or hook safety.

## Proposed portable flow preserving S

1. Qualified controller construction creates generation-bound UI session. At category4/5 rebuild, synchronize publicprofile and independentaxis state withcore. Values are perprofile volatileH/L, not IDs927/939/951/1655, f6ea/f6fa, selectorRAM61fc26ae or stock cursorproperties.
2. Preserve nativeUP/DOWN as categorynavigation. On focus/profile change normalize disabledH/L entries. INFO can become H/L-local single/ALL; wheel sector/value events require a qualified raw-event-to-normalized mapping before `event`. The existingS handler must never be called to implement H/L edits/reset.
3. Frame query returns copied scalar12values, axis/category, profile, and independentselection. Newlabels must identifyH/L and volatile behavior; no fake nativeH/Lcapability. Do not promise touch.
4. Close/rebuild/exit revokesUI session. Boot resetsvolatilecore neutral; user reset inH/L affects only explicitH/Lscope. Preserve stockS updates and stock0..3calls; no stocksettings writes supplied by this portable interface.
5. Existing capture snapshot/pipeline remains a separate integration contract. This UI scaffold alone cannot change pixels. Rebootreset permission removes the NVM requirement, not the snapshot/lifetime/ISP requirements.

## Exact unresolved installation boundaries

The callback loader join is documented below; real installation still requires current table/lifetime qualification. Every parent event arm must be mapped to its physical/logical wheel semantics; static forwarding/guards alone do not establish all wheel delta signs/repeat units. Six-entry allocation, MVC ownership and private H/L child destruction now have concrete candidates and targeted checks. Session/frame and native text update are joined below; actual input is joined below; COLOR gating, visual acceptance and installation/unwind remain incomplete. Native installation still depends on those seams and qualified G6 placement.

Current continuation: [UI resource origin](UI_RESOURCE_ORIGIN.md) now connects
6025bb34 to61fc3874 through the actual startup copy recipe, conditional on successful
loading and the established RAM alias interpretation. Installer still needs current
table/lifetime qualification; this finding alone does not authorize callback writes.

[MVC lifetime binding](UI_MVC_LIFETIME.md) now captures the constructed graph only
after the complete GUI041d entry has published its container, and revokes it before
GUI exit or matching parent/viewer destruction. It also corrects the +40 terminology:
the method performs destruction and returns an optional deallocator.

[Owned H/L content](UI_CONTENT_REBUILD.md) now covers four direct rebuild CALL
sites, including60e269f0, with an independently allocated56-byte child. Failed H/L
allocation retains the prior object and restores both selector and remembered
indices. [Viewer/owner joining](UI_VIEWER_JOIN.md) now binds an independent UI
session to the same published core and updates the owned native text child at
both completion points. [Input binding](UI_INPUT_BINDING.md) now copies the full
count inside a complete preprocessor/engine scope and holds both lifetimes
through actual dispatch. H/L masks stay disabled pending COLOR gating and
normalization; installation and native acceptance remain separate gates.
