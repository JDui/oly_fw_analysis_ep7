#ifndef EP7_OWNED_QUEUE_CONSUMER_H
#define EP7_OWNED_QUEUE_CONSUMER_H
#include "wire.h"
/* Caller proves a live exclusive owned >=312-byte descriptor, with its original
 * metadata identity retained at +48. Parameters name distinct nonaliasing objects.
 * Neither size nor marker establishes native allocation/lifetime provenance.
 * First attempt marks the local trailer consumed BEFORE the registry lock, even
 * if the route is unsupported. Failed claim stays neutral; output is unchanged.
 * No UI sampling, current-address lookup, native free or job registration occurs. */
bool ep7q_claim_owned(ep7t *,unsigned char *,size_t,ep7p_snapshot *);
/* For ACK, drain, rejected routing or cancellation. Mark consumed first, then
 * retire the full key. False requires retaining this descriptor and its cleanup
 * obligation: do not ACK/free/reuse it. A lock failure retains E7C1 and serial.
 * True clears the trailer; absent tickets and repeated successful cleanup are
 * complete. A copied snapshot remains valid independently of this retirement. */
bool ep7q_retire_owned(ep7t *,unsigned char *,size_t);
#endif
