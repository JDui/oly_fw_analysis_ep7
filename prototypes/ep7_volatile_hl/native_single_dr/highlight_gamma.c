/* RGB pre-cache substitution only. Unqualified requests keep stock rendering. */
#include "single_dr.h"

struct gamma_row { uint32_t native; uint16_t values[2][256]; };
#include "single_dr_gamma_tables.inc"

static uint32_t word(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

void ep7dr_gamma_apply(const unsigned char *request, uint32_t rgb[3], unsigned selector_status)
{
    uintptr_t address = (uintptr_t)request;
    if (address <= 11364u || address > UINT32_MAX - 4151u || (address & 3u) ||
        word(request) != 0x60355fd4u)
        return;
    uintptr_t job = address - 11364u, first = job + 14576u;
    uintptr_t operation = word(request + 4);
    if (operation < first || operation - first >= 16u * 56u ||
        (operation - first) % 56u)
        return;
    const unsigned char *op = (const unsigned char *)operation;
    if (word(op) != job || word(op + 8) != address)
        return;
    const unsigned char *body = (const unsigned char *)job;
    uint32_t callback = word(body + 4);
    if (callback != 0x603e7b83u && callback != 0x60306ad5u)
        return;
    unsigned path = callback == 0x60306ad5u ? 0u : 1u;
    /* Only the COLOR1-4 source samplers can publish a nonzero level. The
     * native job constructor clears it and unsupported sources publish OFF.
     * The subsequent operation key is not the source profile: the same job
     * may build ordinary/borrowed processing requests with a different key.
     * Keep reciprocal ownership, pass type, flags and actual LUT qualification. */
    uint32_t level = word(body + EP7DR_JOB_TRAILER);
    if (level < 1u || level > 2u) {
        ep7dr_highlight_observe(path, 2, 0xd0u);
        return;
    }
    if (selector_status != 1u) {
        ep7dr_highlight_observe(path, 2, 0xc0u);
        return;
    }
    /* Native dispatcher 603aaced admits types 0 and 16 to the same COLOR
     * family-1/2 RGB builder. Type 3 is a later conversion, not this pass. */
    if (request[16] != 0 && request[16] != 16) {
        unsigned type = request[16];
        ep7dr_highlight_observe(path, 2, 0xe0u | (type < 15u ? type : 15u));
        return;
    }
    if (request[29] != 1 && request[29] != 2) {
        unsigned family = request[29];
        ep7dr_highlight_observe(path, 2, 0xf0u | (family < 15u ? family : 15u));
        return;
    }
    if (request[1797]) {
        ep7dr_highlight_observe(path, 2, 0xa0u);
        return;
    }
    if (request[1808] || request[1809] || request[1838] ||
        request[1839] || request[1879]) {
        ep7dr_highlight_observe(path, 2, 0xa1u);
        return;
    }
    if (rgb[0] != rgb[1] || rgb[0] != rgb[2]) {
        ep7dr_highlight_observe(path, 2, 0xb0u);
        return;
    }
    /* A nonzero request+1524 is an ordinary borrowed-table route. The stock
     * selector has already validated its variant and produced this tuple.
     * Match the immutable ROM tuple below; never modify the borrowed object. */
    for (unsigned row = 0; row < sizeof gamma_rows / sizeof gamma_rows[0]; ++row)
        if (gamma_rows[row].native == rgb[0]) {
            uint32_t table = (uintptr_t)gamma_rows[row].values[level - 1u];
            rgb[0] = rgb[1] = rgb[2] = table;
            /* High nibble identifies the key route. The low nibble encodes
             * the stock LUT row and level without growing the UI record. */
            ep7dr_highlight_observe(path, 2,
                (word(request + 8) == 0x000b0000u ? 0x40u : 0x70u) + 2u * row + level);
            return;
        }
    ep7dr_highlight_observe(path, 2, 0xb1u);
}
