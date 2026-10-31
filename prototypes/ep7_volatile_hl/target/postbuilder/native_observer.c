/* Self-authored TARGET-ONLY adapter for the reviewed E-P7 native setup seam.
 * Never execute on host or treat arbitrary integers as validated pointers.
 * Caller guarantees setup is readable for >=16 bytes and stable through return;
 * its output pointer denotes >=976 writable bytes with the native output
 * lifetime. Request/output/registered job cannot be freed or mutated by stock
 * code concurrently. Direct registry revoke-before-free uses the same corelock.
 * This translation does not establish those native preconditions or install hooks.
 */
#include "runtime/runtime.h"
_Static_assert(sizeof(uintptr_t)==4, "adapter requires 32-bit target pointers");
_Static_assert(sizeof(void *)==4, "adapter is not a host pointer decoder");
/* Published runtime slot shares worker core/lock/registry. This is never a
 * last-job pointer or task-ID shortcut. Installation still owns native lifetime. */
static uint32_t load_le32(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 |
           (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
void ep7_gcc_postbuilder_observer(const unsigned char *setup)
{
    uintptr_t request;
    unsigned char *output;
    if (!setup) return; /* Null guard only, not a readable-extent proof. */
    request=(uintptr_t)load_le32(setup+4);
    output=(unsigned char *)(uintptr_t)load_le32(setup+12);
    (void)ep7r_apply(&ep7_native_runtime_slot,request,output,EP7P_OUTPUT);
}
