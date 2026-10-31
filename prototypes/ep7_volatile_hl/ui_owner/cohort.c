#include "owner.h"
/* Read-only use of mapped native vtables. G6 patches them only at cold startup;
 * volatile prevents folding their observed values into an assumed cohort. */
extern volatile uint32_t ep7_stock_ui_service_vtable_unresolved[];
extern volatile uint32_t ep7_stock_ui_display_vtable_unresolved[];
extern const unsigned char manager[] __asm__("ep7_native_ui_screen_bridge");
extern const unsigned char cleanup[] __asm__("ep7_native_ui_owner_cleanup_bridge");
extern const unsigned char bulk[] __asm__("ep7_native_ui_owner_bulk_bridge");
extern const unsigned char destructor[] __asm__("ep7_native_ui_owner_destructor_bridge");
int ep7u_native_cohort_present(void)
{
    return ep7_stock_ui_service_vtable_unresolved[784/4]==(uint32_t)(uintptr_t)manager&&
        ep7_stock_ui_display_vtable_unresolved[152/4]==(uint32_t)(uintptr_t)cleanup&&
        ep7_stock_ui_display_vtable_unresolved[432/4]==(uint32_t)(uintptr_t)bulk&&
        ep7_stock_ui_display_vtable_unresolved[0]==(uint32_t)(uintptr_t)destructor;
}
