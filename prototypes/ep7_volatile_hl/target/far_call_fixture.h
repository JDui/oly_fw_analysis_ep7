#ifndef EP7_FAR_CALL_FIXTURE_H
#define EP7_FAR_CALL_FIXTURE_H
/* Host-only byte fixture. These bytes are never executed or installed. */
#include "far_call.h"
#include <assert.h>
static inline void ep7_far_fixture_word(volatile uint8_t *p,uint32_t value)
{ for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(value>>(8*i)); }
static inline void ep7_far_fixture(volatile uint8_t *site,volatile uint8_t *veneer,
                                   const void *target,unsigned mask,unsigned frame)
{
    const uint8_t shape[30]={0xcd,5,0,0,0,0xf8,0xfe,0xfc,0x42,0,0xfc,0xcc,
        0,0,0,0,0x42,0,0xf2,0xf2,0x58,0,0xf8,0xfe,4,0xdc,0,0,0,0};
    assert((uintptr_t)site<=UINT32_MAX&&(uintptr_t)veneer<=UINT32_MAX&&(uintptr_t)target<=UINT32_MAX);
    for(unsigned i=0;i<30;i++)veneer[i]=shape[i];
    veneer[3]=(uint8_t)mask;veneer[4]=(uint8_t)frame;veneer[17]=(uint8_t)(frame+4);
    ep7_far_fixture_word(veneer+12,(uint32_t)(uintptr_t)site+5u);
    ep7_far_fixture_word(veneer+26,(uint32_t)(uintptr_t)target-(uint32_t)(uintptr_t)veneer-25u);
    site[0]=0xdc;
    ep7_far_fixture_word(site+1,(uint32_t)(uintptr_t)veneer-(uint32_t)(uintptr_t)site);
}
#endif
