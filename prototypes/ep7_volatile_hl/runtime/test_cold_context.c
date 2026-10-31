#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include "cold_cohort.c"
const unsigned char cold_clear[]={0},receive_gate[]={0},send_gate[]={0},delete_gate[]={0},capture_init[]={0},bootstrap[]={0};
static const uint32_t pages[]={0x60041000,0x621a6000,0x8ff00000,0x62001000};
static unsigned char before[sizeof pages/sizeof pages[0]][4096];
static unsigned positives,negatives;
static void put32(uint32_t address,uint32_t value){memcpy((void *)(uintptr_t)address,&value,4);}
static void put16(uint32_t address,uint16_t value){memcpy((void *)(uintptr_t)address,&value,2);}
static void check(uint32_t tcb,bool expected)
{
    for(unsigned i=0;i<sizeof pages/sizeof pages[0];i++)memcpy(before[i],(void *)(uintptr_t)pages[i],4096);
    assert(ep7r_native_cold_context(tcb)==expected);
    for(unsigned i=0;i<sizeof pages/sizeof pages[0];i++)assert(!memcmp(before[i],(void *)(uintptr_t)pages[i],4096));
    if(expected)positives++;else negatives++;
}
int main(void)
{
    const uint32_t tcb=0x62001000;
    for(unsigned i=0;i<sizeof pages/sizeof pages[0];i++){
        void *p=(void *)(uintptr_t)pages[i];
        assert(mmap(p,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==p);
    }
    put32(0x8ff00004,0x600411a4);put32(0x60041204,0x621a630c);put32(0x621a630c,tcb);
    put32(0x600411c0,0x621a631c);put32(0x600412ec,0x621a63b0);
    put32(0x600412b4,0x60073215);put32(0x600412b8,0x60073218);
    put32(0x600412bc,0x6007321b);put32(0x600412e0,0x600300a1);put32(0x60041300,0x800);
    put16(tcb+16,0x2d);put16(tcb+48,1);
    check(tcb,true);
    /* A disabled task exception can retain pending bits; admission must not
     * clear them or call the handler to make the condition look quiescent. */
    put32(tcb+56,0x1234);put32(tcb+52,0xdead0000);check(tcb,true);
    put16(tcb+48,0);check(tcb,false);put16(tcb+48,1);
    /* A stale current-task observation and an unexpected root are rejected
     * without following an unmapped alternative pointer. */
    check(0x62003000,false);
    put32(0x8ff00004,0x61000000);check(tcb,false);put32(0x8ff00004,0x600411a4);
    put16(tcb+16,0x2e);check(tcb,false);put16(tcb+16,0x2d);
    put16(0x621a631c,1);check(tcb,false);
    put16(0x621a631c,0x100);check(tcb,false);put16(0x621a631c,0);
    put32(0x621a63b0,1);check(tcb,false);put32(0x621a63b0,0);
    /* Modified callback/mask/restart semantics invalidate the static model. */
    put32(0x600412b4,0xdead0000);check(tcb,false);put32(0x600412b4,0x60073215);
    put32(0x600412b8,0xdead0000);check(tcb,false);put32(0x600412b8,0x60073218);
    put32(0x600412e0,0xdead0000);check(tcb,false);put32(0x600412e0,0x600300a1);
    put32(0x60041300,0xf00);check(tcb,false);put32(0x60041300,0x800);
    put32(0x60041308,1);check(tcb,false);put32(0x60041308,0);
    check(tcb,true);
    printf("{\"positive_observations\":%u,\"rejected_contexts\":%u,\"all_observations_read_only\":true,\"synthetic_pages_executable\":false}\n",positives,negatives);
    return 0;
}
