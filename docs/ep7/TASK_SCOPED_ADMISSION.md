# Task-scoped CPU admission: evidence and design limits

This continues [capture admission](CAPTURE_ADMISSION.md). **No native H/L
admission hook, TLS allocation or camera execution is implemented.**

## Current-task query independently found in E-P7

The exact E-P7 1100 image contains `get_tid returned Error` at `6136c1d3`
(newline/NUL terminated). Its caller `612c78ec` passes stack+8 to **`600317ac`**,
checks the returned status, and on success reads the output halfword. This is
E-P7-specific evidence, not a transplanted PEN-F address.

The API has the observed shape `status = get_tid(uint16_t *out)`:

1. Word `8050` selects an entry in pointer table `8ff00004`; it is used as a
   per-core/context selector here, **not** returned as the task ID.
2. Context flags through per-core+28 reject when byte 0 is nonzero or byte 1
   equals 1. The rejected path returns **-25 without writing the output**.
3. The admitted path follows per-core+96, dereferences it, reads the halfword
   at +16, writes through the caller's `a0`, and returns zero.

Exact interrupt/dispatch-disabled flag semantics and all privileged calling
conditions remain unqualified. A proposed guard must reject any nonzero result;
it must not use stale output or bypass the context checks with direct structure
reads.

The named caller indexes its own 20-byte records using that ID. This is **not**
evidence that those records are general TLS or available to an HSL extension.
No free TLS slot, task-destruction hook or ready-made nesting stack was identified
in this bounded search.

## What this closes—and what it does not

A task-keyed scoped context is now a concrete design candidate, instead of
mistaking a core number or global “last job” pointer for task ownership.
The actual expanded-allocation provenance must still originate from the
qualified constructor invocation; neither task ID nor request shape proves it.

A correct design must specify:

- task-query failure and unsupported-context rejection;
- bounded capacity and overflow behavior;
- nesting push/pop and identity checks at the synchronous CPU reader;
- constructor failure, normal exit, error/unwind and late-call revocation;
- concurrent publication/access and task termination/ID reuse;
- immutable H/L snapshot bound to the captured profile and no asynchronous
  pointer escape; cross-axis atomic S/H/L edit time is a separate stronger
  contract, not assumed from the native sequential S reads.

A numeric task ID is **not a generation token**. Any external registry that
survives task destruction must prevent an old entry from qualifying a new task
with the same ID. A simulated ticket or host context manager cannot establish
that the firmware supplies those guarantees.

## Host-only scoped contract

[`ep7_scoped_admission_design.py`](../../tools/ep7_scoped_admission_design.py)
composes the earlier inline-job allocation fixture. It requires two independent
**assumed** identities: an allocation ticket and a task-instance token distinct
from the numeric 16-bit task ID. Neither is discovered or implemented in firmware.

Each task instance has a nested scope stack. Only the matching live top scope
can delegate to the guarded allocation reader; current type 0 / raw mode 11 /
owner 0 / no mutation callback are rechecked before any simulated trailer read.
Other tasks, nested mismatches, stale scope/allocation tickets, task-ID reuse and
unsupported stage/shape are rejected. Explicit task revocation invalidates all
its scopes; it does not release the separately owned job allocation.

Manual exits require LIFO. Context-manager cleanup revokes its frame and any
unclosed descendants, preserving the original exception; inconsistent bookkeeping
revokes the task's scopes. Regression tests specifically cover an unclosed manual
nested scope during exception unwinding, so cleanup cannot leave a late reader
silently admitted. Dead scope/task records are reclaimed.

Model-only configurable budgets default to **16 tasks / depth 8** and reject
overflow before adding state. These numbers are not observed native capacities.
All interleavings are single-threaded host tests, **not concurrency tests or
proof of native task-exit/stack unwinding**. H/L output remains a scalar stand-in,
not actual coefficient mathematics or a camera result.

## Reproduce

```sh
python tools/ep7_task_identity.py --stock /local/stock.BIN --objdump /trusted/mn10300-objdump
PYTHONPATH=tools python -m unittest discover -s tests -p 'test_ep7*.py'
```

The [report](../../research/ep7/task-identity-1100.json) validates the named
string and 31 instruction witnesses in two windows. It invokes only the trusted
host disassembler, never the firmware's task API.
