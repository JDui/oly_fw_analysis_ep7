#include "lifetime.h"
#include "../target/far_call.h"
extern const unsigned char far_calls[] __asm__("ep7_mvc_far_calls");
extern const unsigned char far_calls_end[] __asm__("ep7_mvc_far_calls_end");
extern volatile uint32_t ep7_stock_gui_color_entry_unresolved;
extern volatile uint32_t ep7_stock_gui_color_exit_unresolved;
extern volatile uint32_t ep7_stock_mvc_parent_vtable_unresolved[];
extern volatile uint32_t ep7_stock_mvc_viewer_vtable_unresolved[];
extern const unsigned char entry[] __asm__("ep7_native_mvc_gui_entry_bridge");
extern const unsigned char leave[] __asm__("ep7_native_mvc_gui_exit_bridge");
extern const unsigned char parent[] __asm__("ep7_native_mvc_parent_destroy_bridge");
extern const unsigned char viewer[] __asm__("ep7_native_mvc_viewer_destroy_bridge");
extern const unsigned char draw[] __asm__("ep7_native_ui_viewer_bridge");
extern const unsigned char rebuild[] __asm__("ep7_native_content_rebuild_bridge");
extern volatile unsigned char ep7_stock_mvc_rebuild_initial_call_unresolved[];
extern volatile unsigned char ep7_stock_mvc_rebuild_previous_call_unresolved[];
extern volatile unsigned char ep7_stock_mvc_rebuild_next_call_unresolved[];
extern volatile unsigned char ep7_stock_mvc_rebuild_touch_call_unresolved[];
static int rebuild_call(volatile unsigned char *p,unsigned index)
{
    const unsigned char *veneer=far_calls+index*EP7_FAR_CALL_BYTES;
    return ep7n_far_call_present((uint32_t)(uintptr_t)p,p,(uint32_t)(uintptr_t)veneer,veneer,
                                (uint32_t)(uintptr_t)rebuild,0xf0,28);
}
int ep7m_native_cohort_present(void)
{
    return (uintptr_t)far_calls_end-(uintptr_t)far_calls==4u*EP7_FAR_CALL_BYTES&&
        ep7_stock_gui_color_entry_unresolved==(uint32_t)(uintptr_t)entry&&
        ep7_stock_gui_color_exit_unresolved==(uint32_t)(uintptr_t)leave&&
        ep7_stock_mvc_parent_vtable_unresolved[40/4]==(uint32_t)(uintptr_t)parent&&
        ep7_stock_mvc_viewer_vtable_unresolved[4/4]==(uint32_t)(uintptr_t)viewer&&
        ep7_stock_mvc_viewer_vtable_unresolved[0]==(uint32_t)(uintptr_t)draw&&
        rebuild_call(ep7_stock_mvc_rebuild_initial_call_unresolved,0)&&
        rebuild_call(ep7_stock_mvc_rebuild_previous_call_unresolved,1)&&
        rebuild_call(ep7_stock_mvc_rebuild_next_call_unresolved,2)&&
        rebuild_call(ep7_stock_mvc_rebuild_touch_call_unresolved,3);
}
