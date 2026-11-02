/* PEN-F's native source-owner transport, rebound to E-P7 build1100.
 * Source tuples are published to slot+912 before its native S acquisition.
 * Freeze H/L at that acquisition, then carry the same owner to its native job.
 * No compact-address registry, current-GUI lookup, lock or private queue.
 */
#include "live.h"
#include <stdbool.h>
#include <stddef.h>

extern bool ep7h_snapshot(unsigned selector,int8_t out[24]);
static int8_t live_rows[5][24];

static uintptr_t uncached(uintptr_t owner)
{
    uintptr_t region=owner&0xe0000000u;
    return region==0x60000000u || region==0xa0000000u ?
        (owner&0x1fffffffu)|0xa0000000u : 0;
}
static int8_t *row(uintptr_t owner)
{
    uintptr_t p=uncached(owner);
    if(p<0xa2731098u || p-0xa2731098u>=5u*980u ||
       (p-0xa2731098u)%980u)return NULL;
    return live_rows[(p-0xa2731098u)/980u];
}
static void copy24(int8_t *to,const int8_t *from)
{
    for(unsigned i=0;i<24;i++)to[i]=from?from[i]:0;
}
void ep7h_live_sample(uintptr_t owner)
{
    int8_t *destination=row(owner);
    if(!destination)return;
    const volatile unsigned char *p=(const volatile unsigned char *)uncached(owner);
    /* Native 6030bccc also skips S refresh for this existing-owner flag. */
    if(p[181]&0x40u)return;
    int8_t values[24]={0};
    /* These are the raw tuple's typed9481 mode and typedf6b1 COLOR selector.
     * Compact+2116/+2117 are HDR/ColorCreator and never identify this profile.
     */
    if(p[941]==11 && p[944]>=1 && p[944]<=4)
        (void)ep7h_snapshot(p[944],values);
    copy24(destination,values);
}
void ep7h_live_to_job(uintptr_t owner,uintptr_t job)
{
    if(job)copy24((int8_t *)(job+15488u),row(owner));
}
