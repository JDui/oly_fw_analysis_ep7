#include <stdint.h>

enum {
    BRACKET_FRAMES = 5,
    SCENE_PROGRAM = 24,
    FIRST_CURTAIN = 166,
    HDR_COMPOSITE = 600,
    ELECTRONIC_SHUTTER = 764,
    CONTINUOUS = 1487,
    BRACKET_KIND = 1494,
    DRIVE = 3281,
    SINGLE_MECHANICAL = 0,
    SINGLE_ANTI_SHOCK = 12,
    SINGLE_SILENT = 30,
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

/* Last Rec milestone for the BODY version display. No capture decisions use it. */
volatile uint32_t ep7rec_status;
const uint16_t ep7rec_version_labels[][8] = {
    u"1.1v" EP7HL_REC_RELEASE_SUFFIX,
    u"1.1K" EP7HL_REC_RELEASE_SUFFIX, /* Recognized press. */
    u"1.1Q" EP7HL_REC_RELEASE_SUFFIX, /* Event prepared for posting. */
    u"1.1D" EP7HL_REC_RELEASE_SUFFIX, /* Marked event dispatched. */
    u"1.1C" EP7HL_REC_RELEASE_SUFFIX, /* Synchronous settings unavailable. */
    u"1.1M" EP7HL_REC_RELEASE_SUFFIX, /* Single-drive or settings conflict. */
    u"1.1P" EP7HL_REC_RELEASE_SUFFIX, /* Property write or sequence rejected. */
    u"1.1T" EP7HL_REC_RELEASE_SUFFIX, /* HDR scope armed, calling native trigger. */
    u"1.1F" EP7HL_REC_RELEASE_SUFFIX, /* Native trigger cleanup restored settings. */
};

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
     * by the physical shutter. Mask 0x2 belongs to the interval session. */
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
    if (ep7rec_get(CONTINUOUS) == 1)
        ep7rec_write_effective(CONTINUOUS, 0);
    if (ep7rec_get(HDR_COMPOSITE) == HDR1)
        ep7rec_write_effective(HDR_COMPOSITE, 0);
    if (ep7rec_get(BRACKET_KIND) == HDR_BRACKET)
        ep7rec_write_effective(BRACKET_KIND, 0);
    if (ep7rec_get(BRACKET_FRAMES) == HDR1_FRAMES)
        ep7rec_write_effective(BRACKET_FRAMES, 0);
    return ep7rec_get(CONTINUOUS) != 1 &&
           ep7rec_get(HDR_COMPOSITE) != HDR1 &&
           ep7rec_get(BRACKET_KIND) != HDR_BRACKET &&
           ep7rec_get(BRACKET_FRAMES) != HDR1_FRAMES;
}

int ep7rec_begin(uint32_t owner)
{
    if (!owner || ep7rec_owner || !still_release_enabled(owner) ||
        ep7rec_settings_inhibit() || (ep7rec_get_trigger() & 1))
        return 0;
    if (!effective_settings_available()) {
        ep7rec_status = 4;
        return 0;
    }

    uint32_t scene = ep7rec_get(SCENE_PROGRAM);
    uint32_t drive = ep7rec_get_setting(DRIVE);
    if (scene < 3 || scene > 6 || ep7rec_get(CONTINUOUS) != 0 ||
        ep7rec_get(HDR_COMPOSITE) != 0 || ep7rec_get(BRACKET_KIND) != 0 ||
        ep7rec_get(BRACKET_FRAMES) != 0 || !selected_single_drive(drive)) {
        ep7rec_status = 5;
        return 0;
    }

    ep7rec_owner = owner;
    /* Stock single-drive rows clear 1487. JudgeSeqAtt only reads the HDR
     * recipe when 1487 is set, so enable it just for this Rec sequence. */
    ep7rec_write_effective(BRACKET_FRAMES, HDR1_FRAMES);
    ep7rec_write_effective(BRACKET_KIND, HDR_BRACKET);
    ep7rec_write_effective(HDR_COMPOSITE, HDR1);
    ep7rec_write_effective(CONTINUOUS, 1);
    if (ep7rec_get(CONTINUOUS) == 1 && ep7rec_get(HDR_COMPOSITE) == HDR1 &&
        ep7rec_get(BRACKET_KIND) == HDR_BRACKET && ep7rec_get(BRACKET_FRAMES) == HDR1_FRAMES) {
        uint32_t sequence = ep7rec_judge_sequence(owner);
        uint32_t mask = ATT_HDR | ATT_CONTINUOUS | ATT_SILENT;
        uint32_t required = ATT_HDR | ATT_CONTINUOUS | (drive == SINGLE_SILENT ? ATT_SILENT : 0);
        if ((sequence & mask) == required) {
            ep7rec_publish_sequence(sequence);
            ep7rec_status = 7;
            return 1;
        }
    }

    ep7rec_status = 6;
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
    ep7rec_status = 8;
}
