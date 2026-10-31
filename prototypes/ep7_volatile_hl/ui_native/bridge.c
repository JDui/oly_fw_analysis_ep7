/* Narrow native routing seam; the provider owns the complete transaction. */
#include "input.h"
_Static_assert(sizeof(struct ep7_native_ui_input)==20,"native input layout");
uint32_t ep7_gcc_ui_route(const struct ep7_native_ui_input *input)
{
    if(!input) return 0;
    /* This seam deliberately leaves category navigation and all stock events
       with their original parent dispatcher. */
    if(input->event!=0x9031u && input->event!=0x9032u && input->event!=0x9014u)
        return EP7_NATIVE_CALL_STOCK;
    return ep7i_route(input);
}
