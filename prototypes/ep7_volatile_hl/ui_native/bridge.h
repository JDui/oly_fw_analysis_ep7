#ifndef EP7_UI_NATIVE_BRIDGE_H
#define EP7_UI_NATIVE_BRIDGE_H
#include "ep7p_ui_raw.h"
/* Five 32-bit words copied by the native wrapper; parent is a native wire
 * address, never dereferenced by this portable router. packet_parameter is NOT
 * the complete wheel delta. */
struct ep7_native_ui_input { uint32_t event, packet_parameter, parent,caller_pc,container; };
/* The provider now performs admission AND dispatch inside one MVC/owner hold.
 * No mutable UI/session pointer escapes an admission callback. */
#define EP7_NATIVE_CALL_STOCK 256u /* INTERNAL wrapper action, never native status. */
uint32_t ep7_gcc_ui_route(const struct ep7_native_ui_input *);
#endif
