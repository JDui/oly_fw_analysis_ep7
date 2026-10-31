#include "lifetime.h"
extern volatile uint32_t ep7_stock_gui_color_entry_unresolved;
extern volatile uint32_t ep7_stock_gui_color_exit_unresolved;
extern volatile uint32_t ep7_stock_mvc_parent_vtable_unresolved[];
extern volatile uint32_t ep7_stock_mvc_viewer_vtable_unresolved[];
extern const unsigned char entry[] __asm__("ep7_native_mvc_gui_entry_bridge");
extern const unsigned char leave[] __asm__("ep7_native_mvc_gui_exit_bridge");
extern const unsigned char parent[] __asm__("ep7_native_mvc_parent_destroy_bridge");
extern const unsigned char viewer[] __asm__("ep7_native_mvc_viewer_destroy_bridge");
int ep7m_native_cohort_present(void)
{
    return ep7_stock_gui_color_entry_unresolved==(uint32_t)(uintptr_t)entry&&
        ep7_stock_gui_color_exit_unresolved==(uint32_t)(uintptr_t)leave&&
        ep7_stock_mvc_parent_vtable_unresolved[40/4]==(uint32_t)(uintptr_t)parent&&
        ep7_stock_mvc_viewer_vtable_unresolved[4/4]==(uint32_t)(uintptr_t)viewer;
}
