# Minimal H/L native text payload — compile-only candidate

## Concrete native text path

Display helper60e850f8 type5 table entry611b1614 points60e85186. This branch takes a NUL-terminated16-bit string atdatarecord+8 and widgetpair[1], then calls **60d4c9df** at60e8528b with native `CALL[d2,d3,a2,a3],24`, a0=validtextwidget,a1=string. This is a UI text storage setter, NOT a stockS property setter. A direct adapter can use this narrower interface without invoking type5's later theme/global handling.

Setter details:
- Widget+156 is its owned dynamic string pointer. Inputwidget must already be a live correctly initialized instance; setter does not validate a null/malformedwidget.
- Null source→0. Existing equal source→1 without allocation/invalidation.
- Changed source: free oldstring via60d109db; count16-bit units throughNUL via60d178a8; allocate2*(length+1) via60d109d1; storepointer, zeroallocation, copy2*length bytes, update/invalidatewidget; return1. Allocation failure returns0 with oldstring alreadyreleased. **Failure is destructive, not transactional rollback.**
- Source is synchronously deep-copied, so a small stackstring need remain valid only untilreturn. It must be bounded and NUL-terminated before the call; native lengthhelper has no caller-supplied bound. UIwidget and native allocator/renderingcontext must stay valid and serialized.
- Constructor60d4be0e initializes+156=0; vtable60faec7c slot0 is destructor60d4be64, freeing+156 atbe82 beforebasecleanup. Vtable+0x238 pointspaint60d4c434. Paint preferentially reads+156 (resourceID+130 fallback onlywhen absent), then passesitsstring to native textdrawing60d075a7 atc61e under its visibility/styleguards. This proves the owned string reaches rendering, not that H/L widget/layout/font selection is implemented.

No±5 numeric icon table is involved: short ordinaryASCII-subset UTF16 `H 01 +7` / `L 12 -7` can be supplied without inventing native numeric glyph IDs. Actualfont glyphcoverage, clipping, contrast, layout andvisibility remain device/resource qualification issues; no claim of successfulon-camera rendering.

## Implemented portable payload

`text.c` validates copiedframe COLOR publicmode54/55/56/64, category4/5, sector0..11 or255, and all12valueswithin-7..7. It emits:
- selectedsector: `H 01 +0` through `L 12 -7` (user-facingsector1..12);
- ALL withuniformvalues: `H ALL +7`;
- ALL withnonuniformvalues: `H ALL MIX`, deliberatelynot reporting onebandvalue as ifall equal.

Allstringsfit10 uint16 units includingNUL. Failure leaves destinationunchanged. Inputisstablecopiedframe, not a livecontroller lookup. `ep7_text_present` validates/formatsonstack and calls the bridge; it doesnot createoradmitwidgets, invokeSsetters, touchframebuffer, or setrenderer_ready. The caller must independentlyown a dedicatedH/L textwidget and a liveviewer/session. Do not repurposea stockS textslot withoutseparate lifecycle/layout work.

## GCC→native callable veneer

`set_text.s`: GCCargd0=widget,d1=string → nativea0/a1. Reserves12bytes belowentrySP=S, uses exactnativeCALL[d2,d3,a2,a3],24, and returnswithRET[],12. OriginalGCC returnat[S] is preserved; nativeCALLreturnatS-12 isseparate. Nativecallee saves/restoresd2,d3,a2,a3 atS-16/S-20/S-24/S-28 and owns24-byteframe (deepestS-36). MDR/flags/volatile registers are notpromisedpreserved. No nakedtailjump, no arbitrarymidfunctionhook. Originaltextsetter deliberatelyunresolved; objectisneverlinked/executed.

`check.py` pins fiveinstructions,17-byte.text, exactPCREL32 relocation and nativeframe; includes5negativevalidationmutations, hostarithmeticframemodel, targetGCC13.4 `-mno-setlb -mno-liw` compile, strictC11+ASan/UBSanhosttests. Testscoverbothaxes,all12sectors,values-7..7,uniform/mixedALL,capacity/canary/no-writefailure,invalidmode/category/value/sector/nullandnativefailurepropagation. Hostnativefunction is a stubcopy, not firmwareexecution. LSan disabledforptraceenvironment; nohostallocationperformed.

Static probe `tools/ep7_text_widget.py` (from repository root), report `research/ep7/text-widget-1100.json` and 8 tests pin148instructions/8windows plus type5/vtable entries. Novendorfont/bitmapdump is redistributed.

## Remaining renderer_ready gate

Need a correctlycreated/styled/positionedH/L textwidget, explicitcategory4/5viewer branch and parentfactory integration, matchingliveownership, synchronizedcopiedframe and UIpublication/cleanup contract. Do not setrenderer_ready merelybecause textformatterorbridge compiles. ExistingstockS categoriesremainfullydelegated. This candidate supplies actualminimalvalue/labelpayload and a provennativecopyinginterface, not aninstalledUI or flash-ready image.

## Edit outcome and display outcome are separate

The H/L edit may already be committed successfully before a later viewer callback calls `ep7_text_present`. A text-allocation failure is a **display failure**, not rejection or rollback of that edit; the old native string may already be gone. Do not feed setter0 back into `ep7_gcc_ui_route` as a retrospective edit rejection, retry the edit, or delegate the already-committed event to stock. Keep the original edit result and report/handle drawing failure separately (e.g. a qualified later redraw of the current frame, without applying the edit again). `renderer_ready` means the native interface/resources/lifetime were qualified; it is not a guarantee that every allocation or render succeeds. Current APIs intentionally keep routing/edit and presentation results separate.
