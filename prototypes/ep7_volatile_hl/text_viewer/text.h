#ifndef EP7_MINIMAL_TEXT_VIEWER_H
#define EP7_MINIMAL_TEXT_VIEWER_H
#include "ep7_ui_adapter_contract.h"
/* ASCII subset encoded as UTF-16 code units. No font/glyph availability claim. */
#define EP7_TEXT_UNITS 10u
/* Returns length excluding NUL, or0 without changing destination on failure.
 * Caller supplies a stable copied frame; this is not a frame/session admission. */
size_t ep7_text_format(const struct ep7_ui_frame *,uint16_t *,size_t);
/* Unlinked GCC->native veneer. Caller independently owns a valid dedicated
 * textwidget of the audited class, UI thread/lifetime and rendering context.
 * Native setter copies the string before returning; failure can erase old text. */
int ep7_gcc_set_text_unresolved_binding(void *,const uint16_t *);
/* No allocation, framebuffer, property/S writes or renderer_ready manipulation
 * in this portable adapter. Native widget admission must precede invocation. */
int ep7_text_present(void *,const struct ep7_ui_frame *);
#endif
