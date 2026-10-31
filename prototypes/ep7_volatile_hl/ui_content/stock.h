#ifndef EP7_NATIVE_UI_STOCK_RESTORE_H
#define EP7_NATIVE_UI_STOCK_RESTORE_H
#include "content.h"
int ep7c_stock_supported(unsigned category,uint32_t mode);
/* H/L -> stock only. Construct using exact original creators before disposing
 * the owned H/L child. Allocation failure retains the old graph and focus. */
int ep7c_to_stock_held(struct ep7m_lifetime *,unsigned category,uint32_t mode);
void *ep7_gcc_mvc_stock_create(unsigned category,const uint32_t args[2]);
void ep7_gcc_mvc_stock_selected(void *parent);
void ep7_gcc_mvc_transition_timers(void);
void ep7c_stop_transition(struct ep7m_lifetime *);
#endif
