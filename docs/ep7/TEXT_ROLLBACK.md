# Fresh text rollback: narrower than arbitrary text destruction

Read-only exact E-P7 1.1. This analysis does not approve installation or execute
native cleanup. Checkpoint of independently reviewed bounded rollback analysis; not a native installation.

## Why destructor + returned deallocator alone is insufficient

`60d4be64` frees owned string+156 using saved allocator bytes+28/+29, then calls
`60d04844 -> 60cfd791`. The latter is only `mov60cfe5c9,a0; retf`, not cleanup.
Successful base resource initialization `60cfdff1` may allocate a layout copy
at+64 (allocation60cfe05b, store60cfe066). Direct destructor/deallocator would
leak it. `60cfe109` (reached by virtual+152) frees+56/+60 and+64; +64 free is
60cfe1f7 and null store60cfe1ff. A failed layout allocation instead storesNULL,
returns0, and derived initializer60d4bfee exits before copying remaining fields.

Returned deallocator `60cfe5c9` uses **current UI-service allocator context** via
service virtual+248, then60d109db; it does not select the widget's saved bytes.
Native bulk cleanup selects context first: child vtable+248 gets object28/29
(`60cfe58f`), service vtable+244 selects it. A rollback must preserve this context
sequence and UI serialization, not just cast a0 to a libc free function.

## Parent-null hazards in ordinary virtual+152

Text vtable+152=`60d048d0` is not universally safe for never-parented resources.
1. widget byte+88 !=0 invokes vtable+492=`60d04cc4`. It gets parent via+128 and
   dereferences parent vtable+484 at60d04cf4..cfa without a null guard.
2. widget byte+68==1 (virtual+452=`60d04c16`) similarly gets parent and calls
   parent+476 at60d048fc..4903 without a null guard.
These fields come from descriptor+68 and+84 respectively. Thus generic factory
resource acceptance does not prove this rollback safe.

A **bounded fresh resource subset** can require descriptor byte68=0 and byte84=0,
not an all-zero descriptor. Their copied widget bytes then suppress both unsafe
branches. The descriptor still requires qualified font/style/rectangle and other
embedded fields. Failed base initializer leaves these bytes constructor-zero.

## Fresh construction and cleanup sequence under that subset

Base constructor60cfd747 zeros parent+20, +56,+60,+64 (d754..78a), while
60d0480b zeros+68..87 and+88..127. Text constructor60d4be0e zeros+156,+160 and
other text state. No parent binding occurs until the explicit later virtual+148.
Initializer's final visibility callback has explicit null-parent guard at60d4c07f.
For a newly created object never published, bound, rendered, text-set or otherwise
mutated, observed constructors/initializers do not register a timer or publish the
object. This is a bounded call-chain statement, not universal absence of observers.

With byte68=0/byte88=0 and parentNULL, virtual+152:
- skips both parent-dependent branches above;
- calls60cfe109: frees optional owned buffers, compares/clears current UI pointer
  references (+584/+736/+724/+732 getters and corresponding setters), frees+64,
  and removes queued entries matching object via60d102f1;
- forwards event6145 through60d04b66, which explicitly returns-1 if parentNULL
  (60d04b7a..80), rather than dereferencing parent;
- calls60d11280 to clear matching timer table entries under native synchronization.
Exact text vtable+368=`60cfeafe` is a bare return, so it contributes no cleanup.
Then text destructor and its returned deallocator can follow the observed native
sequence, provided allocator context remains selected and object identity/lifetime
is valid. Calling virtual+152 is not equivalent to manually freeing just+64.

## Proposed explicit admission, still not installed

A provider may qualify: exact text class/full180 allocation; completed constructor;
factory initialization outcome known; new/unattached/unpublished object; parent+20
NULL; object+68=0 and+88=0; saved allocator bytes installed; serialized live native
UI service with matching selected allocator context; no reentrant publication or
external use. Rollback order: select saved context -> native text+152 cleanup ->
text destructor -> returned deallocator. This closes the simple leak and parent-null
hazards for that subset, not for arbitrary resources/objects.

The portable lifecycle callback remains unbound until this contract and exact ABI
are independently reviewed. Its init-failure handling cannot infer success merely
from native factory nonnull. No renderer_ready or flash-ready assertion follows.


## Reproduction

Read-only probe `tools/ep7_text_rollback.py`, tests `tests/test_ep7_text_rollback.py`, and report `research/ep7/text-rollback-1100.json`.
Compile-only adapter and callback qualification contract: `prototypes/ep7_volatile_hl/text_rollback/`; run `check.py`. Report: `research/ep7/text-rollback-host-target.json`.
The independent ops table/context/saved-token lifetimes, nonmutation/nonreentrancy, and serialized prior-context restoration are mandatory assumptions detailed in its CONTRACT.md. Native context provider remains unbound in this checkpoint.
