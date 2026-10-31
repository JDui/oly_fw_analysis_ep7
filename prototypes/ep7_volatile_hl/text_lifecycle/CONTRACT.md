# Dedicated text lifecycle scaffold — normalized callbacks only

Self-authored portable C implementation; host callbacks are mocks. Strict C11 +
ASan/UBSan fail-fast tests pass seven allocation/init/attach/bind/present/admission
scenarios, plus duplicate creation and revoke. Leak sanitizer disabled for ptrace
host. MN10300 GCC13.4 emits assembly with -mno-setlb/-mno-liw, trusted GAS assembles
an unlinked object with no undefined symbols (all native operations are indirect
callbacks). Target NOT executed. Objects are ignored scratch, not flash payload.

`create` may return a partially initialized **new unattached** object; `initialized`
must establish readiness, not merely test pointer nonnull. Actual native factory
60d337b2 ignores initializer return. Its resource descriptor/font/layout/context
and allocation-failure qualification remain unresolved native provider obligations.
`destroy_unattached` must safely handle partially initialized and fully initialized
objects exactly once. No standalone native wrapper for this obligation established;
this scaffold does NOT bind a guessed destructor address. Existing parent bulk
cleanup or parent-list child removal is not a safe unattached-object substitute.

`attach` returns exactly1 only on ownership transfer, otherwise must leave no list
membership. Actual native60d02beb/list allocation has 0/1 status. Successful
attachment commits ownership to parent even if binding or text presentation fails.
The scaffold never manually deletes an attached child. Parent native virtual+152
lifecycle eventually owns its cleanup; `revoke` clears adapter handles BEFORE that
teardown and does not free. No stale pointer validity is inferred from this struct.

Callbacks and state are serialized/non-reentrant in qualified UI context. The
`qualified` argument expresses an EXTERNAL proved contract, not a native capability
validator. Caller supplies live owner, descriptor (at least reviewed94-byte extent
plus valid embedded references), NUL16text and callbacks. No stock category, S
property, native vtable, memory patch, renderer_ready flag, or real device changed.
No new object is ready solely because factory returned nonnull. Binding/render
failure remains distinct from already-committed H/L edit success.

## Current native factory primitive

`native_create.s` now reuses original factory60d337b2 and returns both A0 child and
D0 initializer status through `struct ep7_text_factory_result`. It saves/restores
the actual service's prior allocator selection across every normal return. The
factory's nonnull path preserves its initializer0/1 even though stock callers do
not inspect that register. A NULL child gets normalized status0. This primitive
does not yet implement all lifecycle callbacks or authorize arbitrary resources.

The original mock-only status above describes the initial scaffold. Actual fresh
rollback with context selection is now available in `../text_rollback`, but its
allocation/service ownership prerequisites still apply. Do not drop nonnull failed
factory results or treat independent result storage as a lifetime lease. Full
details: [TEXT_FACTORY_RESULT](../../../docs/ep7/TEXT_FACTORY_RESULT.md).

## Current full callback composition

`native_lifecycle.c` now implements create/initialized/destroy/attach/bind/set via
the audited native primitives and reuses the original lifecycle algorithm. For
exact owner61032f10, native text bind normally returns -1 from event6144, after
writing child+20. This adapter checks both facts instead of equating raw1 with
success. A transferred child stays parent-owned even on later failure.

Rejected fresh rollback preserves its original allocation record and returns -2
from the outer operation; it cannot be silently discarded by the void callback.
Retry and revoke have explicit ownership rules in `native_lifecycle.h`. The real
GUI entry must still supply the qualified1360-byte owner, stable service and
resource/embedded-data/ID contract before any metadata reads. No live entry or
teardown hook is installed by these C files. The current no-hash check is
`check_native.py`; native leaves/task facts are mocks, while the actual C context
and rollback implementations are included. See
[TEXT_NATIVE_LIFECYCLE](../../../docs/ep7/TEXT_NATIVE_LIFECYCLE.md).
