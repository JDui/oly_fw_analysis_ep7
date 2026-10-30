#ifndef EP7P_UI_H
#define EP7P_UI_H
#include "ep7p.h"
#include "ep7_ui_adapter_contract.h"
#define EP7P_UI_SLOTS 4u /* Prototype capacity, not native firmware capacity. */
typedef struct {
    uint32_t generation;
    bool active, enabled, all;
    uint16_t mode;
    uint8_t category, sector;
} ep7p_ui_slot;
typedef struct { ep7p *core; ep7p_ui_slot slots[EP7P_UI_SLOTS]; } ep7p_ui;
/* Initialize before sharing. All UI callbacks require a serialized UI caller;
 * this is not a native GUI scheduler or register/vtable ABI implementation. */
void ep7p_ui_init(ep7p_ui *, ep7p *);
extern const struct ep7_ui_adapter_ops ep7p_ui_ops;
#endif
