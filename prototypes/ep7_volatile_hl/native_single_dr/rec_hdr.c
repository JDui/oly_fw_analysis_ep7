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
    SHOOTING_CURRENT = 788,
    SHOOTING_NEXT = 792,
    STANDBY = 17,
    READY = 22,
    RELEASE_DOWN_HISTORY = 5,
    FULL_PRESS_EVENT = 4,
    SET_FULL_RELEASE = 0x40000100,
    CLEAR_FULL_RELEASE = 0x20000100,
};

uint32_t ep7rec_get(unsigned property);
uint32_t ep7rec_get_setting(unsigned property);
void ep7rec_write_effective(unsigned property, unsigned value);
uint32_t ep7rec_settings_inhibit(void);
uint32_t ep7rec_get_trigger(void);
uint32_t ep7rec_judge_sequence(uint32_t owner);
void ep7rec_publish_sequence(uint32_t sequence);
void ep7rec_latch_release(unsigned bits);
void ep7rec_unlatch_release(unsigned bits);
void ep7rec_full_release(uint32_t owner, unsigned operation);
uint32_t ep7rec_get_release_event(void);
void ep7rec_set_release_event(unsigned event);

/* Shared with the native silent-shutter guard, on the shooting task. */
uint32_t ep7rec_owner;
static uint32_t release_queued;
static uint32_t previous_release_event;

/* Last Rec milestone for the BODY version display. No capture decisions use it. */
enum {
    REC_CONTEXT = 4,
    REC_MODE,
    REC_PROPERTIES,
    REC_TRIGGER,
    REC_CLEANED,
    REC_NOT_STANDBY,
    REC_RELEASE_LOCKED,
    REC_BUSY,
    REC_RELEASE_QUEUED,
};

volatile uint32_t ep7rec_status;
const uint16_t ep7rec_version_labels[][8] = {
    u"1.1v" EP7HL_REC_RELEASE_SUFFIX,
    u"1.1K" EP7HL_REC_RELEASE_SUFFIX, /* Recognized press. */
    u"1.1Q" EP7HL_REC_RELEASE_SUFFIX, /* Event prepared for posting. */
    u"1.1D" EP7HL_REC_RELEASE_SUFFIX, /* Marked event dispatched. */
    [REC_CONTEXT] = u"1.1C" EP7HL_REC_RELEASE_SUFFIX,
    [REC_MODE] = u"1.1M" EP7HL_REC_RELEASE_SUFFIX,
    [REC_PROPERTIES] = u"1.1P" EP7HL_REC_RELEASE_SUFFIX,
    [REC_TRIGGER] = u"1.1T" EP7HL_REC_RELEASE_SUFFIX,
    [REC_CLEANED] = u"1.1F" EP7HL_REC_RELEASE_SUFFIX,
    [REC_NOT_STANDBY] = u"1.1S" EP7HL_REC_RELEASE_SUFFIX,
    [REC_RELEASE_LOCKED] = u"1.1L" EP7HL_REC_RELEASE_SUFFIX,
    [REC_BUSY] = u"1.1W" EP7HL_REC_RELEASE_SUFFIX,
    [REC_RELEASE_QUEUED] = u"1.1R" EP7HL_REC_RELEASE_SUFFIX,
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
    /* The stock AUTO_RELEASE_ENABLE command sets _activeRelease. Its
     * _isTakePicture field requests an immediate shot and is normally zero.
     * Mask 0x2 belongs to the interval session. */
    return *(volatile const uint32_t *)0x61facce0u &&
           !(*(volatile const uint32_t *)(owner + 728u) & 2u);
}

static uint32_t selector(uint32_t owner, unsigned offset)
{
    return *(const uint32_t *)(owner + offset);
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
    if (!owner || ep7rec_owner || ep7rec_settings_inhibit() || ep7rec_get_trigger() ||
        selector(owner, SHOOTING_CURRENT) != STANDBY || selector(owner, SHOOTING_NEXT) != STANDBY) {
        ep7rec_status = REC_BUSY;
        return 0;
    }
    if (!still_release_enabled(owner)) {
        ep7rec_status = REC_RELEASE_LOCKED;
        return 0;
    }
    if (!effective_settings_available()) {
        ep7rec_status = REC_CONTEXT;
        return 0;
    }

    uint32_t scene = ep7rec_get(SCENE_PROGRAM);
    uint32_t drive = ep7rec_get_setting(DRIVE);
    if (scene < 3 || scene > 6 || ep7rec_get(CONTINUOUS) != 0 ||
        ep7rec_get(HDR_COMPOSITE) != 0 || ep7rec_get(BRACKET_KIND) != 0 ||
        ep7rec_get(BRACKET_FRAMES) != 0 || !selected_single_drive(drive)) {
        ep7rec_status = REC_MODE;
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
            ep7rec_status = REC_TRIGGER;
            return 1;
        }
    }

    ep7rec_status = REC_PROPERTIES;
    if (restore_capture_settings())
        ep7rec_owner = 0;
    return 0;
}

void ep7rec_end(uint32_t owner)
{
    if (!ep7rec_owner || ep7rec_owner != owner)
        return;
    if (release_queued) {
        ep7rec_unlatch_release(RELEASE_DOWN_HISTORY);
        ep7rec_full_release(owner, CLEAR_FULL_RELEASE);
        if (ep7rec_get_release_event() == FULL_PRESS_EVENT)
            ep7rec_set_release_event(previous_release_event);
        release_queued = 0;
    }
    if (!effective_settings_available() || !restore_capture_settings())
        return;

    ep7rec_owner = 0;
    ep7rec_publish_sequence(ep7rec_judge_sequence(owner));
    ep7rec_status = REC_CLEANED;
}

void ep7rec_after_standby_guard(uint32_t owner)
{
    if (ep7rec_owner != owner)
        return;
    if (selector(owner, SHOOTING_NEXT) != READY) {
        ep7rec_end(owner);
        return;
    }
    /* Same pending half/full request as native ctrlRelease's immediate-shot
     * path. The silent burst also uses the native Trig2KeyIn event kind
     * when it chooses the exposure count. */
    previous_release_event = ep7rec_get_release_event();
    ep7rec_set_release_event(FULL_PRESS_EVENT);
    ep7rec_latch_release(RELEASE_DOWN_HISTORY);
    ep7rec_full_release(owner, SET_FULL_RELEASE);
    release_queued = 1;
    ep7rec_status = REC_RELEASE_QUEUED;
}

void ep7rec_on_trigger_reset(uint32_t owner)
{
    /* The normal exit from STANDBY clears the native trigger mask before
     * entering READY. This reset is part of starting the Rec sequence. */
    if (ep7rec_owner == owner && release_queued &&
        selector(owner, SHOOTING_CURRENT) == STANDBY && selector(owner, SHOOTING_NEXT) == READY)
        return;
    ep7rec_end(owner);
}
