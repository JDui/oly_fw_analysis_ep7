# Narrow capture admission: E-P7 1100

This continues the [inline-job design](STORAGE_AND_INLINE_JOB_DESIGN.md).
It identifies conditional native stage and request paths, **not a runtime
admission hook, expanded allocation, firmware patch or demonstrated capture**.

## Dynamic stage table, not one fixed ROM list

The constructor clears 16 × 12-byte stage records at job+10984 and initializes
the count at job+11314, then calls `60354709` at `60353c70`. The ordinary
family reaches `603666c7` → `60368e97` under these conditions:

- job+26 is 0 or 4;
- job+31 is zero;
- job+12 is 0 or 2;
- job+16 bit `0x80000` is clear.

The ordinary core stage list is `[603687d4, 603687ed, 6036884d]` if:

- job+29 is zero;
- neither special predicate admits job+11341 in `{0,1,2,3,8}` together with
  job+30==1 or job+33==1;
- job+25 is not 2.

Other branches select different stage lists. A later initializer may append
`60356116`, so **three is not a guaranteed final stage count**. The supported
candidate is the ordinary core's zero-based index 2 and callback `6036884d`.

For the reviewed `603e6d04` producer, dispatch `0x100d` initially gives job+26=0.
Some other fields start zero in its cleared input header. The job+30 predicate
is derived from capture+24799==1 and descriptor+298!=3. These are initialization
facts, not guarantees that intervening helpers cannot change fields. Admission
must examine the actual supported state, not infer it from a UI mode name.

## One stage can submit several different operations

`6036884d` calls `60366f21` at `603688bc`. It can acquire a borrowed resource
into job+13252, which may select the native generic-owner path instead of COLOR.
The request wrapper at `60366f79` forms the embedded request, but an optional
stage callback can mutate it at `60366f90`.

Direct binder sites in this routine:

| Binder call | Request argument | Initial research admission |
| --- | --- | --- |
| `60367646`, `60367717`, `60367f56` | `a1=0`, explicit embedded arm | Further type/mode/owner checks required |
| `6036780f`, `6036793e` | external argument candidates | Reject in an embedded-only design |

The tail call `603680d9` → `60366d52` invokes `60355439` → `60355343`, clearing
712 bytes of the **same** embedded request and setting request+16 to **type 3**.
Its later binder is not proof that the earlier type-0 COLOR request is submitted.

Also, binder `60354bb0` can overwrite request+17 at `60354c27`: job+16 bit
`0x10000`, job+4682 and job+28 determine conditional values 1 or 2. Thus the
producer's initial request+17=0 is not a submission invariant. Together with
the previously verified request+12=`0xf005` stage override, this prevents
blindly deriving a hardware slot from initial request fields.

## Bounded design qualification, not a global proof shortcut

A future synchronous reader could admit a deliberately narrow case based on
an independently retained **fresh constructor invocation**, descriptor+36
matching that job, the qualified stage/index, an embedded reciprocal operation
shape, actual type 0 / native COLOR mode 11 / owner 0, and the CPU builder's
existing predicates. Optional stage mutation callbacks can be excluded initially.

This is a proposed proof structure, not a native facility already discovered.
A scoped context must reject nested/concurrent mismatches, old allocations,
errors/unwinds and late calls **before** any trailer read. A global “last job”
pointer is insufficient. A matching stage, callback or address does not prove
allocation extent. The model cannot read a nonexistent trailer magic to
establish its own permission.

It is unnecessary to prove all allocators and hardware paths merely to admit
one independently qualified synchronous invocation. It is still necessary to
prove the selected invocation's allocation/initialization, task/nesting identity,
lifetime and immutable capture snapshot. These obligations remain open.

## Captured raw selector is 1-based on the accepted COLOR rows

The public property-111 getter `602b0b43` uses composite descriptor `604ccd10`
and member list `6043090e`. It collects raw properties **111, 908 and 973**
into a zeroed 64-byte tuple, not just raw mode 111. Matching table `604ba8fc`
has 33 rows; rows 13–16 at `604bac3c` onward are:

| Raw mode | Raw COLOR selector | Raw MONO selector | Public COLOR mode |
| --- | --- | --- | --- |
| 11 | 1 | 0 | 54 |
| 11 | 2 | 0 | 55 |
| 11 | 3 | 0 | 56 |
| 11 | 4 | 0 | 64 |

The remaining tuple words are zero. The parallel public table is `604addc8`.
The capture population's raw mode and COLOR selector at offsets 24053 and
24083 therefore must **not** be interpreted as mode 54 and zero-based 0–3.
The existing full composite getter also compares the raw MONO selector;
those two captured fields alone do not reproduce every invalid-composite case.

The format-6 matcher compares the first 32 rows and returns index 32 when
unmatched; the range guard accepts 32<33 and the public table maps it to
**63**, not COLOR1 or a neutral H/L state. The host binding helper intentionally
rejects unsupported raw mode/selector pairs instead of copying that fallback.
It remains only a conditional field-to-profile binding, not a coherence check
or a reproduction of all full-getter semantics.

There is a real schema distinction left open: standalone property 908's list
at `604cc0cc` is `[0,1,2,3]`, and the `f6b1` ROM default is zero, while the
accepted composite COLOR rows use **1,2,3,4**. Do not silently clamp selector 4
to 3 or call zero COLOR1. The public composite writer/validation path and
runtime defaults need separate qualification; a ROM default is not current
camera state.

[Raw-profile report](../../research/ep7/s-capture-profile-1100.json) checks the
complete accepted rows, public table, fallback, descriptors and 10 helper
windows / 298 instruction witnesses. Snapshot consistency and task/lifetime
admission remain separate requirements.

## Reproduce

```sh
python tools/ep7_stage_admission.py --stock /local/stock.BIN --objdump /trusted/mn10300-objdump
python tools/ep7_s_capture_profile.py --stock /local/stock.BIN --objdump /trusted/mn10300-objdump
PYTHONPATH=tools python -m unittest discover -s tests -p 'test_ep7*.py'
```

The [report](../../research/ep7/stage-admission-1100.json) checks 21 windows,
143 instruction/operand witnesses and the stage-2 callback literal. No camera,
firmware execution, generated install image or bulk disassembly is involved.
