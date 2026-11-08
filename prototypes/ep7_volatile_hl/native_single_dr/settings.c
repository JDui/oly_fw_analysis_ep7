/* Settings admitted at the build1100 StlRdy2 exposure submission. */
#include "single_dr.h"

extern int ep7h_stock_value(unsigned property);
extern uint32_t ep7h_active_get(unsigned property);
extern void ep7h_active_set(unsigned property, uint32_t value);
extern uint32_t ep7dr_settings_irq_lock(void);
extern void ep7dr_settings_irq_unlock(uint32_t psw);

#define CURRENT_COMMAND 0x6223d414u
#define STILL_ENGINE 0x6223d8a0u
#define STILL_DESCRIPTOR 0x6223d488u
#define CORE_ID 0x8050u
#define PICTURE_MODE_PROPERTY 111u
#define PICTURE_MODE_KEY 0x9481u
#define COLOR_SELECTOR_KEY 0xf6b1u
#define GRADATION_KEY 0x8eb9u
#define FORCE_AUTO_GRADATION_KEY 0x9961u
#define ALTERNATE_DEVELOPMENT_KEY 0xeee1u
#define ALTERNATE_STAGE_KEY 0x69b9u
#define SPECIAL_CAPTURE_KEY 0xe911u
#define QUALITY_KEY 0x8141u
#define SPECIAL_FORMAT_KEY 0x8231u
#define AUXILIARY_FORMAT_KEY 0x52b1u
#define ISO_KEY 0x810au
#define ELECTRONIC_SHUTTER_KEY 0xf101u
#define SPECIAL_SHUTTER_KEY 0x99e1u

struct bank_epoch {
    uint32_t depth;
    uint32_t sequence;
};

/* Uncached extension storage, one writer core per element. Native veneers
 * mask local interrupts only around the two observer functions. */
static volatile struct bank_epoch bank_epochs[3];

#ifdef EP7DR_LAB_STAGING
static _Alignas(4) volatile uint32_t staged_levels[9];
#else
static const uint16_t level_properties[] = {
    894, 963, 966, 969, 1672, 998, 1001, 1004, 1675,
};
static const uint32_t level_words[] = {0, 0x445201feu, 0x445202fdu};
#endif

static uint32_t word(uint32_t address)
{
    return *(const volatile uint32_t *)(uintptr_t)address;
}

static uint16_t half(uint32_t address)
{
    return *(const volatile uint16_t *)(uintptr_t)address;
}

static uint8_t byte(uint32_t address)
{
    return *(const volatile uint8_t *)(uintptr_t)address;
}

void ep7dr_bank_begin(void)
{
    uint32_t core = word(CORE_ID);
    /* Every wrapped entry, including cold bank save/reset, must avoid the
     * extension until the original loaded-image flag admits its RAM alias. */
    if (core < 3u && (word(0xa272e420u) & 4u))
        ++bank_epochs[core].depth;
}

void ep7dr_bank_end(void)
{
    uint32_t core = word(CORE_ID);
    if (core < 3u && (word(0xa272e420u) & 4u) && bank_epochs[core].depth) {
        ++bank_epochs[core].sequence;
        --bank_epochs[core].depth;
    }
}

static int bank_unchanged(uint32_t first, uint32_t second, uint32_t third)
{
    return !bank_epochs[0].depth && !bank_epochs[1].depth && !bank_epochs[2].depth &&
           bank_epochs[0].sequence == first && bank_epochs[1].sequence == second &&
           bank_epochs[2].sequence == third;
}

static int slot_for_mode(uint32_t public_mode)
{
    switch (public_mode) {
#ifndef EP7DR_HIGHLIGHT_MAPPING
    case 1u: return 0;   /* Archived gain-route scope. */
#endif
    case 54u: return 1;  /* COLOR 1–4 each own one native curve group. */
    case 55u: return 2;
    case 56u: return 3;
    case 64u: return 4;
    default: return -1;
    }
}

int ep7dr_storage_scope(uint32_t public_mode)
{
    switch (public_mode) {
    case 0u: case 1u: case 2u: case 3u: case 5u:
    case 6u: case 7u: case 20u: case 21u: return 0;
    case 54u: return 1;
    case 55u: return 2;
    case 56u: return 3;
    case 64u: return 4;
    case 57u: return 5;
    case 58u: return 6;
    case 59u: return 7;
    case 65u: return 8;
    default: return -1;
    }
}

static int settings_ready(void);

/* Read-only on-camera diagnosis. Do not relax a bank guard without knowing
 * which live condition blocked it. Bits are documented in the release note. */
uint32_t ep7dr_settings_blockers(uint32_t public_mode)
{
    uint32_t result = 0;
    if (word(CORE_ID) >= 3u) result |= 0x0001u;
    if (!(word(0xa272e420u) & 4u)) return result | 0x0002u;
    if (!word(0x62253594u)) result |= 0x0004u;
    if (byte(0x62257b04u)) result |= 0x0008u;
    /* 0x0010 retired: 622484fa stays set between separate session enter/leave
     * calls. Their actual execution is covered by the bank epochs instead. */
    if (word(0x61fa7538u)) result |= 0x0020u;
    if (bank_epochs[0].depth) result |= 0x0040u;
    if (bank_epochs[1].depth) result |= 0x0080u;
    if (bank_epochs[2].depth) result |= 0x0100u;
    unsigned head = half(0xa2715c8cu), tail = half(0xa2715c8eu);
    if (head >= 16u || tail >= 16u) result |= 0x0200u;
    if (head != tail || head != half(0xa2715c8cu)) result |= 0x0400u;
    if (ep7dr_storage_scope(public_mode) < 0) result |= 0x0800u;
    return result;
}

/* GUI-only view of a completed submission to the stock typed-write ring.
 * Capture readers still require the ring to drain and read ACTIVE. */
static int queued_level(int scope)
{
#ifdef EP7DR_LAB_STAGING
    (void)scope;
    return -1;
#else
    unsigned head = half(0xa2715c8cu), tail = half(0xa2715c8eu);
    int level = -1;
    if (head >= 16u || tail >= 16u || head == tail)
        return -1;
    for (unsigned i = tail; i != head; i = (i + 1u) & 15u) {
        uint32_t entry = 0xa2715accu + 28u * i;
        if (half(entry) == 1u && half(entry + 2u) == 0x8b64u &&
            half(entry + 4u) == 1769u + level_properties[scope] &&
            word(entry + 8u) == word(0x62253594u)) {
            uint32_t value = word(entry + 12u);
            level = value == level_words[0] ? 0 :
                    value == level_words[1] ? 1 : value == level_words[2] ? 2 : -1;
        }
    }
    return head == half(0xa2715c8cu) && tail == half(0xa2715c8eu) ? level : -1;
#endif
}

int ep7dr_display_level(uint32_t public_mode)
{
    int scope = ep7dr_storage_scope(public_mode);
    int level = ep7dr_selected_level(public_mode);
    if (level >= 0 || scope < 0 || word(CORE_ID) >= 3u ||
        !(word(0xa272e420u) & 4u) || !word(0x62253594u) ||
        byte(0x62257b04u) || word(0x61fa7538u) ||
        bank_epochs[0].depth || bank_epochs[1].depth || bank_epochs[2].depth)
        return level;
    return queued_level(scope);
}

static uint32_t scope_level(int scope)
{
#ifdef EP7DR_LAB_STAGING
    uint32_t value = staged_levels[scope];
    return value <= 2u ? value : 0;
#else
    uint32_t value = ep7h_active_get(level_properties[scope]);
    if (value == level_words[1])
        return 1;
    if (value == level_words[2])
        return 2;
    return 0;
#endif
}

int ep7dr_stage_level(uint32_t public_mode, uint32_t level)
{
    int scope = ep7dr_storage_scope(public_mode);
    if (scope < 0 || level > 2u || word(CORE_ID) >= 3u)
        return 0;

#ifdef EP7DR_LAB_STAGING
    staged_levels[scope] = level;
    return 1;
#else
    uint32_t first = bank_epochs[0].sequence;
    uint32_t second = bank_epochs[1].sequence;
    uint32_t third = bank_epochs[2].sequence;
    if (!settings_ready() || !bank_unchanged(first, second, third) ||
        ep7h_stock_value(PICTURE_MODE_PROPERTY) != (int)public_mode)
        return 0;

    /* Stock owns inter-core enqueue and serialization. Do not hold a local
     * IRQ mask across its kernel calls, and do not mistake enqueue for an
     * immediately visible ACTIVE store. */
    if (word(CORE_ID)) {
        if (word(0x62253594u) != 0xa250ba00u)
            return 0;
        if (scope_level(scope) != level)
            ep7h_active_set(level_properties[scope], level_words[level]);
        return bank_unchanged(first, second, third) &&
               ((settings_ready() && scope_level(scope) == level) ||
                queued_level(scope) == (int)level);
    }
    uint32_t psw = ep7dr_settings_irq_lock();
    int accepted = 0;
    if (settings_ready() && bank_unchanged(first, second, third) &&
        word(0x62253594u) == 0x6250ba00u) {
        if (scope_level(scope) != level)
            ep7h_active_set(level_properties[scope], level_words[level]);
        accepted = scope_level(scope) == level && bank_unchanged(first, second, third) &&
                   settings_ready();
    }
    ep7dr_settings_irq_unlock(psw);
    return accepted;
#endif
}

int ep7dr_selected_level(uint32_t public_mode)
{
    int scope = ep7dr_storage_scope(public_mode);
    uint32_t first = bank_epochs[0].sequence;
    uint32_t second = bank_epochs[1].sequence;
    uint32_t third = bank_epochs[2].sequence;
    if (scope < 0 ||
#ifdef EP7DR_HIGHLIGHT_MAPPING
        word(CORE_ID) >= 3u ||
#else
        word(CORE_ID) ||
#endif
        !settings_ready() ||
        !bank_unchanged(first, second, third))
        return -1;

    uint32_t level = scope_level(scope);
    return bank_unchanged(first, second, third) && settings_ready() ? (int)level : -1;
}

static int still_context(uint32_t command, uint32_t engine)
{
    if (word(CORE_ID) || !command || (command & 3u) ||
        command != word(CURRENT_COMMAND) || engine != STILL_ENGINE ||
        half(engine) != 7u || word(engine + 12u) != STILL_DESCRIPTOR ||
        half(STILL_DESCRIPTOR) != 10u || byte(0x6223dbeau) ||
        byte(0x6223dabcu) || byte(0x6223dd48u) || byte(0x6223dbf4u))
        return 0;

    uint32_t metadata = word(engine + 4u);
    if (!metadata || metadata != word(command + 60u))
        return 0;

    /* The controller reports these three fields together as strobe_info.
     * The sensor input also has to meet the ordinary calculation shape. */
    return !byte(0x6223daa2u) && !byte(0x6223dac6u) &&
           !half(0x6223dac8u) && !half(0x6223dacau) &&
           !(word(metadata) & 0x80u) && !word(metadata + 32u) &&
           !half(metadata + 44u);
}

static int settings_ready(void)
{
    /* Core 1 can return from the native bank writer before its typed
     * copies are consumed. The consumer advances the tail after the store. */
    uint16_t head = half(0xa2715c8cu);
    uint16_t tail = half(0xa2715c8eu);
    /* These are observed busy flags. They do not cover every bank writer. */
    return head < 16u && head == tail && head == half(0xa2715c8cu) &&
           (word(0xa272e420u) & 4u) && word(0x62253594u) &&
           !byte(0x62257b04u) && !word(0x61fa7538u);
}

static int normal_gradation(void)
{
    return ep7dr_stock_key(GRADATION_KEY) == 0 &&
           ep7dr_stock_key(FORCE_AUTO_GRADATION_KEY) == 0;
}

static int ordinary_development(void)
{
    /* These feed capture+24799, +24050 and +24134. Each can
     * select an alternate development route. */
    return ep7dr_stock_key(ALTERNATE_DEVELOPMENT_KEY) == 0 &&
           ep7dr_stock_key(ALTERNATE_STAGE_KEY) == 0 &&
           ep7dr_stock_key(SPECIAL_CAPTURE_KEY) == 0;
}

static int ordinary_jpeg(void)
{
    return ep7dr_stock_key(QUALITY_KEY) == 1 &&
           ep7dr_stock_key(SPECIAL_FORMAT_KEY) == 0 &&
           ep7dr_stock_key(AUXILIARY_FORMAT_KEY) == 0;
}

static int ordinary_shutter_setting(void)
{
    return ep7dr_stock_key(ELECTRONIC_SHUTTER_KEY) == 0 &&
           ep7dr_stock_key(SPECIAL_SHUTTER_KEY) == 0;
}

static int native_profile_matches(int slot)
{
    if (slot == 0)
        return ep7dr_stock_key(PICTURE_MODE_KEY) == 2;

    return ep7dr_stock_key(PICTURE_MODE_KEY) == 11 &&
           ep7dr_stock_key(COLOR_SELECTOR_KEY) == slot;
}

enum ep7dr_selection_status ep7dr_selection_status(uint32_t public_mode, uint32_t level)
{
    if (level == 0)
        return EP7DR_SELECTION_AVAILABLE;

    int slot = slot_for_mode(public_mode);
    if (level > 2u || slot < 0 || word(CORE_ID) >= 3u ||
        !native_profile_matches(slot) || !normal_gradation() ||
        !ordinary_development()
#ifndef EP7DR_HIGHLIGHT_MAPPING
        || !ordinary_jpeg() || !ordinary_shutter_setting()
#endif
        )
        return EP7DR_SELECTION_UNAVAILABLE;

#ifdef EP7DR_HIGHLIGHT_MAPPING
    /* A rendering policy has no exposure or ISO floor. */
    return EP7DR_SELECTION_AVAILABLE;
#else
    int iso = ep7dr_stock_key(ISO_KEY);
    if (iso <= 0 || iso > 2048)
        return EP7DR_SELECTION_UNAVAILABLE;
    if (iso < 1536 + (int32_t)level * 256)
        return EP7DR_SELECTION_ISO_LOW;
    return ep7dr_fixed_nominal_admissible(iso, level) ?
           EP7DR_SELECTION_AVAILABLE : EP7DR_SELECTION_UNAVAILABLE;
#endif
}

uint32_t ep7dr_select_scoped_level(uint32_t command, uint32_t engine,
                                   uint32_t *mode)
{
    if (!mode)
        return 0;
    *mode = 0;
    uint32_t first = bank_epochs[0].sequence;
    uint32_t second = bank_epochs[1].sequence;
    uint32_t third = bank_epochs[2].sequence;
    if (!still_context(command, engine) || !settings_ready() ||
        !bank_unchanged(first, second, third))
        return 0;

    int public_mode = ep7h_stock_value(PICTURE_MODE_PROPERTY);
    int slot = slot_for_mode((uint32_t)public_mode);
    if (slot < 0)
        return 0;
    if (!native_profile_matches(slot) || !normal_gradation() ||
        !ordinary_development() || !ordinary_jpeg() || !ordinary_shutter_setting())
        return 0;

    uint32_t level = scope_level(slot);
    if (level < 1u || level > 2u || !ordinary_jpeg() || !ordinary_shutter_setting() ||
        !ordinary_development() || !normal_gradation() ||
        !native_profile_matches(slot) ||
        ep7h_stock_value(PICTURE_MODE_PROPERTY) != public_mode ||
        !settings_ready() || !still_context(command, engine) ||
        !bank_unchanged(first, second, third))
        return 0;

    *mode = (uint32_t)public_mode;
    return level;
}
