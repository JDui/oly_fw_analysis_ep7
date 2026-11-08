#include <stdint.h>

enum {
    BRACKET_FRAMES = 5,
    SCENE_PROGRAM = 24,
    FIRST_CURTAIN = 166,
    HDR_COMPOSITE = 600,
    ELECTRONIC_SHUTTER = 764,
    STILL_SEQUENCE = 1487,
    BRACKET_KIND = 1494,
    DRIVE = 3281,
    SINGLE_MECHANICAL = 0,
    SINGLE_ANTI_SHOCK = 12,
    SINGLE_SILENT = 24,
    ATT_CONTINUOUS = 8,
    ATT_HDR = 512,
    ATT_SILENT = 65536,
    HDR1 = 1,
    HDR_BRACKET = 4,
    HDR1_FRAMES = 4,
};

uint32_t ep7rec_get(unsigned property);
uint32_t ep7rec_get_setting(unsigned property);
void ep7rec_write_effective(unsigned property, unsigned value);
uint32_t ep7rec_settings_inhibit(void);
uint32_t ep7rec_get_trigger(void);
uint32_t ep7rec_judge_sequence(uint32_t owner);
void ep7rec_publish_sequence(uint32_t sequence);

/* Shared with the native silent-shutter guard, on the shooting task. */
uint32_t ep7rec_owner;

static int effective_settings_available(void)
{
    /* The typed setter queues writes on other cores. This scope needs the
     * synchronous path for both admission and terminal restoration. */
    return (*(volatile const uint32_t *)0xa272e420u & 4u) &&
           *(volatile const uint32_t *)0x8050u == 0;
}

static int still_release_enabled(uint32_t owner)
{
    /* setCtrlReleaseStatus supplies the same active and still enables used
     * by the physical shutter. Bit 2 belongs to the interval session. */
    return *(volatile const uint32_t *)0x61facce0u &&
           *(volatile const uint32_t *)0x61facd00u &&
           !(*(volatile const uint32_t *)(owner + 728u) & 2u);
}

static int selected_single_drive(uint32_t drive)
{
    uint32_t electronic = ep7rec_get(ELECTRONIC_SHUTTER);
    uint32_t first_curtain = ep7rec_get(FIRST_CURTAIN);
    return (drive == SINGLE_MECHANICAL && electronic == 0 && first_curtain == 0) ||
           (drive == SINGLE_ANTI_SHOCK && electronic == 0 && first_curtain == 1) ||
           (drive == SINGLE_SILENT && electronic == 1 && first_curtain == 0);
}

static int restore_capture_settings(void)
{
    /* Only undo the effective values owned by this request. */
    if (ep7rec_get(HDR_COMPOSITE) == HDR1)
        ep7rec_write_effective(HDR_COMPOSITE, 0);
    if (ep7rec_get(BRACKET_KIND) == HDR_BRACKET)
        ep7rec_write_effective(BRACKET_KIND, 0);
    if (ep7rec_get(BRACKET_FRAMES) == HDR1_FRAMES)
        ep7rec_write_effective(BRACKET_FRAMES, 0);
    return ep7rec_get(HDR_COMPOSITE) != HDR1 &&
           ep7rec_get(BRACKET_KIND) != HDR_BRACKET &&
           ep7rec_get(BRACKET_FRAMES) != HDR1_FRAMES;
}

int ep7rec_begin(uint32_t owner)
{
    if (!owner || ep7rec_owner || !effective_settings_available() ||
        !still_release_enabled(owner) || ep7rec_settings_inhibit() || (ep7rec_get_trigger() & 1))
        return 0;

    uint32_t scene = ep7rec_get(SCENE_PROGRAM);
    uint32_t drive = ep7rec_get_setting(DRIVE);
    if (scene < 3 || scene > 6 || ep7rec_get(STILL_SEQUENCE) != 1 ||
        ep7rec_get(HDR_COMPOSITE) != 0 || ep7rec_get(BRACKET_KIND) != 0 ||
        ep7rec_get(BRACKET_FRAMES) != 0 || !selected_single_drive(drive))
        return 0;

    ep7rec_owner = owner;
    ep7rec_write_effective(BRACKET_FRAMES, HDR1_FRAMES);
    ep7rec_write_effective(BRACKET_KIND, HDR_BRACKET);
    ep7rec_write_effective(HDR_COMPOSITE, HDR1);
    if (ep7rec_get(HDR_COMPOSITE) == HDR1 && ep7rec_get(BRACKET_KIND) == HDR_BRACKET &&
        ep7rec_get(BRACKET_FRAMES) == HDR1_FRAMES) {
        uint32_t sequence = ep7rec_judge_sequence(owner);
        uint32_t mask = ATT_HDR | ATT_CONTINUOUS | ATT_SILENT;
        uint32_t required = ATT_HDR | ATT_CONTINUOUS | (drive == SINGLE_SILENT ? ATT_SILENT : 0);
        if ((sequence & mask) == required) {
            ep7rec_publish_sequence(sequence);
            return 1;
        }
    }

    if (restore_capture_settings())
        ep7rec_owner = 0;
    return 0;
}

void ep7rec_end(uint32_t owner, uint32_t cleared_trigger_bits)
{
    if (!ep7rec_owner || ep7rec_owner != owner || !(cleared_trigger_bits & 1) ||
        !effective_settings_available() || !restore_capture_settings())
        return;

    ep7rec_owner = 0;
    ep7rec_publish_sequence(ep7rec_judge_sequence(owner));
}
