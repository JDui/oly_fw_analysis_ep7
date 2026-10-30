#ifndef EP7_OWNED_WORKER_JOB_H
#define EP7_OWNED_WORKER_JOB_H
#include "consumer.h"
enum { EP7J_NEUTRAL=0,EP7J_FROZEN,EP7J_ALLOCATED,EP7J_REGISTERED,EP7J_FINISHED };
/* Native32 layout is48 bytes. Host pointers may enlarge it; never serialize it.
 * Owned by one synchronous worker wrapper, never a global current-job pointer. */
typedef struct {
    uint32_t state;
    ep7p_snapshot snapshot;
    unsigned char reserved[3];
    void *allocation;
    size_t extent;
    uint64_t job;
} ep7j_scope;
/* Initialize fresh wrapper storage only after the preceding job is fully retired.
 * Descriptor is live, exclusive, genuinely312 bytes with original identity. */
void ep7j_begin(ep7j_scope *,ep7t *,unsigned char *,size_t);
/* Trusted synchronous native allocator: fresh writable requested extent, no
 * reentry. Eligible scope requests15512, records the actual result and zeros only
 * its newly requested24 bytes. Other calls retain the requested size. No free. */
typedef void *(*ep7j_allocator)(void *,unsigned);
void *ep7j_allocate(ep7j_scope *,unsigned,ep7j_allocator,void *);
/* Once, after successful conversion and before processing. The observed native
 * descriptor job must equal this scope's actual fresh allocation. Failed lock or
 * admission permanently disables registration for this invocation. */
bool ep7j_register(ep7j_scope *,ep7p *,void *observed_job);
/* Must finish before native cleanup/free. False retains the registered token and
 * requires the adapter to keep the live job/scope until a later cleanup retry.
 * Successful repeated revocation is harmless; no stock cleanup is performed. */
bool ep7j_revoke(ep7j_scope *,ep7p *);
#endif
