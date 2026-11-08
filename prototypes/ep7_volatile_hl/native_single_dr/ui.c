/* The curve child owns page navigation. The settings module owns the level. */
#include "single_dr.h"

extern int ep7h_stock_value(unsigned property);
#ifdef EP7DR_HIGHLIGHT_MAPPING
extern void ep7h_refresh(unsigned profile);

static void refresh_color(int mode)
{
    /* Reuse the installed 015 COLOR publication callback, after accepting
     * the ACTIVE write/enqueue and outside the settings IRQ critical section.
     * This updates processing, whereas the child redraw only updates UI. */
    if (mode >= 54 && mode <= 56)
        ep7h_refresh((unsigned)mode - 54u);
    else if (mode == 64)
        ep7h_refresh(3u);
}
#endif

volatile uintptr_t ep7dr_ui_child;
volatile unsigned ep7dr_ui_building_curve;

static uint32_t word(uintptr_t address)
{
    return *(const volatile uint32_t *)address;
}

static uint16_t half(uintptr_t address)
{
    return *(const volatile uint16_t *)address;
}

static uint8_t byte(uintptr_t address)
{
    return *(const volatile uint8_t *)address;
}

static int curve_mode(uintptr_t child)
{
    if (!child || word(0x8050u) >= 3u || !(word(0xa272e420u) & 4u) ||
        !word(0x62253594u) || word(child) != 0x61159ea8u ||
        half(child + 220u) != 2u || half(child + 236u) != 383u)
        return -1;

    int mode = ep7h_stock_value(111u);
    int row = ep7dr_storage_scope((uint32_t)mode);
    return row >= 0 && word(child + 216u) == 0x611595a8u + 56u * (unsigned)row
               ? mode : -1;
}

static int current_curve(uintptr_t child)
{
    if (word(0x8050u) >= 3u)
        return 0;
    uintptr_t machine = word(0x61fb2564u);
    if (!machine || byte(machine) != 4u || byte(machine + 1u) != 29u)
        return 0;

    uintptr_t container = word(0x61fc436cu);
    if (!container)
        return 0;

    uintptr_t parent = word(container);
    uintptr_t viewer = word(container + 4u);
    if (!parent || !viewer || word(parent) != 0x6118957cu ||
        word(viewer) != 0x61189ba8u || word(viewer + 384u) != parent ||
        word(parent + 80u) != child)
        return 0;

    uintptr_t selector = word(parent + 76u);
    return selector && half(selector + 86u) == 3u;
}

int ep7dr_ui_start_first_page(uintptr_t child)
{
    if (!ep7dr_ui_building_curve)
        return 0;
    int mode = curve_mode(child);
    return mode >= 0;
}

/* The matching child still owns input when the staged setting is unavailable.
 * This prevents an HDR gesture from falling into a Midtone edit. */
int ep7dr_ui_open(uintptr_t child)
{
    return child && current_curve(child) && child == ep7dr_ui_child &&
           half(child + 222u) == 1u;
}

int ep7dr_ui_draw(uintptr_t viewer)
{
    uintptr_t child = word(viewer + 392u);
    if (!ep7dr_ui_open(child))
        return 0;

    /* The stock viewer zeroes the whole record before this hook. Its type-5
     * guide stores a NUL-terminated UTF-16 string inline at offset 8. */
    static const uint16_t labels[8][26] = {
        u"HDR [OFF] 200 400", u"HDR OFF [200] 400", u"HDR OFF 200 [400]",
        u"HDR unavailable: 0000", u"HDR OFF [200] 400 ISO400+", u"HDR OFF 200 [400] ISO800+",
        u"HDR OFF [200] 400 N/A", u"HDR OFF 200 [400] N/A",
    };
    int mode = curve_mode(child);
    int level = mode >= 0 ? ep7dr_display_level((uint32_t)mode) : -1;
    unsigned label = 3;
    if (level >= 0 && level <= 2) {
        label = (unsigned)level;
        if (level > 0) {
            enum ep7dr_selection_status status = ep7dr_selection_status((uint32_t)mode, label);
            if (status == EP7DR_SELECTION_ISO_LOW)
                label += 3u;
            else if (status != EP7DR_SELECTION_AVAILABLE)
                label += 5u;
        }
    }
    const uint16_t *text = labels[label];
    uintptr_t offset = word(viewer + 404u) == 1u ? 186u : 260u;
    uint16_t *guide = (uint16_t *)(viewer + offset);
    guide[0] = 5u;
    guide[3] = 2u;
    for (unsigned i = 0; i < sizeof labels[0] / sizeof labels[0][0]; ++i)
        guide[4u + i] = text[i];
#ifdef EP7DR_HIGHLIGHT_MAPPING
    if (label <= 2u) {
        for (unsigned path = 0; path < 2u; ++path) {
            unsigned at = 4u + 17u + 4u * path;
            uint32_t code = ep7dr_highlight_observation(path);
            guide[at] = ' ';
            guide[at + 1u] = path ? 'P' : 'V';
            for (unsigned i = 0; i < 2u; ++i) {
                unsigned digit = (code >> (4u - 4u * i)) & 15u;
                guide[at + 2u + i] = (uint16_t)(digit < 10u ? '0' + digit : 'A' + digit - 10u);
            }
        }
        guide[4u + 25u] = 0;
    }
#endif
    if (label == 3u) {
        uint32_t reasons = mode < 0 ? 0x1000u : ep7dr_settings_blockers((uint32_t)mode);
        if (!reasons) reasons = 0x2000u; /* Gate changed between read and draw. */
        for (unsigned i = 0; i < 4u; ++i) {
            unsigned nibble = (reasons >> (12u - 4u * i)) & 15u;
            guide[4u + 17u + i] = (uint16_t)(nibble < 10u ? '0' + nibble : 'A' + nibble - 10u);
        }
    }
    *(uint32_t *)(viewer + 340u) = 13u;
    return 1;
}

int ep7dr_ui_info(uintptr_t child)
{
    if (ep7dr_ui_open(child)) {
        ep7dr_ui_child = 0;
        return 0;
    }
    if (!current_curve(child) || !child || half(child + 222u) != 1u ||
        word(0x61fc1bacu))
        return 0;

    int mode = curve_mode(child);
    if (mode < 0)
        return 0;
    ep7dr_ui_child = child;
    return 1;
}

/* Zero delegates to stock, one consumes without redraw, two redraws. */
int ep7dr_ui_dial(uintptr_t child, int32_t step)
{
    if (!ep7dr_ui_open(child))
        return 0;

    int mode = curve_mode(child);
    int level = mode >= 0 ? ep7dr_display_level((uint32_t)mode) : -1;
    if (level < 0 || !step || (step > 0 && level == 2) ||
        (step < 0 && !level))
        return 1;

    level += step > 0 ? 1 : -1;
    if (!ep7dr_stage_level((uint32_t)mode, (uint32_t)level))
        return 1;
#ifdef EP7DR_HIGHLIGHT_MAPPING
    ep7dr_highlight_clear_observations();
    refresh_color(mode);
#endif
    return 2;
}

int ep7dr_ui_reset(uintptr_t child)
{
    if (!ep7dr_ui_open(child))
        return 0;
    int mode = curve_mode(child);
    int level = mode >= 0 ? ep7dr_display_level((uint32_t)mode) : -1;
    if (level <= 0)
        return 1;
    if (!ep7dr_stage_level((uint32_t)mode, 0))
        return 1;
#ifdef EP7DR_HIGHLIGHT_MAPPING
    ep7dr_highlight_clear_observations();
    refresh_color(mode);
#endif
    return 2;
}
