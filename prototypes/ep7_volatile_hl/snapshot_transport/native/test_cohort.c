/* Synthetic installed bytes only; no firmware fixture or instruction execution. */
#define _GNU_SOURCE
#include "../../target/far_call_fixture.h"
#include <stdio.h>
#include <sys/mman.h>
/* Keep the production data lists, function and branches in this one fixture. */
#include "cohort.c"
unsigned char ep7_pipeline_far_calls[8*EP7_FAR_CALL_BYTES];
__asm__(".globl ep7_pipeline_far_calls_end\n.set ep7_pipeline_far_calls_end,ep7_pipeline_far_calls+240");
const unsigned char ep7_native_capture_scope_bridge[1]={1};
const unsigned char ep7_native_producer_send_bridge[1]={2};
const unsigned char ep7_native_materializer_receive_bridge[1]={3};
const unsigned char ep7_native_descriptor_receive_bridge[1]={4};
const unsigned char ep7_native_descriptor_send_bridge[1]={5};
const unsigned char ep7_native_worker_scope_bridge[1]={6};
const unsigned char ep7_native_worker_allocate_bridge[1]={7};
const unsigned char ep7_native_worker_process_bridge[1]={8};
const unsigned char ep7_native_worker_cleanup_bridge[1]={9};
const unsigned char ep7_native_ack_bridge[1]={10};
int main(void)
{
    const uint32_t pages[]={0x6003b000,0x602ac000,0x60353000,0x603df000,
                           0x603e0000,0x603ef000,0x603f2000};
    for(unsigned i=0;i<sizeof pages/sizeof pages[0];i++)
        assert(mmap((void *)(uintptr_t)pages[i],4096,PROT_READ|PROT_WRITE,
            MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)(uintptr_t)pages[i]);
    assert(!ep7q_native_cohort_present());
    unsigned short_index=0;
    for(unsigned i=0;i<sizeof calls/sizeof calls[0];i++){
        const struct call_site *s=&calls[i];uint8_t *p=(uint8_t *)(uintptr_t)s->pc;
        if(s->width==2)ep7_far_fixture(p,ep7_pipeline_far_calls+30*short_index++,s->target,s->mask,s->frame);
        else{
            assert((uintptr_t)s->target<=UINT32_MAX);
            p[0]=0xdd;ep7_far_fixture_word(p+1,(uint32_t)(uintptr_t)s->target-s->pc);
            p[5]=s->mask;p[6]=s->frame;
        }
    }
    for(unsigned i=0;i<sizeof frames/sizeof frames[0];i++){
        uint8_t *p=(uint8_t *)(uintptr_t)frames[i].pc;uint16_t v=(uint16_t)frames[i].adjustment;
        p[0]=0xfa;p[1]=0xfe;p[2]=(uint8_t)v;p[3]=(uint8_t)(v>>8);
    }
    for(unsigned i=0;i<sizeof words/sizeof words[0];i++)
        ep7_far_fixture_word((uint8_t *)(uintptr_t)words[i].address,words[i].value);
    assert(ep7q_native_cohort_present());
    unsigned rejected=0;
    for(unsigned i=0;i<sizeof calls/sizeof calls[0];i++){
        volatile uint8_t *p=(volatile uint8_t *)(uintptr_t)calls[i].pc;
        p[1]^=1;assert(!ep7q_native_cohort_present());p[1]^=1;rejected++;
    }
    for(unsigned i=0;i<8;i++){
        unsigned off=i*30+12;ep7_pipeline_far_calls[off]^=1;
        assert(!ep7q_native_cohort_present());ep7_pipeline_far_calls[off]^=1;rejected++;
    }
    for(unsigned i=0;i<sizeof frames/sizeof frames[0];i++){
        volatile uint8_t *p=(volatile uint8_t *)(uintptr_t)frames[i].pc;
        p[2]^=1;assert(!ep7q_native_cohort_present());p[2]^=1;rejected++;
    }
    for(unsigned i=0;i<sizeof words/sizeof words[0];i++){
        volatile uint8_t *p=(volatile uint8_t *)(uintptr_t)words[i].address;
        p[0]^=1;assert(!ep7q_native_cohort_present());p[0]^=1;rejected++;
    }
    assert(ep7q_native_cohort_present());
    for(unsigned i=0;i<sizeof pages/sizeof pages[0];i++)
        assert(munmap((void *)(uintptr_t)pages[i],4096)==0);
    printf("{\"synthetic_complete_group_accepted\":true,\"missing_or_corrupt_items_rejected\":%u}\n",rejected);
    return 0;
}
