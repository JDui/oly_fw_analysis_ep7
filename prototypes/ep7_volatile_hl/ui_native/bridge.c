/* Narrow native routing seam; the provider owns the complete transaction. */
#include "input.h"
#include "../ui_gate/gate.h"
_Static_assert(sizeof(struct ep7_native_ui_input)==20,"native input layout");
uint32_t ep7_gcc_ui_route(const struct ep7_native_ui_input *input)
{
    if(!input) return 0;
    int previous=ep7g_before_event((void *)(uintptr_t)input->parent);
    /* This seam deliberately leaves category navigation and all stock events
       with their original parent dispatcher. */
    if(input->event!=0x9031u && input->event!=0x9032u && input->event!=0x9014u)
        return EP7_NATIVE_CALL_STOCK;
    /* A mode/owner transition must not reinterpret this H/L edit as S input. */
    struct ep7i_scope *s=&ep7_native_ui_input_scope;
    if (previous>=4&&ep7_native_mvc.category<4) {
        if (s->phase==3) s->consumed=2;
        return 0;
    }
    if (previous>=0&&s->phase==3&&s->consumed==2) return 0;
    return ep7i_route(input);
}
