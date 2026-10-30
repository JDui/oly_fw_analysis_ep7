#ifndef EP7_CAPTURE_PRODUCER_H
#define EP7_CAPTURE_PRODUCER_H
#include "forward.h"
enum {EP7Q_SCOPE_EMPTY=0,EP7Q_SCOPE_AVAILABLE=1,EP7Q_SCOPE_CONSUMED=2};
typedef struct {
    uint32_t capture_id;
    ep7p_snapshot snapshot;
    uint8_t state;
    unsigned char reserved[2];
} ep7q_capture_scope;
_Static_assert(sizeof(ep7q_capture_scope)==32,"native producer owns32 bytes for frozen scope");
_Static_assert(offsetof(ep7q_capture_scope,state)==29,"native scope state offset");
typedef struct {ep7t *transport;ep7q_forward_ops forward;} ep7q_producer_ops;
/* Trusted caller supplies an ALREADY frozen capture-bound value after sidecar
 * ownership/exclusion checks. This does not qualify node pointers/current UI.
 * Fresh scope is caller-owned and cannot be concurrently reused or reset. */
void ep7q_capture_scope_init(ep7q_capture_scope *,uint32_t,const ep7p_snapshot *);
/* Each available scope has one publication attempt, including failed admission.
 * Publishes the ticket before native enqueue; immediate consumers may run there.
 * Returns normalized local raw result, or delegate256 when no raw call occurred.
 * No native metadata is dereferenced or freed. Callback owns failed cleanup. */
int ep7q_producer_send(const ep7q_producer_ops *,ep7q_capture_scope *,unsigned,int,
                       const unsigned char *command,size_t extent);
#endif
