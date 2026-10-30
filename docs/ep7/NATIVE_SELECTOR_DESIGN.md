# E-P7 native selector: an input route that does not assume Delete

Read-only exact E-P7 1.1/1100 findings and a host-only design experiment.
Nothing here adds a working H/L editor, touch target or firmware patch.

## Correction: 193 is a list ID, not proven persistent storage

Earlier notes called the parent selector's argument “property 193.” The generic
constructor/loader now establishes **list/selector ID 193**: descriptor
`0x6114efa0` has four values at `0x6114e050`, exactly **[0,1,2,3]**. A handler
record at `0x6114f330` selects initializer `0x60de150c`.

That initializer reads a remembered halfword at RAM `0x61fc26ae`, clamps it to
zero if above count-1, and stores the index at child+86. Prev/next callbacks
`0x60de1550` / `0x60de1567` invoke generic navigation and write the index back.
Several mode-change paths clear this RAM. It is not demonstrated NVRAM, free
H/L storage or an axis variable that can be safely borrowed.

Parent `0x60e266a9` already assigns all four categories:

| Existing index | Stock child construction |
| --- | --- |
| 0 | factory 0, key 111 |
| 1 | mode-key table `0x61189278`, factory 7 (COLOR/MONO editor) |
| 2 | table `0x611892b8`, factory 7 |
| 3 | factory 14, key 383 |

The parent switch and viewer both explicitly handle only 0..3. Increasing a
list count alone cannot add H/L behavior.

## Native entry and navigation evidence

GUI machine 1's event `0x9715` selects handler `0x60e4b097` in the identified
states. Argument 4 or 5 returns packed GUI state **`0x041d`** (machine 4/state 29),
whose COLOR-selector construction was already traced. Argument 4 resets the
remembered category to zero; argument 5 preserves it. GuiCaller enums `0xa1`
and `0xb7` map to `0x9715`. The concrete B7-producing app branches are now traced below; this is still not
a physical-button guarantee.

Reviewed forwarding tables map OLY UP/DOWN to GUI enums 8/11 and local
`0x9004`/`0x9006`. The parent vtable binds their navigation wrappers. The initial
callback array has a ROM-to-RAM initialization join still unqualified, so do not
claim every callback installation or physical state is fully proven.

Generic list navigation reads a per-entry halfword mask at child+88, skips
nonzero entries and bounds its loop by count. The loader allocates count*2 bytes
and initializes masks to zero. This supports a bounded conditional-category
design; it does not establish all-disabled native behavior or every native mask.

Viewer factory **`0x84`** creates a 408-byte object with draw `0x60e26ab0`.
Its category-1 branch separates MONO modes 57/58/59/65 from COLOR rendering;
COLOR draw is `0x60e27289`. No existing H/L focus, label or touch hit-box was found.
Touch hardware alone is not evidence of a usable H/L interaction.

## Candidate: preserve native categories, add COLOR-only H/L views

A more evidence-backed alternative to unqualified Delete routing is to retain
categories 0..3 and investigate additional, explicitly labeled H and L views.
UP/DOWN would continue **category navigation**, not be globally repurposed as
axis hotkeys. INFO retains single/ALL selection, and the wheels retain their
existing sector/value roles in the qualified editor context.

This requires coordinated parent-switch, viewer/label and controller-state work,
plus separate H/L value storage and image-owned snapshot transport. Existing S
property IDs and remembered category RAM must not be reused for H/L values.
New H/L categories must be disabled outside COLOR1–4, and remembered focus must
be normalized when a mode change disables its current entry. Native categories,
MONO/CRT paths, modal handling, reset behavior and exit semantics must survive.

[`ep7_selector_design.py`](../../tools/ep7_selector_design.py) tests this
**proposal only** with six synthetic entries: stock 0..3 then proposed H/L 4/5.
It tests bounded navigation, disabled focus normalization, empty/all-disabled
failure and preservation of stock order. Native category masks are unknown;
the fixture models gating of new entries, not exact native CPU behavior.
It does not load firmware, modify S, draw a camera UI or implement H/L.

## Reproduction

The expanded [GUI-machine report](../../research/ep7/gui-machine-1100.json)
checks list values, initializer, remembered-index writes, entry handler,
viewer/mask landmarks and inspected instruction windows.

```sh
python3 tools/ep7_gui_machine.py --stock /local/stock.BIN --objdump /trusted/mn103-objdump
python3 -m unittest discover -s tests -p 'test_ep7*.py'
```

Delete remains a separate routing-qualified candidate, not an assumed compatible
PEN-F shortcut. Neither this design nor its host tests is permission to flash.


## Concrete app profile-entry producers

The bridge can now be narrowed from generic app-state examples to actual profile
entry requests. A guarded branch in `0x60cd4830` writes next app state **`0x5704`**,
outgoing enum **`0xb7`** and argument **4** at `0x60cd4a1d..0x60cd4a2c`.
Another guarded branch in `0x60cf0713` writes the same app state and enum with
argument **5** at `0x60cf08e6..0x60cf08f7`. The latter is referenced by native
profile-launch touch event tables; this establishes a profile-entry route,
**not H/L touch editing**. Its switch values are not assumed public picture modes,
and a subsequent branch can replace the enum with `0xee`.

The existing GuiCaller mapping `0xb7 → 0x9715` and GUI entry handler therefore
connect these branches to reset-category argument 4 / retain-category argument 5.
One return normalizer (`0x60cf665d`, guard `0x60cd52e1`) preserves B7 on the
inspected path; its clearing condition targets enum `0xae`. Full transitive
behavior of every external helper and asynchronous delivery remains unqualified.
The alternate enum `0xa1` producer was not found and is not inferred from a
coincidentally equal property-read argument.

The selected app-state descriptor is `0x60f5e66c = (0x5704,0x60f5d06c,90)`.
State resolution and commit code connect the requested state to the event table.
Its reviewed rows include:

| OLY event | Outgoing GUI enum | Row callback |
| --- | --- | --- |
| UP `0x0100000a` | `0x08` | none |
| DOWN `0x0100000e` | `0x0b` | none |
| OK `0x0100001a` | `0x14` | `0x60cd4238` |
| Delete `0x01000026` | `0x27` | none |
| INFO `0x0100002a` | `0x25` | `0x60ceb328` |

Thus Delete's normal app forwarding leads toward the previously identified GUI
`0x9016` admission gap. INFO is not unconditional: its callback can change the
enum to `0x9d`, argument to 17 and app state to `0x5809` when its stock conditions
hold. Preserving “INFO = ALL” means preserving the native qualified editor path,
not overriding this legitimate app-level transition.

A higher-priority secondary event table can take precedence, and GUI queue
posting is not proof of observed simultaneous active states. These limitations
remain explicit rather than claiming a universal physical key route.
The [GUI bridge report](../../research/ep7/gui-bridge-1100.json) now includes the
two producer branches, state-table rows/lookup, state/argument commit and the
inspected conditional INFO override and B7-preserving normalizer.
