#ifndef EP7_TEXT_NATIVE_CONTEXT_H
#define EP7_TEXT_NATIVE_CONTEXT_H
#include "rollback.h"

/* Invoke only inside a live, serialized GUI operation. The initialized service
 * and its allocator selection must remain exclusive through the whole call;
 * current-task and vtable checks below are not a lifetime lease or a mutex.
 * qualify retains rollback.h's exact fresh-object provenance contract and must
 * not reenter, publish, change allocator selection or invalidate the service.
 * Its independent context stays alive through native destruction. */
int ep7_text_rollback_native(void *object,
    int (*qualify)(void *,const void *,size_t),void *context);

/* GCC interfaces to three audited native leaves. Only valid service instances
 * may be passed. A packed selection is byte28 | (byte29 << 8), never a pointer.
 * Exchange/select have no failure branch; serialization is a caller contract. */
void *ep7_gcc_ui_service(void);
uint16_t ep7_gcc_ui_context_exchange(void *,uint16_t);
void ep7_gcc_ui_context_select(void *,uint16_t);
#endif
