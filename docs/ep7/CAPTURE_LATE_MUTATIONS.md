# Later capture mutation: narrow H/L relevance, not whole-structure immutability

Exact E-P7 1.1 input is the previously pinned SHA256 9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb. Read-only disassembly; no native execution.

## Observed identity selection

602a9647 receives context a0, ID-context a1, selected-node pointer d0. At 9664..9678 it chooses node[0] if context+2348 != 0 or context+1696 == 5; otherwise ID-context[0]. It resolves that ID through 6029b9d1 and holds the resulting capture in a3 (967f). This is an identity *selection*, not a demonstrated allocation/replacement of an image. The two ID sources must not be assumed equal. An H/L capability should match the actual resolved allocation/image generation.

## What the reviewed writes do and do not establish

The direct 602a9647..602a9a5b function writes time/exposure/derived metadata fields and small arrays. No direct store to raw mode +24053 or COLOR selector +24083 was identified. Examples: 968d/9698 write +24160/+24168; 96b1..96c8 +3770..3776; later copies target +27018 (31 halfwords) and +1972 (32 bytes). Dynamic arrays start +24236/+24380; this is not a proof about arbitrary corrupt counts. No direct allocation or capture registry replacement was found in this body.

The passed-capture helper 603b664d→603b665b writes the +5214 region and +5573 flag list in the reviewed body through 603b679e. 602a9f16 writes +14404/+14406/+14408 and +27178. Neither reviewed helper directly changes the two profile bytes.

The other passed-capture helper 60300068→603017f3 is large (returns 60303215). It explicitly reads rawmode +24053 at 603018df/18e7 and selector +24083 at 6030195c/1960 and 6030198e/1992. Destination a2 was set to capture+3180 at 603018d6: stores 60301988/19ba write translated output there, NOT back to selector. Both selector branches handle 1,2,3,4 (default falls back to first output). Later code includes writes to +24098 (e.g. 60302e3f, 60302eac), which is distinct from selector +24083. The direct body does not exhibit a literal-address write to +24053/+24083. Its many helper calls have NOT all been transitively proven unable to mutate an aliased capture; this is a bounded classification, not exhaustive write-set proof.

## Design correction / supersession

Earlier notes treating any write anywhere in the 27332-byte capture as an H/L epoch invalidation were overly conservative. H/L is an immutable image-associated snapshot, while stock S and derived metadata retain native behavior. There is no demonstrated reason to invalidate H/L merely because the above time/derived metadata fields change. Bind H/L to allocation generation + image/population generation + captured raw profile; track re-population, retirement, or verified profile changes, not arbitrary unrelated field writes.

A clone may carry the same image's immutable H/L snapshot despite unrelated metadata updates. Native validity/lifetime during its original memcpy remains a caller precondition; sidecar epochs do not pin memory or repair stock UAF. Early-published clones stay neutral until explicit capability qualification, and missing/mismatched capabilities must never be filled later from current UI values. This does not claim identical-time S/H/L sampling or global atomicity.

The remaining qualification is precise capability transport to the kind19 metadata/descriptor/job, including queued-copy/address-reuse behavior, not a new requirement to freeze every capture byte.


## Reproducible scope

`tools/ep7_kind19_lifetime.py` checks254 instruction witnesses in8 windows plus
the event44 handler row. [Actual result](../../research/ep7/kind19-lifetime-1100.json).
This pins the cited reads/returns and bounded ownership edges; it does not prove
all transitive writes, every queued copy lifetime or native installation safety.
