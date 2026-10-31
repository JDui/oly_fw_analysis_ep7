#include "cold_bootstrap.h"
#include <stdint.h>
extern const unsigned char cold_clear[] __asm__("ep7_native_cold_clear");
extern const unsigned char receive_gate[] __asm__("ep7_native_queue_receive_gate");
extern const unsigned char send_gate[] __asm__("ep7_native_queue_send_gate");
extern const unsigned char delete_gate[] __asm__("ep7_native_queue_delete_observer");
extern const unsigned char capture_init[] __asm__("ep7_native_capture_initialize");
extern const unsigned char bootstrap[] __asm__("ep7_native_cold_bootstrap_bridge");
struct inline_site { uint32_t address; const unsigned char *target; unsigned bytes; };
static const struct inline_site sites[]={
    {0x600201fe,cold_clear,6},
    {0x60036d3c,receive_gate,10},
    {0x60036f93,send_gate,6},
    {0x60031072,delete_gate,6},
    {0x602897d7,capture_init,6},
};
static uint32_t word(uint32_t address)
{ return *(const volatile uint32_t *)(uintptr_t)address; }
static uint32_t displacement(const volatile unsigned char *p)
{ return (uint32_t)p[1]|((uint32_t)p[2]<<8)|((uint32_t)p[3]<<16)|((uint32_t)p[4]<<24); }
bool ep7r_native_early_cohort_present(void)
{
    /* First four ordinary sections have returned from their local initializer.
     * Flags are necessary ordering observations, never data integrity evidence. */
    if((word(0xa272e420u)&15u)!=15u || (word(0xa272e41cu)&15u)!=15u)return false;
    if(*(const volatile uint16_t *)(uintptr_t)0x62234fc0u!=0)return false;
    for(unsigned i=0;i<sizeof sites/sizeof sites[0];i++){
        const struct inline_site *s=&sites[i];
        const volatile unsigned char *p=(const volatile unsigned char *)(uintptr_t)s->address;
        if(p[0]!=0xdc || s->address+displacement(p)!=(uint32_t)(uintptr_t)s->target)return false;
        for(unsigned j=5;j<s->bytes;j++)if(p[j]!=0xcbu)return false; /* Complete overwritten span, NOP suffix. */
    }
    const volatile unsigned char *p=(const volatile unsigned char *)(uintptr_t)0x60191371u;
    if(p[0]!=0xdd || p[5] || p[6]!=4u ||
       0x60191371u+displacement(p)!=(uint32_t)(uintptr_t)bootstrap)return false;
    /* Both original domain2 big-pool bounds must shrink32->31 at cold load.
     * Observing them now is not proof that no earlier allocator used the slot. */
    const volatile unsigned char *alloc=(const volatile unsigned char *)(uintptr_t)0x600229b9u;
    const volatile unsigned char *free_bound=(const volatile unsigned char *)(uintptr_t)0x60022c28u;
    return alloc[0]==0x80u && alloc[1]==31u && free_bound[0]==0x8fu && free_bound[1]==31u;
}
