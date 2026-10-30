#ifndef EP7P_DECODE_H
#define EP7P_DECODE_H
#include "ep7p.h"
/* Bounded decoder of an independently owned, stable native-layout job buffer.
 * wire_base is its 32-bit camera address; on host it is a synthetic relocation
 * base, NEVER dereferenced. Native addresses are translated only after exact
 * embedded-membership checks. Captured selector is supplied by the original
 * capture attachment: no corresponding request selector field is claimed.
 * This function establishes supported shape, NOT allocation extent/liveness,
 * task identity, native ABI, coherent concurrent observation or H/L permission.
 * out must be a real writable, non-overlapping object; input lifetime/length
 * must be truthful. No trailer bytes are read; stock-size input can decode.
 */
bool ep7p_decode(const unsigned char *job_bytes, size_t length,
                  uint32_t wire_base, uint32_t request_address,
                  unsigned captured_selector, ep7p_observation *out);
#endif
