#ifndef EP7_SNAPSHOT_WIRE_H
#define EP7_SNAPSHOT_WIRE_H
#include "transport.h"
#define EP7W_COMMAND 16u
#define EP7W_DESCRIPTOR 300u
#define EP7W_TRAILER 12u
#define EP7W_MAX (EP7W_DESCRIPTOR+EP7W_TRAILER)
enum { EP7W_REJECT=-1, EP7W_LEGACY=0, EP7W_TAGGED=1 };
/* All pointers refer to live distinct nonaliasing objects. Prefix must be exactly
 * COMMAND or DESCRIPTOR. This codec operates ONLY on owned buffers; native stock
 * metadata/descriptors are not enlarged. It supplies no allocator/queue hook.
 * The native prefix is copied byte-for-byte. A zero ticket sends the old length.
 * A nonzero ticket must match the prefix metadata and supported kind19 route.
 * Encode failure leaves wire and *written unchanged (no partial publication). */
bool ep7w_encode(unsigned prefix,const unsigned char *native,ep7t_ticket,
                 unsigned char *wire,size_t capacity,size_t *written);
/* actual MUST be the byte count from a qualified receive, not its requested cap.
 * Clear ticket on EVERY call, including rejection, preventing stale carry-over.
 * Bad lengths/capacity reject before native output writes. Exact legacy length,
 * malformed trailer, unsupported route or zero serial produce a neutral ticket.
 * Well-formed ticket is NOT ownership proof: final consumer must ep7t_claim it.
 * Caller must not fall back to current metadata-address lookup or UI sampling. */
int ep7w_decode(unsigned prefix,const unsigned char *wire,size_t actual,
                unsigned char *native,size_t capacity,ep7t_ticket *);
#endif
