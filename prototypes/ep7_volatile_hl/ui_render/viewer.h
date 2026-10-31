#ifndef EP7_NATIVE_UI_RENDER_H
#define EP7_NATIVE_UI_RENDER_H
#include <stdint.h>
struct ep7m_lifetime;
struct ep7v_receipt {
    void *viewer,*child;
    uint32_t mvc_generation,session_generation,owner_generation,mode,category;
    unsigned ready;
};
/* A successful native setter receipt is not input admission or LCD acceptance. */
extern struct ep7v_receipt ep7_native_ui_receipt;
unsigned ep7v_draw_begin(void *viewer);
void ep7v_draw_end(void *viewer,unsigned held);
void ep7v_refresh(void);
/* Already held and reconciled: avoids nested holds or repeated allocation on
 * one event boundary. flags are EP7G_*; original drawing is invoked if rebuilt. */
void ep7v_refresh_held(struct ep7m_lifetime *,unsigned flags);
void ep7_gcc_ui_draw_original(void *viewer);
void ep7v_clear(void);
void ep7v_invalidate(void); /* No native calls; before changing either lifetime. */
#endif
