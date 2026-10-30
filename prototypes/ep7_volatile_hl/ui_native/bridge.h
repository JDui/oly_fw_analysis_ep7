#ifndef EP7_UI_NATIVE_BRIDGE_H
#define EP7_UI_NATIVE_BRIDGE_H
#include "ep7p_ui_raw.h"
/* Three 32-bit words copied by the native wrapper; parent is a native wire
 * address, never dereferenced by this portable router. packet_parameter is NOT
 * the complete wheel delta. */
struct ep7_native_ui_input { uint32_t event, packet_parameter, parent; };
struct ep7_ui_admission {
    ep7p_ui *ui;
    struct ep7_ui_session session;
    int32_t synchronized_full_delta;
};
/* Unresolved native binding. STOCK=0 means known stock/unowned parent or
 * category0..3: no H/L mutation. OWNED=1 requires exact active parent/session,
 * COLOR category4/5, matching installed H/L viewer, serialized stable input,
 * and copied event-associated delta. REJECT=2 means swallow, never stock S.
 * Admission owns serialization through the router call; it must not acquire a
 * lock then silently release it while returning mutable UI/session state. */
enum ep7_native_admission { EP7_NATIVE_STOCK=0, EP7_NATIVE_OWNED=1, EP7_NATIVE_REJECT=2 };
int ep7_ui_native_admit_unresolved(const struct ep7_native_ui_input *, struct ep7_ui_admission *);
#define EP7_NATIVE_CALL_STOCK 256u /* INTERNAL wrapper action, never native status. */
uint32_t ep7_gcc_ui_route(const struct ep7_native_ui_input *);
#endif
