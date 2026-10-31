#include "input.h"
extern volatile unsigned char ep7_stock_ui_preprocess_call_unresolved[];
extern volatile unsigned char ep7_stock_ui_dispatch_call_unresolved[];
extern volatile unsigned char ep7_stock_ui_wheel_1_call_unresolved[];
extern volatile unsigned char ep7_stock_ui_wheel_0_call_unresolved[];
extern volatile unsigned char ep7_stock_ui_wheel_2_call_unresolved[];
extern volatile unsigned char ep7_stock_ui_wheel_4_call_unresolved[];
extern volatile unsigned char ep7_stock_ui_wheel_3_call_unresolved[];
extern volatile uint32_t ep7_stock_mvc_parent_vtable_unresolved[];
extern const unsigned char prep[] __asm__("ep7_native_ui_preprocess_bridge");
extern const unsigned char dispatch[] __asm__("ep7_native_ui_dispatch_bridge");
extern const unsigned char sample[] __asm__("ep7_native_ui_wheel_sample_bridge");
extern const unsigned char parent[] __asm__("ep7_native_ui_event_bridge");
static int call(volatile unsigned char *p,const void *target,unsigned wide,unsigned mask,unsigned frame)
{
    uint32_t d=(uint32_t)p[1]|((uint32_t)p[2]<<8);
    if (wide) d|=(uint32_t)p[3]<<16|(uint32_t)p[4]<<24;
    else if (d&0x8000u) d|=UINT32_C(0xffff0000);
    return p[0]==(wide?0xdd:0xcd)&&p[wide?5:3]==mask&&p[wide?6:4]==frame&&
        (uint32_t)(uintptr_t)p+d==(uint32_t)(uintptr_t)target;
}
int ep7i_native_cohort_present(void)
{
    return ep7_stock_mvc_parent_vtable_unresolved[0]==(uint32_t)(uintptr_t)parent&&
        call(ep7_stock_ui_preprocess_call_unresolved,prep,1,0xb0,224)&&
        call(ep7_stock_ui_dispatch_call_unresolved,dispatch,1,0xf0,48)&&
        call(ep7_stock_ui_wheel_1_call_unresolved,sample,0,0,0)&&
        call(ep7_stock_ui_wheel_0_call_unresolved,sample,0,0,0)&&
        call(ep7_stock_ui_wheel_2_call_unresolved,sample,0,0,0)&&
        call(ep7_stock_ui_wheel_4_call_unresolved,sample,0,0,0)&&
        call(ep7_stock_ui_wheel_3_call_unresolved,sample,0,0,0);
}
