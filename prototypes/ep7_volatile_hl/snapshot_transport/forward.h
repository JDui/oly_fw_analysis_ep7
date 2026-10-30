#ifndef EP7_FORWARD_OWNED_H
#define EP7_FORWARD_OWNED_H
#include "owned_io.h"
enum {EP7Q_DELEGATE_SEND=256};
typedef struct {
    ep7q_ops queue;
    void *retirement_context;
    /* Takes ownership of this VALUE on return, including a failed poll-lock
     * retirement. Must retain any unresolved obligation until retirement or
     * qualified pipeline invalidation; cannot retain a descriptor pointer. */
    void (*retire_owned)(void *,ep7t_ticket);
} ep7q_forward_ops;
/* Sends using owned scratch and consumes the source trailer. Preserves native
 * normalized status if raw was called. If no raw call occurred, returns internal
 * delegate256 for original300-byte send; caller must restore its native ABI.
 * No expanded send is allowed without a retirement owner for failure/legacy. */
int ep7q_forward_send(const ep7q_forward_ops *,unsigned,int,unsigned char *,size_t);
#endif
