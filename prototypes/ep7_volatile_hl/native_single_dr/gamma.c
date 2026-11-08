/* E-P7 1100, ordinary still development only. The producer qualifies the
 * route before applying gain. The job owner proves the extension's extent. */
#include "single_dr.h"
#include <stdint.h>

#define REQUEST_OFFSET 11364u
#define OPERATION_OFFSET 14576u
#define OPERATION_SIZE 56u
#define OPERATION_COUNT 16u

struct gamma_row {
    uint32_t native;
    uint16_t values[2][256];
};

#include "single_dr_gamma_tables.inc"

static uint32_t word(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static const unsigned char *request_job(const unsigned char *request)
{
    const uintptr_t address = (uintptr_t)request;
    const uint32_t trailer_span = EP7DR_JOB_TRAILER - REQUEST_OFFSET + 3u;
    if (address <= REQUEST_OFFSET || address > UINT32_MAX - trailer_span || (address & 3u) ||
        word(request) != 0x60355fd4u)
        return 0;

    const uintptr_t job = address - REQUEST_OFFSET;
    const uintptr_t operation = word(request + 4);
    const uintptr_t first = job + OPERATION_OFFSET;
    if (operation < first || operation - first >= OPERATION_COUNT * OPERATION_SIZE ||
        (operation - first) % OPERATION_SIZE)
        return 0;
    const unsigned char *op = (const unsigned char *)operation;
    if (word(op) != job || word(op + 8) != address)
        return 0;
    const unsigned char *body = (const unsigned char *)job;
    return word(body + 4) == 0x603e7b83u ? body : 0;
}

uint32_t ep7dr_gamma_schedule_ready(uint32_t job)
{
    const unsigned char *body = (const unsigned char *)job;
    const unsigned char *stages = body + 10984u;
    const uint32_t count = word(body + 11312u);
    return (count == 0x00030000u ||
            (count == 0x00040000u && word(stages + 36) == 0x60356116u &&
             !word(stages + 40))) &&
           word(stages) == 0x603687d4u && !word(stages + 4) &&
           word(stages + 12) == 0x603687edu && !word(stages + 16) &&
           word(stages + 24) == 0x6036884du && !word(stages + 28) &&
           !body[11338] && !body[11339] && !body[11340];
}

static uint32_t processing_stage(const unsigned char *job)
{
    const uint32_t stage = word(job + 11312u);
    return stage == 0x00030002u || stage == 0x00040002u;
}

void ep7dr_gamma_config_begin(const unsigned char *request)
{
    const unsigned char *job = request_job(request);
    if (job && processing_stage(job) && ep7dr_job_level((uintptr_t)job))
        ep7dr_job_gamma_clear((uintptr_t)job);
}

uint32_t ep7dr_gamma_config_missing(const unsigned char *request)
{
    const unsigned char *job = request_job(request);
    return job && processing_stage(job) && ep7dr_job_gamma_missing((uintptr_t)job);
}

uint32_t ep7dr_gamma_bypass_pending(const unsigned char *request)
{
    const unsigned char *job = request_job(request);
    return job && processing_stage(job) && ep7dr_job_level((uintptr_t)job);
}

uint32_t ep7dr_gamma_stage_missing(const unsigned char *job)
{
    return word(job + 4) == 0x603e7b83u && processing_stage(job) &&
           ep7dr_job_gamma_missing((uintptr_t)job);
}

uint32_t ep7dr_gamma_output_missing(const unsigned char *descriptor)
{
    if (descriptor[194] != 1 || descriptor[195] != 0x20)
        return 0;
    const uintptr_t job = word(descriptor + 36);
    return job && word((const unsigned char *)job + 4) == 0x603e7b83u &&
           ep7dr_job_gamma_missing(job);
}

void ep7dr_gamma_apply(const unsigned char *request, uint32_t rgb[3])
{
    const unsigned char *job = request_job(request);
    if (!job)
        return;

    /* The outer kind19/0x2001 command is not an ISP request type or stage. */
    const uint32_t key = word(request + 8);
    if ((key != 0x00020000u && key != 0x000b0000u) || request[16] != 0 ||
        (request[29] != 1 && request[29] != 2) ||
        word(request + 1524) != 0 || request[1797] || request[1808] ||
        request[1809] || request[1838] || request[1839] || request[1879] ||
        !processing_stage(job) ||
        word(job + 11008u) != 0x6036884du || word(job + 11012u))
        return;

    /* This call owns the allocated-extent and capture-publication check.
     * The embedded request's shape alone does not authorize a trailer read. */
    const uint32_t level = ep7dr_job_level((uintptr_t)job);
    if (level < 1 || level > 2 || rgb[0] != rgb[1] || rgb[0] != rgb[2])
        return;

    for (unsigned row = 0; row < sizeof gamma_rows / sizeof gamma_rows[0]; ++row) {
        if (gamma_rows[row].native == rgb[0]) {
            const uint32_t table = (uintptr_t)gamma_rows[row].values[level - 1];
            rgb[0] = table;
            rgb[1] = table;
            rgb[2] = table;
            ep7dr_job_gamma_applied((uintptr_t)job);
            return;
        }
    }
}
