#ifndef EP7_NATIVE_UI_GATE_H
#define EP7_NATIVE_UI_GATE_H
#include "../ui_mvc/lifetime.h"
struct ep7g_state { uint32_t generation,last_stock;unsigned available; };
extern struct ep7g_state ep7_native_ui_gate;
enum { EP7G_AVAILABLE=1,EP7G_REBUILT=2 };
/* Held, actual graph only. Re-evaluates real mode/runtime/cohorts/owner; no
 * caller-supplied readiness. Never modifies stock masks. May normalize H/L. */
unsigned ep7g_reconcile_held(struct ep7m_lifetime *,uint32_t *mode);
/* Serial GUI boundary before any parent event, including stock navigation. */
int ep7g_before_event(void *parent); /* Returns previous category, or -1 if unowned. */
#endif
