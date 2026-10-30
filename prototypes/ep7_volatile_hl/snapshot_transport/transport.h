#ifndef EP7_SNAPSHOT_TRANSPORT_H
#define EP7_SNAPSHOT_TRANSPORT_H
#include "ep7p.h"
#define EP7T_CAP 8u /* prototype bound, not native queue capacity */
typedef struct { uintptr_t metadata; uint64_t serial; } ep7t_ticket;
typedef struct {
    ep7t_ticket ticket;
    unsigned state;
    ep7p_snapshot snapshot;
} ep7t_entry;
typedef struct {
    ep7p_ops ops;
    bool initialized;
    uint64_t serial;
    ep7t_entry entries[EP7T_CAP];
} ep7t;
/* Fresh zeroed distinct storage, once before publication; never reset live state.
 * Reuses the existing poll-only lock vocabulary; current() is not used.
 * Lock/unlock must provide exclusion/visibility and must not reenter. Caller
 * supplies live, distinct nonaliasing C objects for all pointer parameters.
 * Metadata is only an opaque identity label: no native memory is accessed.
 * Tickets MUST travel with each owned message/descriptor, never reconstructed
 * by looking up a raw address. Native transport of the ticket is NOT supplied.
 */
bool ep7t_init(ep7t *,ep7p_ops);
bool ep7t_prepare(ep7t *,uintptr_t metadata,const ep7p_snapshot *,ep7t_ticket *);
/* Before native publication, to permit an immediate consumer. Failure must keep
 * the descriptor neutral. A second publish cannot renew an existing ticket. */
bool ep7t_publish(ep7t *,ep7t_ticket);
/* At most one consumer gets an owned copy. Early claim burns the ticket. On any
 * failure output is unchanged; caller must permanently neutralize that local
 * descriptor attempt, including lock failure, without retry or late UI reads. */
bool ep7t_claim(ep7t *,ep7t_ticket,ep7p_snapshot *);
/* Explicit cancellation/ACK cleanup. No native free or inferred completion.
 * Failed lock leaves the slot intact; caller retains cleanup obligation.
 * Successful retirement allows the address to be registered with a NEW serial;
 * old queued tickets remain invalid, even when both slot and address are reused.
 * Already claimed copies are independent values, not revoked by this call. */
bool ep7t_retire(ep7t *,ep7t_ticket);
/* Teardown/abort of the admitted pipeline: clear all outstanding records while
 * preserving serial, initialization and lock binding. No native frees, reset of
 * sequence, or revocation of already copied snapshots. Idempotent on success.
 * Lock failure leaves records intact and the invalidation obligation pending.
 * Native teardown ordering and producer shutdown are adapter responsibilities. */
bool ep7t_invalidate_all(ep7t *);
#endif
