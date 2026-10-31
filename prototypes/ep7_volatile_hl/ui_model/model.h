#ifndef EP7_NATIVE_UI_MODEL_H
#define EP7_NATIVE_UI_MODEL_H
#include "../ep7p_ui.h"
#include "../runtime/runtime.h"
#include "../ui_mvc/lifetime.h"
/* Permanent GUI-only state. Slot0 has its own monotonic serial: H/L can close
 * and reopen within one MVC generation, so the MVC token alone is insufficient. */
struct ep7cm_model {
    ep7r *runtime;
    ep7p_ui ui;
    struct ep7_ui_session session;
    uint32_t serial;
};
extern struct ep7cm_model ep7_native_ui_model;
/* Caller holds the actual recorded MVC graph through every native/core call.
 * Reads property111 via the native service; never accepts a caller's mode flag. */
int ep7cm_frame_held(struct ep7m_lifetime *,struct ep7_ui_frame *);
void ep7cm_revoke(void); /* GUI scope; no native callbacks, core reset or image mutation. */
uint32_t ep7_gcc_ui_public_mode(void);
#endif
