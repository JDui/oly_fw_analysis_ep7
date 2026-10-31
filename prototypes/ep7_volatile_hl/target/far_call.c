#include "far_call.h"
static uint32_t word(const volatile uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static bool bytes(const volatile uint8_t *p,const uint8_t *expected,unsigned count)
{ for(unsigned i=0;i<count;i++)if(p[i]!=expected[i])return false;return true; }
bool ep7n_far_call_present(uint32_t site_address,const volatile uint8_t site[5],
                          uint32_t veneer_address,const volatile uint8_t veneer[EP7_FAR_CALL_BYTES],
                          uint32_t target,unsigned mask,unsigned frame)
{
    static const uint8_t save[]={0xf8,0xfe,0xfc,0x42,0,0xfc,0xcc};
    static const uint8_t restore[]={0xf2,0xf2,0x58,0,0xf8,0xfe,4,0xdc};
    unsigned saves=4u*(((mask>>7)&1u)+((mask>>6)&1u)+((mask>>5)&1u)+((mask>>4)&1u));
    if(!site||!veneer||mask>240u||(mask&15u)||frame>248u||(frame&3u)||frame<saves)return false;
    if(site[0]!=0xdcu||site_address+word(site+1)!=veneer_address)return false;
    return veneer[0]==0xcdu&&veneer[1]==5u&&veneer[2]==0u&&
        veneer[3]==mask&&veneer[4]==frame&&bytes(veneer+5,save,sizeof save)&&
        word(veneer+12)==site_address+5u&&veneer[16]==0x42u&&veneer[17]==frame+4u&&
        bytes(veneer+18,restore,sizeof restore)&&veneer_address+25u+word(veneer+26)==target;
}
