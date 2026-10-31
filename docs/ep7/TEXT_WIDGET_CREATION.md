# Minimal dedicated native text widget: bounded creation/lifetime evidence

Read-only E-P7 1.1 exact-stock research; no native calls executed, no installation,
no existing S widget stolen. Addresses refer to decoded main base 60020020.

## Concrete creation, not an inferred spare object

Generic factory inner entry `60d337b2` takes d0=type, d1=owner/context,
a1=resource descriptor. Table row `60fa8e84` is `(0x8010,60d33b02)`.
Branch `60d33b02` requests **180 bytes** via `60cfe5a0`, calls constructor
`60d4be0e` at `60d33b11`, installs allocator context bytes at object+28/+29
through `60cfe586`, and calls initializer `60d4bfee` at `60d33b31`.
Factory returns object in a0 (common exit `60d37b4b`), but **does not check
initializer d0**. A nonnull factory result is not proof initialization succeeded.
Factory CALL contract at actual site: `[d2,a2,a3],24`; not a GCC function.
Allocator uses current UI service allocator context, not arbitrary libc malloc.

Concrete display-container class constructor `60d7ab3f` sets vtable `61032f10`.
Its child-building method `60d7abf6` reads descriptor table `61fb7070`, creates
indices 1..57 with factory call `60d7ac2a`, adjusts child rectangle through
virtual+44, attaches to owner's list via `60d02beb` at `60d7acbf`, records child
at `(owner+792)[index]`, then calls child virtual+148 at `60d7acd5`.
This is a reference lifecycle, not authorization to add an out-of-bounds index58.

`60d02beb` calls owner virtual+440, then list insertion
`60d023d2 -> 60d02314 -> 60cfef7b`. It allocates a **12-byte list node**, stores
child pointer at node+8, returns 0 on allocation failure, 1 on success. Native
reference callsite ignores this status. A new adapter must not assume ownership
transferred when insertion fails or leak a created-but-unattached object.

For text vtable `60faec7c`, +148=`60d0487a`, which invokes
`60cfe0f8 -> virtual124=60cfdfe0`: stores parent a1 at child+20. It additionally
performs visibility/layout/event callbacks; this is not merely assigning a pointer.

## Actual owner teardown chain

Container vtable+152=`60d43d4b`; at `60d43dc9` it calls `60d02bbd`.
That invokes owner virtual+432=`60d42d69`, whose `60d42dc3` calls
`60d02c03` (inner entry of bulk child teardown). For each list child it selects
allocator context through child vtable+248/UI service vtable+244, invokes child vtable+368, child vtable+152,
child virtual0 destructor, then **calls the deallocator returned in a0** with
the original child pointer (`60d02ca1..60d02caa`). It finally clears list nodes.
Text destructor `60d4be64` frees its copied text at+156, calls base cleanup,
returns `60cfe5c9` deallocator. Text +152=`60d048d0` handles detach/cleanup.

Only afterwards the container destructor path `60d7ab79 -> 60d42c67 ->
60d0297c` clears list/base storage. **Calling the container destructor alone
is not equivalent to its virtual+152 lifecycle teardown.** Dedicated child
must not be independently freed while still registered in this list.

## Descriptor size, copies, and unresolved resource selection

Base `60d04928 -> 60cfdff1` reads descriptor type+0, ID+2, layout pointer+4,
flags+8, opaque value/pointer+12 (stored verbatim at object+24), and halfword+16.
If layout pointer nonnull, UI-service virtual+696 provides count, +692 current
index; it allocates/copies count*8 layout bytes and selects indexed rectangle.
Null layout pointer skips this allocation; it does not establish a useful visible
rectangle. Caller must qualify count/index, descriptor subobjects and UI context.

Derived `60d4bfee` reads descriptor through byte93:
- +20 resource-string ID -> widget+130;
- +24..47 text style -> widget+132..155;
- +48 font selector -> widget+128;
- +50,+52,+56,+60,+62 -> widget+172,+166,+168,+174,+164;
- +68..83 -> widget+88..103;
- +84..91 -> widget+68..75 via two-word copy `60d3ca8a`;
- +92 halfword -> widget+176.

Thus **94 readable bytes is the reviewed initializer minimum**, not a certified
resource-format size or permission to use an all-zero descriptor. The descriptor
address itself is not retained in this reviewed chain, but opaque embedded fields
are copied verbatim; no claim they are all scalars or safe stack-lifetime pointers.
A caller-supplied qualified descriptor can use this factory; actual compatible
font/style/rectangle values and embedded-pointer lifetimes remain to be qualified.
ASCII H/L/ALL/MIX glyph availability is not proved merely by using UTF16.

## Bounded table-origin check

`61fb7070` is outside decoded main (main ends 6191ffe0). Exact literal scan of
all bytes found only consumer immediate at `60d7ac1d`; the neighboring
61fb7070..61fb7157 range likewise has only that literal. This does NOT prove no
writer: a startup relocation/resource loader may initialize a larger region.
Reviewed early startup copy `60020117..60020137` copies 6002e020..6002e8e8 to
61b20fe0..61b218a8 and **does not cover** this resource table. Nearby initializer
`60d7aaba` writes different RAM pointers61fb6fb8/6fbc/6fc0, not this table.
No static join to a concrete table descriptor was established in this bounded pass.

## Minimal integration boundary / stop

Creation is demonstrably feasible via a native existing factory, not blocked by
absence of a text class. Remaining installation gates: qualified descriptor/font/
layout + live owning container/UI serialization; allocation/init failure handling;
checked list ownership transfer and teardown ordering; adapter invalidation before
native child release. A later GCC veneer can expose factory calls, but compiling
that veneer alone cannot establish these gates. renderer_ready stays false absent
them. Existing text setter copies transient UTF16, but its allocation failure can
remove old text; display failure must not roll back/replay an already committed H/L
edit. None of this changes S properties or proves a rendered camera image.


## Reproduction and portable scaffold

`tools/ep7_text_creation.py` and `tests/test_ep7_text_creation.py` reproduce the read-only stock evidence; report `research/ep7/text-creation-1100.json`.
`prototypes/ep7_volatile_hl/text_lifecycle/` contains normalized callback sequencing and mock host tests, not native bindings. Run its `check.py` for temporary host/target compile checks.

Current continuation: [UI resource origin](UI_RESOURCE_ORIGIN.md) joins the actual
startup data-copy recipe to the RAM resource table and identifies four existing
type8010 descriptors, font1 and two rectangles per descriptor. It retains the
RAM-alias/cache and later-table-mutation limits; opaque embedded fields and actual
glyph/rendering behavior are not yet fully qualified.
