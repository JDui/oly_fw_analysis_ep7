/* E-P7 build 1100. The existing native allocators delimit each identity.
 * A settings read is permitted only before submission. Each following owner
 * receives an immutable copy, including the native temporary image clone. */
#include "single_dr.h"

#define ENGINE 0x6223d8a0u
#define CURRENT_COMMAND 0x6223d414u
#define METADATA_POOL 0x6223e450u
#define METADATA_COUNT 4u
#define METADATA_SIZE 96u
#define CAPTURE_REGISTRY 0x6223d178u
#define CAPTURE_POOL 0xaf6037c0u
#define CAPTURE_COUNT 25u
#define CAPTURE_SIZE 41984u
#define CLONE_OWNER 0x622933dcu
#define STILL_JOB_CALLBACK 0x603e7b83u

struct metadata_owner {
    uint32_t generation;
    uint32_t command;
    uint32_t capture;
    uint32_t capture_id;
    uint32_t capture_epoch;
    uint32_t plan;
    uint32_t applied;
};

struct capture_owner {
    uint32_t epoch;
    uint32_t plan;
    uint32_t public_mode;
    uint32_t nominal_sv;
};

/* Placed in the uncached alias by the experimental linker. The controller
 * claims/submits/consumes metadata. The native allocator clears image state
 * before publishing a slot. The ISP queue carries jobs after construction. */
static volatile struct metadata_owner metadata_owners[METADATA_COUNT];
static volatile struct capture_owner capture_owners[CAPTURE_COUNT];
static volatile uint32_t clone_owner;
static volatile uint32_t clone_plan;
static volatile uint32_t clone_frozen_format;

static uint32_t word(uint32_t p)
{
    return *(const volatile uint32_t *)(uintptr_t)p;
}

static uint32_t half(uint32_t p)
{
    return *(const volatile uint16_t *)(uintptr_t)p;
}

static uint32_t byte(uint32_t p)
{
    return *(const volatile uint8_t *)(uintptr_t)p;
}

static uint32_t uncached(uint32_t p)
{
    uint32_t region = p & 0xe0000000u;
    if (region != 0x60000000u && region != 0xa0000000u)
        return 0;
    return (p & 0x1fffffffu) | 0xa0000000u;
}

static volatile struct metadata_owner *metadata_owner(uint32_t metadata)
{
    if (metadata < METADATA_POOL || metadata - METADATA_POOL >=
        METADATA_COUNT * METADATA_SIZE ||
        (metadata - METADATA_POOL) % METADATA_SIZE ||
        byte(metadata + 92u) != 1u ||
        byte(metadata + 93u) != (metadata - METADATA_POOL) / METADATA_SIZE)
        return 0;
    return &metadata_owners[(metadata - METADATA_POOL) / METADATA_SIZE];
}

static volatile struct capture_owner *capture_owner(uint32_t capture)
{
    uint32_t p = uncached(capture);
    if (p < CAPTURE_POOL || p - CAPTURE_POOL >= CAPTURE_COUNT * CAPTURE_SIZE ||
        (p - CAPTURE_POOL) % CAPTURE_SIZE)
        return 0;
    return &capture_owners[(p - CAPTURE_POOL) / CAPTURE_SIZE];
}

static uint32_t registered_capture(uint32_t id)
{
    if (id < 1u || id > CAPTURE_COUNT)
        return 0;
    uint32_t entry = CAPTURE_REGISTRY + id * 24u;
    if (!(half(entry) & 4u))
        return 0;
    return uncached(word(entry + 12u));
}

void ep7dr_reset_metadata(uint32_t metadata)
{
    volatile struct metadata_owner *owner = metadata_owner(metadata);
    if (!owner)
        return;
    owner->plan = 0;
    owner->applied = 0;
    owner->command = 0;
    owner->generation = (owner->generation + 4u) & ~3u;
}

void ep7dr_claim_capture(uint32_t capture)
{
    volatile struct capture_owner *owner = capture_owner(capture);
    if (!owner)
        return;
    owner->plan = 0;
    owner->public_mode = 0;
    owner->epoch = (owner->epoch + 2u) | 1u;
}

void ep7dr_release_capture(uint32_t capture)
{
    volatile struct capture_owner *owner = capture_owner(capture);
    if (!owner)
        return;
    owner->epoch &= ~1u;
    owner->plan = 0;
    owner->public_mode = 0;
}

void ep7dr_freeze_plan(uint32_t command, uint32_t engine)
{
    if (!command || command != word(CURRENT_COMMAND) || engine != ENGINE)
        return;
    uint32_t metadata = word(command + 60u);
    volatile struct metadata_owner *owner = metadata_owner(metadata);
    if (!owner || metadata != word(engine + 4u) || !owner->generation ||
        owner->command)
        return;
    owner->command = command;
    uint32_t id = word(command);
    uint32_t capture = registered_capture(id);
    volatile struct capture_owner *image = capture_owner(capture);
    if (!image || !(image->epoch & 1u) || image->public_mode)
        return;
    uint32_t mode = 0;
    uint32_t level = ep7dr_select_scoped_level(command, engine, &mode);
    if (level < 1u || level > 2u ||
        (mode != 1u && mode != 54u && mode != 55u && mode != 56u && mode != 64u))
        return;
    int32_t fixed_iso = ep7dr_stock_key(0x810au);
    if (!ep7dr_fixed_nominal_admissible(fixed_iso, level) ||
        (uint32_t)fixed_iso != half(metadata + 8u))
        return;
    owner->capture = capture;
    owner->capture_id = id;
    owner->capture_epoch = image->epoch;
    /* Capture population may begin as soon as the native queue accepts the
     * request. Its settings freeze must precede the worker's gain decision. */
    image->nominal_sv = (uint32_t)fixed_iso;
    image->public_mode = mode;
    owner->plan = owner->generation | level;
}

uint32_t ep7dr_plan_for_metadata(uint32_t metadata)
{
    volatile struct metadata_owner *owner = metadata_owner(metadata);
    if (!owner)
        return 0;
    uint32_t plan = owner->plan;
    uint32_t command = owner->command;
    if (!plan || (plan & ~3u) != owner->generation || !command ||
        command != word(CURRENT_COMMAND) || metadata != word(command + 60u) ||
        owner->capture_id != word(command) ||
        owner->capture != registered_capture(owner->capture_id))
        return 0;
    volatile struct capture_owner *image = capture_owner(owner->capture);
    if (!image || image->epoch != owner->capture_epoch)
        return 0;
    return plan;
}

uint32_t ep7dr_record_applied(uint32_t metadata, uint32_t plan)
{
    if (!plan || ep7dr_plan_for_metadata(metadata) != plan)
        return 0;
    volatile struct metadata_owner *owner = metadata_owner(metadata);
    if (!owner || owner->plan != plan)
        return 0;
    volatile struct capture_owner *image = capture_owner(owner->capture);
    uint32_t pending = EP7DR_CAPTURE_PENDING | (plan & 3u);
    if (!image || image->epoch != owner->capture_epoch ||
        (image->plan && image->plan != pending))
        return 0;
    /* Establish the image obligation before the native TG handoff. If the
     * selected event loses its join, the converter sees pending, never OFF. */
    image->plan = pending;
    owner->applied = plan;
    return 1;
}

void ep7dr_reject_plan(uint32_t metadata, uint32_t plan)
{
    volatile struct metadata_owner *owner = metadata_owner(metadata);
    if (owner && plan && owner->plan == plan) {
        owner->plan = 0;
        owner->applied = 0;
    }
}

static void publish_capture_result(uint32_t command)
{
    if (!command || command != word(CURRENT_COMMAND))
        return;
    uint32_t metadata = word(command + 60u);
    uint32_t plan = ep7dr_plan_for_metadata(metadata);
    if (!plan)
        return;
    volatile struct metadata_owner *owner = metadata_owner(metadata);
    if (!owner || owner->applied != plan)
        return;
    volatile struct capture_owner *image = capture_owner(owner->capture);
    if (image && image->epoch == owner->capture_epoch &&
        image->plan == (EP7DR_CAPTURE_PENDING | (plan & 3u)))
        image->plan = plan & 3u;
}

void ep7dr_capture_result(uint32_t node, uint32_t command)
{
    if (node && command && command == word(CURRENT_COMMAND) &&
        word(node) == word(command))
        publish_capture_result(command);
}

/* StlTake's registered result callback uses the command ID, with no node.
 * Its native metadata writer selects this exact owner when dd48/dabc are 0. */
void ep7dr_still_result(uint32_t command)
{
    if (!byte(0x6223dd48u) && !byte(0x6223dabcu))
        publish_capture_result(command);
}

static uint32_t capture_plan(uint32_t source)
{
    volatile struct capture_owner *image = capture_owner(source);
    if (image)
        return image->epoch & 1u ? image->plan : 0;
    uint32_t p = uncached(source);
    if (p && p == clone_owner && p == uncached(word(CLONE_OWNER)))
        return clone_plan;
    return 0;
}

int ep7dr_capture_key(uint32_t capture, uint32_t key)
{
    volatile struct capture_owner *image = capture_owner(capture);
    if (!image) {
        uint32_t p = uncached(capture);
        if (key == 0x52b1u && p && p == clone_owner &&
            p == uncached(word(CLONE_OWNER)) && clone_frozen_format)
            return 0;
        return -1;
    }
    if (!(image->epoch & 1u) || !image->public_mode)
        return -1;
    switch (key) {
    case 0x810au: return (int)image->nominal_sv;
    case 0x8141u: return 1; /* Ordinary JPEG recipe */
    case 0x8231u:
    case 0x52b1u:
    case 0x69b9u:
    case 0x8eb9u:
    case 0x9961u:
    case 0xe911u:
    case 0xeee1u: return 0;
    case 0x9481u: return image->public_mode == 1u ? 2 : 11;
    case 0xf6b1u:
        if (image->public_mode == 64u)
            return 4;
        return image->public_mode >= 54u && image->public_mode <= 56u ?
            (int)image->public_mode - 53 : -1;
    default: return -1;
    }
}

void ep7dr_capture_clone(uint32_t destination, uint32_t source)
{
    uint32_t plan = capture_plan(source);
    clone_owner = 0;
    clone_plan = plan;
    volatile struct capture_owner *image = capture_owner(source);
    clone_frozen_format = image && (image->epoch & 1u) && image->public_mode;
    clone_owner = uncached(destination);
}

void ep7dr_release_clone(void)
{
    clone_owner = 0;
    clone_plan = 0;
    clone_frozen_format = 0;
}

uint32_t ep7dr_development_plan(uint32_t descriptor)
{
    return capture_plan(word(descriptor + 28u));
}

uint32_t ep7dr_bind_job(uint32_t descriptor, uint32_t plan)
{
    uint32_t job = word(descriptor + 36u);
    if (!job || word(job + 4u) != STILL_JOB_CALLBACK)
        return plan != 0;
    *(volatile uint32_t *)(uintptr_t)(job + EP7DR_JOB_TRAILER) = plan;
    return plan && ((plan & EP7DR_CAPTURE_PENDING) ||
                    half(descriptor + 194u) != 0x2001u ||
                    !ep7dr_gamma_schedule_ready(job));
}

/* Called by the embedded-request validator after proving the native job
 * callback, live stage and operation backlinks. The common constructor
 * allocates and clears this trailer for every member of that job family. */
uint32_t ep7dr_job_level(uint32_t job)
{
    return word(job + EP7DR_JOB_TRAILER) & 3u;
}

void ep7dr_job_gamma_applied(uint32_t job)
{
    volatile uint32_t *trailer =
        (volatile uint32_t *)(uintptr_t)(job + EP7DR_JOB_TRAILER);
    *trailer |= EP7DR_JOB_GAMMA_APPLIED;
}

void ep7dr_job_gamma_clear(uint32_t job)
{
    volatile uint32_t *trailer =
        (volatile uint32_t *)(uintptr_t)(job + EP7DR_JOB_TRAILER);
    *trailer &= ~EP7DR_JOB_GAMMA_APPLIED;
}

uint32_t ep7dr_job_gamma_missing(uint32_t job)
{
    uint32_t trailer = word(job + EP7DR_JOB_TRAILER);
    return (trailer & 3u) && !(trailer & EP7DR_JOB_GAMMA_APPLIED);
}
