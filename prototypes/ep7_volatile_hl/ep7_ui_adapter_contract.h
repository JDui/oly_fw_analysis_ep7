#ifndef EP7_UI_ADAPTER_CONTRACT_H
#define EP7_UI_ADAPTER_CONTRACT_H
/* Portable integration contract only. NO native function addresses, installation,
 * direct memory access, firmware layout casts, native ABI or executable hooks.
 * Proposed H/L values are volatile logical steps; no calibrated pixel units. */
#include <stddef.h>
#include <stdint.h>

enum ep7_ui_axis { EP7_UI_HUE = 0, EP7_UI_LUMINANCE = 1 };
enum ep7_ui_event {
    EP7_UI_SECTOR_PREVIOUS, EP7_UI_SECTOR_NEXT,
    EP7_UI_VALUE_DECREASE, EP7_UI_VALUE_INCREASE,
    EP7_UI_TOGGLE_ALL, EP7_UI_RESET_CURRENT_AXIS
};
enum ep7_ui_result { EP7_UI_REJECTED = -1, EP7_UI_UNCHANGED = 0, EP7_UI_CHANGED = 1 };

/* Ownership supplied by a separately qualified native veneer, not a raw pointer
 * or numeric task ID. A new controller lifetime requires a new token. */
struct ep7_ui_session { uint32_t generation; uint32_t slot; };
struct ep7_ui_frame {
    uint16_t public_mode;       /* Only 54,55,56,64 are admitted for H/L. */
    uint8_t category;          /* New 4=H,5=L. Stock0..3 remain untouched. */
    uint8_t selected_sector;   /* Proposed0..11,255=ALL; not a stock cursor write. */
    int16_t logical_steps[12]; /* Proposed host/core units, not ISP coefficients. */
};
struct ep7_ui_adapter_ops {
    /* These are proposed PORTABLE callbacks, never native vtable typedefs. */
    int (*open)(void *core, struct ep7_ui_session session,
                uint16_t public_mode, uint8_t category);
    int (*sync)(void *core, struct ep7_ui_session session,
                uint16_t public_mode, uint8_t category);
    int (*event)(void *core, struct ep7_ui_session session,
                 enum ep7_ui_event event, uint16_t repeat_count);
    int (*frame)(void *core, struct ep7_ui_session session,
                 struct ep7_ui_frame *out);
    void (*close)(void *core, struct ep7_ui_session session);
};
/* No installer provided: allocation/vtable/event-register veneers are unresolved.
 * A core boot initializer may zero all volatile H/L. UI close only revokes UI
 * ownership; it MUST NOT erase immutable in-flight image snapshots. */
#endif
