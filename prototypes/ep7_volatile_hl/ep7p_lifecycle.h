#ifndef EP7_LIFECYCLE_H
#define EP7_LIFECYCLE_H
#include "ep7p_direct.h"
/* Self-authored HOST integration vocabulary, not a native ABI binding. */
typedef struct { void *base; size_t extent; bool fresh_extent_proven; } ep7l_allocation;
typedef bool (*ep7l_reader)(void *,uintptr_t request,unsigned char *,size_t);
typedef struct {
    void *ctx;
    /* Trusted constructor wrapper: actual allocator provenance, not geometry or
       trailer magic. Failure may still leave partial descriptor needing cleanup. */
    int (*construct)(void *,void *descriptor,ep7l_allocation *);
    int (*convert)(void *,void *descriptor);
    /* Must return normally only when no reader callback/context is retained.
       Lifetime/completion of native descriptor remains adapter responsibility. */
    int (*process)(void *,void *descriptor,ep7l_reader,void *reader_context);
    void (*cleanup)(void *,void *descriptor);
} ep7l_ops;
typedef struct {
    int native_status;
    bool invoked, registered, cleaned, quarantined;
    unsigned readers, applied;
    uint64_t pending_job;
} ep7l_result;
/* Caller owns descriptor, snapshot; initialized core required (no task lease on this path).
   Snapshot must already be capture-bound, not taken from current UI here.
   No C nonlocal exits/cancellation, callback reentry, or concurrent reuse allowed.
   If quarantined, retain descriptor/allocation; retry cleanup before reuse/free. */
ep7l_result ep7l_run(ep7p *,const ep7l_ops *,void *,const ep7p_snapshot *);
bool ep7l_retry_cleanup(ep7p *,const ep7l_ops *,void *,ep7l_result *);
#endif
