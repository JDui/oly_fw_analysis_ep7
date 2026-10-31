#ifndef EP7_NATIVE_FAR_CALL_H
#define EP7_NATIVE_FAR_CALL_H
#include <stdbool.h>
#include <stdint.h>
#define EP7_FAR_CALL_BYTES 30u
/* All byte spans must already denote resident executable storage owned by the
 * installation. Never follow an arbitrary target read from an untrusted JMP. */
bool ep7n_far_call_present(uint32_t site_address,const volatile uint8_t site[5],
                          uint32_t veneer_address,const volatile uint8_t veneer[EP7_FAR_CALL_BYTES],
                          uint32_t target,unsigned mask,unsigned frame);
#endif
