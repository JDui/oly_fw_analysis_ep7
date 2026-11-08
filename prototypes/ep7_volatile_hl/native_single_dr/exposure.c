/* E-P7 1100 ordinary STILL gain admission. The native code owns the
 * actual gain calculation and TG command. This code qualifies its input. */
#include "single_dr.h"

#define ENGINE 0x6223d8a0u
#define CURRENT_COMMAND 0x6223d414u
#define METADATA_POOL 0x6223e450u
#define STILL_CALIBRATION 0x621f3ff4u
#define STILL_MODE 10u

extern uint32_t ep7dr_stock_exp2_q12(int32_t exponent);

static uint32_t word(uint32_t address)
{
    return *(const volatile uint32_t *)(uintptr_t)address;
}

static uint16_t half(uint32_t address)
{
    return *(const volatile uint16_t *)(uintptr_t)address;
}

uint32_t ep7dr_exposure_metadata(uint32_t lower, uint32_t context)
{
    if (!lower || !context)
        return 0;
    uint32_t request = word(context);
    if (!request || half(request) != 8u || half(request + 2u) != 7u ||
        word(request + 12u) != ENGINE + 4u || word(context + 4u) != lower ||
        word(lower + 4u) != STILL_MODE)
        return 0;

    uint32_t metadata = word(ENGINE + 4u);
    if (metadata < METADATA_POOL || metadata - METADATA_POOL >= 4u * 96u ||
        (metadata - METADATA_POOL) % 96u)
        return 0;

    uint32_t current = word(CURRENT_COMMAND);
    uint32_t copy = word(context + 12u);
    if (!current || word(current + 60u) != metadata ||
        !copy || word(lower + 20u) != copy || copy == metadata ||
        half(copy + 4u) != 1u ||
        half(copy + 6u) != half(metadata + 6u) ||
        half(copy + 8u) != half(metadata + 8u) ||
        half(copy + 10u) != half(metadata + 10u) ||
        word(copy + 32u) || half(copy + 44u) || (word(copy) & 0x80u))
        return 0;
    return metadata;
}

static int32_t calibrated_q16(const volatile int16_t *table, unsigned sv)
{
    unsigned index = (sv - 1024u) >> 8;
    int32_t low = table[index];
    int32_t high = table[index + 1u];
    return low * 256 + (high - low) * (int32_t)(sv & 255u);
}

/* Replicate the range and Q12 packing used by 6012f401/6012f474 only
 * for validation. The real request will still run these original functions. */
static uint32_t gain_code(int32_t calibration)
{
    uint32_t gain = ep7dr_stock_exp2_q12(-((calibration / 20) >> 4));
    return (16773120u - 4095u * gain) >> 12;
}

/* Return expected TG code in the high half and candidate work Sv in the low
 * half. A zero result leaves the entire original command path in force. */
uint32_t ep7dr_exposure_target(uint32_t nominal, uint32_t plan)
{
    unsigned level = plan & 3u;
    if (!ep7dr_fixed_nominal_admissible((int32_t)nominal, level))
        return 0;

    uint32_t address = word(STILL_CALIBRATION);
    if ((address & 1u) ||
        !((address >= 0x60020020u && address <= 0x6279687cu) ||
          (address >= 0xa0000000u && address <= 0xa279687cu)))
        return 0;

    const volatile int16_t *table = (const volatile int16_t *)(uintptr_t)address;
    unsigned target = nominal - 256u * level;
    int32_t lower = calibrated_q16(table, target);
    int32_t upper = calibrated_q16(table, nominal);
    int32_t difference = upper - lower - (int32_t)level * 1541 * 256;
    if (lower < 0 || upper > 1577984 || difference < -256 || difference > 256)
        return 0;

    uint32_t before = gain_code(upper);
    uint32_t after = gain_code(lower);
    if (before > 3839u || after >= before)
        return 0;

    int32_t ratio_error = (int32_t)(4095u - after) -
                          (int32_t)((4095u - before) << level);
    if (ratio_error < -8 || ratio_error > 8)
        return 0;
    return after << 16 | target;
}
