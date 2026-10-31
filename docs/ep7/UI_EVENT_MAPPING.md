# E-P7 COLOR logical wheel / repeat mapping (exact 1100, static only)

The useful change for the real portable UI bridge is that **packet d1 is not the
stock COLOR wheel repeat count**. A veneer accepting `(event,d1)` and treating
`abs(d1)` as repeat would lose or change native wheel steps.

## Exact dispatch join

Base dispatcher60dd5250 hash table6114040c uses key `event-0x9003`.
9032 row61140484→60dd5445→virtual+60;9031 row6114047c→60dd5467→virtual+64.
On parentvtable6118957c these slots are60e262cf and60e263a6.
Parent+64/+68 callback forwarders (expected ROM initial callbacks60e26397 and
60e2642a) pass event/argument to parent+80 child virtual0. As previously noted,
ROM→RAM initializer installation and event-associated lifetime remain qualified,
not silently proven by a ROM pointer.

COLOR child vtable61187534+60/+64 selects wrappers60e20c70/60e20ca6, which invoke
child+64/+68. All four 56-byte rows61185bdc/5c14/5c4c/5c84 explicitly install
60e21cae /60e21efb at those offsets. The same rows bind9004→60e20e0a,
9006→60e2107a,9008→60e213bb,900a→60e21852,INFO9014→60e22579.
GUI machine4/state29 event matrix admits9004/6/8/a,9031/2,9014, all to handler137
60e5da87. This is event-table admission, not physical delivery qualification.

## Actual signed repeat source

Both COLOR wheel callbacks ignore incoming d1 and call60ea3b35. That function
reads signed16 halfword61fc4fb8. Its setter60ea3b2c stores a halfword.

* 9032/60e21cae: negate/signextend the full count. Positive original count sends
  9006 once per count; negative original count sends9004 once per absolute count.
  Each synthetic child call sets d1=0. COLOR9004/6 forwarding selects the S value
  child indexed by current cursor or visits all twelve in ALL branches.
* 9031/60e21efb: same full-count source. Positive original count sends900a;
  negative original count sends9008, repeated, d1=0. COLOR9008/900a forwarding
  updates the first child (the profile cursor property), not S per-sector values.
* Zero count makes no child calls. Signed -32768 remains negative after narrowed
  negation, a pathological boundary; a bounded extension should reject it, not
  naively abs(int16_t). No claim this input occurs on the camera.

The lower generic property-list default decrease function60de55f5 uses index-1,
while its default ROM initializer6025a9e8 lists that function first; the standalone
S927 enum at604d1054 points to ascending -5..+5 halfwords. However its callback
RAM61fc2728 initialization join is not proven in this pass. Thus exact child-event
signs above are verified; labeling them numeric increase/decrease and cursor
next/previous in a new H/L child is an **explicit compatible design policy**, not
a proof of every native property's runtime override. Do not invoke S handlers to
implement H/L edits.

## Why event argument differs

60ea0e2f queries service607af9ce virtual+80 with selector3 into signed16 stacklocal.
It stores the **full value** to61fc4fb8 at60ea0e66. On status0/nonzero count branch,
it rewrites packet event9032 at60ea0e82/88 and packet+12 to only +1 or -1 at0e8d.
60ea0d39 (service selector2) and60ea0db4 (selector4) similarly store the full value
at0d70/0deb before rewriting event9031. Their packet+12 normalizes positive counts
>=2 to2, positive1 to1, negative to-1. These are logical service selector numbers,
**not established physical front/rear wheel labels**. There are other global delta
writers (60ea0070/00f7), not an ownership-exclusive global.

The shared global must be captured for the same event under a qualified GUI-task
ordering/serialization contract. A later asynchronous H/L queue must not re-read
it and associate a newer wheel delta with an old event. No such adapter is supplied
by this probe; the portable bridge can take an explicitly supplied, copied full
signed count and bound/split repeat processing without touching camera memory.

## Concrete proposed normalization for new H/L categories4/5

Only with a validated COLOR public mode (54/55/56/64), current owned UI session,
and matching category4/5:

| Raw local event | Full copied delta | Normalized portable action |
|---|---|---|
|9032|positive/negative|VALUE_INCREASE / VALUE_DECREASE, abs(count)|
|9031|positive/negative|SECTOR_NEXT / SECTOR_PREVIOUS, abs(count)|
|9014|not a repeat source|TOGGLE_ALL exactly once per admitted INFO press|
|9004,9006|irrelevant|delegate unchanged to stock category UP/DOWN|
|900c,903e|context-specific|do not map blindly; OK/hold-reset/internal commit differ|

The numeric direction labels are the stated new-child policy. Wheel zero is no-op;
-32768 rejected. If portable repeat limit64 remains, reject >64 explicitly or split
under one event/session transaction; never silently reinterpret packet d1 as full
repeat. Preserve native S category1 and stock0..3 paths unchanged. Parent gates
currently admit only0/1/3 or1/2/3: merely adding child4/5 does NOT route these wheels.
New gate arms and their native ABI/lifetime must be deliberately installed later.
No GPIO identity, touch, firmware installer, or H/L camera execution is claimed.

`tools/ep7_ui_event_mapping.py` pins stock hash before trustedobjdump; checks the
callback/vtable/dispatch/machine tables and instruction witnesses in bounded
windows. Report publishes metadata/hashes, not firmware bytes or bulk disassembly.
Scratch listings stay ignored. Tests reject wrong stock and altered operands.

## Current implementation continuation

[Input binding](UI_INPUT_BINDING.md) now captures the full local count at all five
setter CALL sites, inside a complete preprocessor/engine scope. It also qualifies
the real container return PC and holds MVC/owner across the actual raw dispatch.
The current no-SHA check adds original9031/service1 and9032/service0 to the three
recoding routes described above. INFO has its own zero-only modal gate. H/L masks
remain disabled pending COLOR gating/normalization; no hardware route is claimed.
