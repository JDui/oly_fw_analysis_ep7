#ifndef EP7_DIRECT_H
#define EP7_DIRECT_H
#include "ep7p.h"
/* TRUSTED OBSERVER boundary, not public untrusted pointer validation.
 * Invoke synchronously only at the qualified exact native post-builder seam.
 * Caller guarantees request/config/output live through return, no simultaneous
 * stock request mutation, no retained/queued invocation, and no stale request
 * across cleanup/address reuse. Output is a real writable buffer of len bytes,
 * not runtime state. Registry revocation MUST precede free under same core lock.
 * Request itself is treated as an integer until matched to a registered job.
 * No task identity/current GUI is consulted. These preconditions are not proven
 * by a caller boolean or by this C interface. No native installer is provided.
 */
bool ep7p_direct_apply(ep7p *,uintptr_t request,unsigned char *output,size_t len);
#endif
