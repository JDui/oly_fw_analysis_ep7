#include "input.h"
#include "../target/far_call.h"
extern const unsigned char far_calls[] __asm__("ep7_input_far_calls");
extern const unsigned char far_calls_end[] __asm__("ep7_input_far_calls_end");
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
static int call(volatile unsigned char *p,const void *target,unsigned mask,unsigned frame)
{
    uint32_t d=(uint32_t)p[1]|((uint32_t)p[2]<<8)|((uint32_t)p[3]<<16)|((uint32_t)p[4]<<24);
    return p[0]==0xdd&&p[5]==mask&&p[6]==frame&&
        (uint32_t)(uintptr_t)p+d==(uint32_t)(uintptr_t)target;
}
static int sample_call(volatile unsigned char *p,unsigned index)
{
    const unsigned char *veneer=far_calls+index*EP7_FAR_CALL_BYTES;
    return ep7n_far_call_present((uint32_t)(uintptr_t)p,p,(uint32_t)(uintptr_t)veneer,veneer,
                                (uint32_t)(uintptr_t)sample,0,0);
}
int ep7i_native_cohort_present(void)
{
    return (uintptr_t)far_calls_end-(uintptr_t)far_calls==5u*EP7_FAR_CALL_BYTES&&
        ep7_stock_mvc_parent_vtable_unresolved[0]==(uint32_t)(uintptr_t)parent&&
        call(ep7_stock_ui_preprocess_call_unresolved,prep,0xb0,224)&&
        call(ep7_stock_ui_dispatch_call_unresolved,dispatch,0xf0,48)&&
        sample_call(ep7_stock_ui_wheel_1_call_unresolved,0)&&
        sample_call(ep7_stock_ui_wheel_0_call_unresolved,1)&&
        sample_call(ep7_stock_ui_wheel_2_call_unresolved,2)&&
        sample_call(ep7_stock_ui_wheel_4_call_unresolved,3)&&
        sample_call(ep7_stock_ui_wheel_3_call_unresolved,4);
}
