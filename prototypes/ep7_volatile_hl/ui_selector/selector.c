#include "selector.h"
#include "../runtime/task_context.h"
#include <stddef.h>

const uint16_t ep7s_categories[6]={0,1,2,3,4,5};
extern volatile uint32_t ep7_stock_selector_initializer_unresolved;
extern const unsigned char initializer[] __asm__("ep7_native_selector_init_bridge");
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static uint16_t half(const uint8_t *p)
{ return (uint16_t)(p[0]|((uint16_t)p[1]<<8)); }
static void put16(uint8_t *p,uint16_t n)
{ p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8); }
static void put32(uint8_t *p,uint32_t n)
{ for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }

int ep7s_expand_after_init(void *selector,uint32_t id)
{
    ep7n_task task;uint8_t *s=selector;
    if (!s||id!=193||ep7_stock_selector_initializer_unresolved!=(uint32_t)(uintptr_t)initializer||
        !ep7n_native_current_task((uint32_t)(uintptr_t)&task,&task)||
        task.domain!=0||task.entry!=UINT32_C(0x60dd5067)) return 0;
    /* Pointer/extent provenance is the just-returned initializer, not these
     * header comparisons. No reads beyond the original124-byte allocation. */
    if (word(s)!=UINT32_C(0x6114f7e4)||word(s+80)!=193||half(s+84)!=4||half(s+86)>=4||
        !word(s+88)||word(s+92)!=UINT32_C(0x6114e050)||word(s+96)!=0||
        half(s+104)!=0||half(s+106)!=3||word(s+48)!=UINT32_C(0x60de1550)||
        word(s+52)!=UINT32_C(0x60de1567)) return 0;
    uint8_t *old=(void *)(uintptr_t)word(s+88);
    uint8_t *masks=ep7_gcc_mvc_array_new(12);
    if (!masks) return 0; /* Keep the original four values, masks and focus. */
    for (unsigned i=0;i<8;i++) masks[i]=old[i];
    put16(masks+8,1);put16(masks+10,1); /* H/L unavailable until MVC/viewer admission. */
    put32(s+88,(uint32_t)(uintptr_t)masks);
    put32(s+92,(uint32_t)(uintptr_t)ep7s_categories);
    put16(s+106,5);put16(s+84,6);
    /* Same serialized construction call. Original selector destructor already
     * owns this array field and uses this exact array-delete operation. */
    ep7_gcc_mvc_array_delete(old);
    return 1;
}
