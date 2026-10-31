#ifndef EP7_NATIVE_ACK_H
#define EP7_NATIVE_ACK_H
#include "stack.h"
#include "../consumer.h"
enum { EP7Q_ACK_NORMAL=1,EP7Q_ACK_DRAIN,EP7Q_ACK_WORKER };
typedef struct { uint32_t descriptor;unsigned origin; } ep7q_ack_args;
bool ep7q_ack_layout(const ep7q_stack *,uint32_t wrapper_sp,uint32_t actual_descriptor,ep7q_ack_args *);
typedef struct {
    ep7q_stack stack;
    ep7t *transport;
    void *wait_context;
    /* Safe ordinary-task progress only, no ACK/free/reuse/reentry; retains the
     * full descriptor. A failed poll holds no core lock across this callback. */
    void (*wait_retirement)(void *);
} ep7q_ack_context;
/* Provider must remain available for every owned tagged descriptor until ACK or
 * explicit retirement. The full installer/task group proves owned storage and
 * original metadata identity at+48. It must not downgrade lost owned context to
 * unknown stock. runtime/contexts.c binds timed progress and terminal retention;
 * native exception behavior and installation remain unqualified. */
bool ep7q_ack_context_unresolved(uint32_t,ep7q_ack_context *);
void ep7q_ack_entry(uint32_t descriptor,uint32_t wrapper_sp);
#endif
