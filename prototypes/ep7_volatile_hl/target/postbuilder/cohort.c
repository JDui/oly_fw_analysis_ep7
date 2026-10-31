#include "cohort.h"
#include "../far_call.h"
extern const unsigned char far_calls[] __asm__("ep7_postbuilder_far_calls");
extern const unsigned char far_calls_end[] __asm__("ep7_postbuilder_far_calls_end");
extern const unsigned char bridge[] __asm__("ep7_native_postbuilder_bridge");
bool ep7n_postbuilder_cohort_present(void)
{
    const uint32_t pc=UINT32_C(0x603b02d9);
    return (uintptr_t)far_calls_end-(uintptr_t)far_calls==EP7_FAR_CALL_BYTES&&
        ep7n_far_call_present(pc,(const volatile uint8_t *)(uintptr_t)pc,
            (uint32_t)(uintptr_t)far_calls,far_calls,(uint32_t)(uintptr_t)bridge,0xf0,96);
}
