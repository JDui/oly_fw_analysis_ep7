#ifndef EP7_OWNED_QUEUE_IO_H
#define EP7_OWNED_QUEUE_IO_H
#include "wire.h"
typedef struct {
    void *ctx;
    /* Trusted binding verifies installed frame/queue group, live local task
     * domain, actual queue maximum and publication state. Size alone is NOT
     * allocation provenance. Qualification must remain valid through I/O. */
    bool (*qualify)(void *,unsigned handle,unsigned maximum);
    /* Synchronous local raw ABI vocabulary. No capacity arg exists in stock:
     * backend must copy <= the qualified maximum and retain no buffer on return.
     * Receive returns actual length or negative error; send returns native status.
     * A preserving named-send binding may map normalized timeout-2 back to-50
     * for this vocabulary; do not bypass native post-send queue notifications.
     * Do NOT substitute remote wrappers with positive255 allocation failures. */
    int (*receive)(void *,unsigned,void *,int);
    int (*send)(void *,unsigned,const void *,unsigned,int);
} ep7q_ops;
typedef struct {
    bool called;
    int raw_result; /* meaningful only when called */
    int status; /* stock wrapper vocabulary: 0 success, -2 timeout, -1 failure */
    int wire_status;
    ep7t_ticket ticket; /* receive: admitted format; send: CLEANUP ONLY, even if route changed */
} ep7q_result;
/* Every pointer/extent must name an actual live owned object, nonaliasing ops and
 * outputs. Native command is >=16, descriptor is >=312 from the expanded frame
 * group. APIs never infer extent from a tag, address, returnPC or numeric size.
 * Descriptor trailer clears before any admitted receive attempt, including error.
 * No native metadata access/free, queue configuration, or late UI read occurs. */
ep7q_result ep7q_command_receive(const ep7q_ops *,unsigned,int,
    unsigned char *command,size_t command_extent,unsigned char *descriptor,size_t descriptor_extent);
ep7q_result ep7q_descriptor_receive(const ep7q_ops *,unsigned,int,unsigned char *,size_t);
/* Consumes the owned trailer before sending a separate scratch copy; retry cannot
 * revive its ticket. Result carries original ticket for cleanup on failure or
 * legacy-only routing. Qualification/codec failure calls no native send. */
ep7q_result ep7q_descriptor_send(const ep7q_ops *,unsigned,int,unsigned char *,size_t);
#endif
