#include "native_resource.h"

extern const uint8_t ep7_stock_hl_text_descriptor_unresolved[EP7_TEXT_DESCRIPTOR_BYTES];
extern const uint8_t ep7_stock_hl_text_layouts_unresolved[16];
_Static_assert(sizeof(void *)==4,"resource contains native32 pointers");
_Static_assert(sizeof(struct ep7_text_resource)==112,"owned resource extent");

void ep7_text_resource_prepare(struct ep7_text_resource *r)
{
    for (unsigned i=0;i<EP7_TEXT_DESCRIPTOR_BYTES;i++)
        r->descriptor[i]=ep7_stock_hl_text_descriptor_unresolved[i];
    r->descriptor[94]=r->descriptor[95]=0;
    for (unsigned i=0;i<sizeof r->layouts;i++)
        r->layouts[i]=ep7_stock_hl_text_layouts_unresolved[i];
    r->descriptor[2]=(uint8_t)EP7_HL_TEXT_WIDGET_ID;
    r->descriptor[3]=(uint8_t)(EP7_HL_TEXT_WIDGET_ID>>8);
    uintptr_t layouts=(uintptr_t)r->layouts;
    for (unsigned i=0;i<4;i++) r->descriptor[4+i]=(uint8_t)(layouts>>(8*i));
}
