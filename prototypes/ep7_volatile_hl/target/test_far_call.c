#include "far_call.h"
#include <assert.h>
#include <string.h>
static void put32(uint8_t *p,uint32_t n)
{ for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(n>>(8*i)); }
int main(void)
{
    const uint32_t pc=0x60289c5e,base=0x60048080,target=0x60049000;
    uint8_t site[5]={0xdc},veneer[30]={0xcd,5,0,0xf0,32,0xf8,0xfe,0xfc,
        0x42,0,0xfc,0xcc,0,0,0,0,0x42,36,0xf2,0xf2,0x58,0,0xf8,0xfe,4,0xdc};
    put32(site+1,base-pc);put32(veneer+12,pc+5);put32(veneer+26,target-base-25);
    assert(ep7n_far_call_present(pc,site,base,veneer,target,0xf0,32));
    /* Six distinct admission failures: unrelated JMP, RA, MDR, ABI, destination,
     * and unsupported extended state. Values are synthetic, not native addresses. */
    site[1]^=1;assert(!ep7n_far_call_present(pc,site,base,veneer,target,0xf0,32));site[1]^=1;
    veneer[12]^=1;assert(!ep7n_far_call_present(pc,site,base,veneer,target,0xf0,32));veneer[12]^=1;
    veneer[19]=0xf6;assert(!ep7n_far_call_present(pc,site,base,veneer,target,0xf0,32));veneer[19]=0xf2;
    assert(!ep7n_far_call_present(pc,site,base,veneer,target,0xf0,28));
    assert(!ep7n_far_call_present(pc,site,base,veneer,target+4,0xf0,32));
    assert(!ep7n_far_call_present(pc,site,base,veneer,target,0xf1,32));
    return 0;
}
