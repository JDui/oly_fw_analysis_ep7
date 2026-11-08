/* Rendering-only transport, following the already installed 015 H/L owners.
 * There are no exposure tickets, sensor writes or forced capture failures. */
#include "single_dr.h"

static uint32_t capture_levels[25];
static uint32_t live_levels[5];
static uintptr_t clone_owner;
static uint32_t clone_level;
static volatile uint32_t observations[2][3];

void ep7dr_highlight_observe(unsigned path, unsigned stage, uint32_t code)
{
    if (path < 2u && stage < 3u)
        observations[path][stage] = code;
}

void ep7dr_highlight_clear_observations(void)
{
    for (unsigned path = 0; path < 2u; ++path)
        for (unsigned stage = 0; stage < 3u; ++stage)
            observations[path][stage] = 0;
}

uint32_t ep7dr_highlight_observation(unsigned path)
{
    if (path >= 2u)
        return 0;
    /* Diagnostic only: aligned independent stores, no control-path decisions.
     * A concurrent frame can appear during a UI reset; these are last observed
     * stages, not a completion receipt or proof that ISP pixels were rendered. */
    uint32_t sample = observations[path][0];
    if (sample >= 0x50u)
        return sample;
    uint32_t gamma = observations[path][2];
    uint32_t job = observations[path][1];
    return gamma ? gamma : job ? job : sample;
}

static uintptr_t uncached(uintptr_t p)
{
    uintptr_t region = p & 0xe0000000u;
    return region == 0x60000000u || region == 0xa0000000u ?
           (p & 0x1fffffffu) | 0xa0000000u : 0;
}

static uint32_t *capture_row(uintptr_t owner)
{
    uintptr_t p = uncached(owner);
    if (p >= 0xaf6037c0u && p - 0xaf6037c0u < 25u * 41984u &&
        (p - 0xaf6037c0u) % 41984u == 0)
        return &capture_levels[(p - 0xaf6037c0u) / 41984u];
    return p && p == clone_owner ? &clone_level : 0;
}

static uint32_t *live_row(uintptr_t owner)
{
    uintptr_t p = uncached(owner);
    return p >= 0xa2731098u && p - 0xa2731098u < 5u * 980u &&
           (p - 0xa2731098u) % 980u == 0 ?
           &live_levels[(p - 0xa2731098u) / 980u] : 0;
}

static int selected(unsigned mode, unsigned selector)
{
    unsigned public_mode;
    if (mode == 11u && selector >= 1u && selector <= 4u)
        public_mode = selector == 4u ? 64u : 53u + selector;
    else
        return -2;
    int level = ep7dr_selected_level(public_mode);
    return level >= 0 && level <= 2 ? level : -1;
}

static void sample_level(unsigned path, uint32_t *row, unsigned mode, unsigned selector)
{
    int level = selected(mode, selector);
    *row = level > 0 ? (uint32_t)level : 0;
    ep7dr_highlight_observe(path, 0, level == -1 ? 0x50u :
                           level == -2 ? 0x60u : 0x10u | (uint32_t)level);
}

void ep7dr_highlight_capture_sample(uintptr_t owner)
{
    uint32_t *row = capture_row(owner);
    if (!row) {
        ep7dr_highlight_observe(1, 0, 0x60u);
        return;
    }
    const volatile unsigned char *p = (const volatile unsigned char *)owner;
    sample_level(1, row, p[24053], p[24083]);
}

void ep7dr_highlight_capture_clone(uintptr_t destination, uintptr_t source)
{
    const uint32_t *row = capture_row(source);
    uint32_t value = row ? *row : 0;
    clone_owner = 0;
    clone_level = value;
    clone_owner = uncached(destination);
}

static void job_level(unsigned path, uintptr_t job, const uint32_t *row)
{
    if (job) {
        *(volatile uint32_t *)(job + EP7DR_JOB_TRAILER) = row ? *row : 0;
        ep7dr_highlight_observe(path, 1, row ? 0x20u | *row : 0x60u);
    }
}

void ep7dr_highlight_capture_to_job(uintptr_t owner, uintptr_t parameters)
{
    if (parameters >= 36u)
        job_level(1, parameters - 36u, capture_row(owner));
}

void ep7dr_highlight_live_sample(uintptr_t owner)
{
    uint32_t *row = live_row(owner);
    if (!row) {
        ep7dr_highlight_observe(0, 0, 0x60u);
        return;
    }
    const volatile unsigned char *p = (const volatile unsigned char *)uncached(owner);
    if (!(p[181] & 0x40u))
        sample_level(0, row, p[941], p[944]);
}

void ep7dr_highlight_live_to_job(uintptr_t owner, uintptr_t job)
{
    job_level(0, job, live_row(owner));
}

/* Uninstalled legacy capture-key veneers remain in the shared settings object.
 * They have no call sites in the rendering candidate and always defer. */
int ep7dr_capture_key(uint32_t capture, uint32_t key)
{
    (void)capture;
    (void)key;
    return -1;
}
