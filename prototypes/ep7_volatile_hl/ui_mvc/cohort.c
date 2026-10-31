#include "lifetime.h"
extern volatile uint32_t ep7_stock_gui_color_entry_unresolved;
extern volatile uint32_t ep7_stock_gui_color_exit_unresolved;
extern volatile uint32_t ep7_stock_mvc_parent_vtable_unresolved[];
extern volatile uint32_t ep7_stock_mvc_viewer_vtable_unresolved[];
extern const unsigned char entry[] __asm__("ep7_native_mvc_gui_entry_bridge");
extern const unsigned char leave[] __asm__("ep7_native_mvc_gui_exit_bridge");
extern const unsigned char parent[] __asm__("ep7_native_mvc_parent_destroy_bridge");
extern const unsigned char viewer[] __asm__("ep7_native_mvc_viewer_destroy_bridge");
extern const unsigned char rebuild[] __asm__("ep7_native_content_rebuild_bridge");
extern volatile unsigned char ep7_stock_mvc_rebuild_initial_call_unresolved[];
extern volatile unsigned char ep7_stock_mvc_rebuild_previous_call_unresolved[];
extern volatile unsigned char ep7_stock_mvc_rebuild_next_call_unresolved[];
extern volatile unsigned char ep7_stock_mvc_rebuild_touch_call_unresolved[];
static int rebuild_call(volatile unsigned char *p)
{
    uint32_t displacement=(uint32_t)p[1]|((uint32_t)p[2]<<8);
    if (displacement&0x8000u) displacement|=UINT32_C(0xffff0000);
    return p[0]==0xcdu&&p[3]==0xf0u&&p[4]==28u&&
        (uint32_t)(uintptr_t)p+displacement==(uint32_t)(uintptr_t)rebuild;
}
int ep7m_native_cohort_present(void)
{
    return ep7_stock_gui_color_entry_unresolved==(uint32_t)(uintptr_t)entry&&
        ep7_stock_gui_color_exit_unresolved==(uint32_t)(uintptr_t)leave&&
        ep7_stock_mvc_parent_vtable_unresolved[40/4]==(uint32_t)(uintptr_t)parent&&
        ep7_stock_mvc_viewer_vtable_unresolved[4/4]==(uint32_t)(uintptr_t)viewer&&
        rebuild_call(ep7_stock_mvc_rebuild_initial_call_unresolved)&&
        rebuild_call(ep7_stock_mvc_rebuild_previous_call_unresolved)&&
        rebuild_call(ep7_stock_mvc_rebuild_next_call_unresolved)&&
        rebuild_call(ep7_stock_mvc_rebuild_touch_call_unresolved);
}
