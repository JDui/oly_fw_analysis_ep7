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
