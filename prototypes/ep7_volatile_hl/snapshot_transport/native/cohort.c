#include "cohort.h"
#include "../../target/far_call.h"
extern const unsigned char far_calls[] __asm__("ep7_pipeline_far_calls");
extern const unsigned char far_calls_end[] __asm__("ep7_pipeline_far_calls_end");
extern const unsigned char capture[] __asm__("ep7_native_capture_scope_bridge");
extern const unsigned char producer[] __asm__("ep7_native_producer_send_bridge");
extern const unsigned char materializer[] __asm__("ep7_native_materializer_receive_bridge");
extern const unsigned char receive[] __asm__("ep7_native_descriptor_receive_bridge");
extern const unsigned char send[] __asm__("ep7_native_descriptor_send_bridge");
extern const unsigned char worker[] __asm__("ep7_native_worker_scope_bridge");
extern const unsigned char allocate[] __asm__("ep7_native_worker_allocate_bridge");
extern const unsigned char process[] __asm__("ep7_native_worker_process_bridge");
extern const unsigned char cleanup[] __asm__("ep7_native_worker_cleanup_bridge");
extern const unsigned char ack[] __asm__("ep7_native_ack_bridge");
struct call_site {uint32_t pc;const unsigned char *target;uint8_t width,mask,frame;};
static const struct call_site calls[]={
    {0x602ac3de,capture,2,0xb0,32},{0x602ac869,producer,4,0xc0,48},
    {0x603dfc9b,materializer,4,0xf0,44},
    {0x603ef8b5,receive,2,0xf0,44},{0x603ef8d2,receive,2,0xf0,44},
    {0x603ef8fd,receive,2,0xf0,44},{0x603ef91a,receive,2,0xf0,44},
    {0x603dfa04,receive,4,0xf0,44},{0x603dfaa1,send,4,0xe0,36},
    {0x603f2722,worker,2,0x30,56},{0x603537f3,allocate,4,0,4},
    {0x603f2890,process,4,0xb0,24},{0x603f28c0,cleanup,4,0x30,24},
    {0x603dfc67,ack,2,0x30,32},{0x603e05c6,ack,2,0x30,32},
    {0x603f2769,ack,4,0x30,32}};
struct frame_site {uint32_t pc;int16_t adjustment;};
static const struct frame_site frames[]={
    {0x603df805,-332},{0x603df933,332},{0x603ef894,-324},
    {0x603ef94c,-316},{0x603ef9b4,316},{0x603f26a3,-316},
    {0x603f2792,316},{0x603e0546,-324},{0x603e05e2,324}};
struct word_site {uint32_t address,value;};
static const struct word_site words[]={
    {0x6003b424,312},{0x6003b428,10112},
    {0x6003bb90,312},{0x6003bb94,10112},
    {0x6003b460,312},{0x6003b464,10112}};
static uint32_t read_word(const volatile uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
bool ep7q_native_cohort_present(void)
{
    unsigned short_index=0;
    if((uintptr_t)far_calls_end-(uintptr_t)far_calls!=8u*EP7_FAR_CALL_BYTES)return false;
    for(unsigned i=0;i<sizeof calls/sizeof calls[0];i++){
        const struct call_site *s=&calls[i];
        const volatile uint8_t *p=(const volatile uint8_t *)(uintptr_t)s->pc;
        if(s->width==2){
            if(short_index>=8u)return false;
            const uint8_t *veneer=far_calls+EP7_FAR_CALL_BYTES*short_index++;
            if(!ep7n_far_call_present(s->pc,p,(uint32_t)(uintptr_t)veneer,veneer,
                                      (uint32_t)(uintptr_t)s->target,s->mask,s->frame))return false;
        }else if(p[0]!=0xdd||p[5]!=s->mask||p[6]!=s->frame||
                  s->pc+read_word(p+1)!=(uint32_t)(uintptr_t)s->target)return false;
    }
    for(unsigned i=0;i<sizeof frames/sizeof frames[0];i++){
        const volatile uint8_t *p=(const volatile uint8_t *)(uintptr_t)frames[i].pc;
        uint16_t value=(uint16_t)frames[i].adjustment;
        if(p[0]!=0xfa||p[1]!=0xfe||p[2]!=(uint8_t)value||p[3]!=(uint8_t)(value>>8))return false;
    }
    for(unsigned i=0;i<sizeof words/sizeof words[0];i++)
        if(read_word((const volatile uint8_t *)(uintptr_t)words[i].address)!=words[i].value)return false;
    return short_index==8u;
}
