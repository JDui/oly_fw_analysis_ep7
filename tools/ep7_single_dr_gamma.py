#!/usr/bin/env python3
"""Generate offline HDR gamma tables from E-P7 1100 normal-gradation ROM curves.

The input model is an ideal 2x or 4x reduction in linear RGB before gamma.
This tool neither modifies the source image nor binds an ISP or sensor hook.
"""

import argparse
import json
from pathlib import Path
import struct


BASE = 0x60020020
ROM_ROW = 0x60530B6C
ROM_POINTERS = (
    0x604EDE78, 0x604EE078, 0x604EDE78, 0x604F3E78,
    0x604EDE78, 0x604EE078, 0x604EDE78, 0x604EE078,
)
GAMMA = struct.Struct('<256H')
GAIN = (1, 2, 4)
WHITE = 4095
NOMINAL_KNEE = 32


def gamma_table(stock_image: bytes, stock_pointer: int, level: int) -> bytes:
    """Return an immutable little-endian table for level 0 (OFF), 1 or 2."""
    if len(stock_image) != 26214336:
        raise ValueError('expected an E-P7 1100 decoded main component')
    if struct.unpack_from('<8I', stock_image, ROM_ROW - BASE) != ROM_POINTERS:
        raise ValueError('unexpected stock normal-gradation RGB pointer row')
    if stock_pointer not in ROM_POINTERS or level not in (0, 1, 2):
        raise ValueError('unsupported stock gamma pointer or HDR level')

    offset = stock_pointer - BASE
    original = stock_image[offset:offset + GAMMA.size]
    stock = GAMMA.unpack(original)
    if stock[0] != 0 or stock[-1] != WHITE or any(a > b for a, b in zip(stock, stock[1:])):
        raise ValueError('stock gamma samples are not monotone between native endpoints')
    if level == 0:
        return original

    gain = GAIN[level]
    knee_index = NOMINAL_KNEE // gain
    knee_code = stock[NOMINAL_KNEE]
    incoming = knee_code - stock[NOMINAL_KNEE - gain]
    span = len(stock) - 1 - knee_index

    # Keep one code per remaining knot as a linear ramp. Allocate the rest
    # to a rational shoulder whose initial slope matches the incoming ramp.
    # This keeps the shoulder strictly increasing even after quantization.
    budget = WHITE - knee_code - span
    slope_scale = span * (incoming - 1)
    if not 0 < budget < slope_scale:
        raise ValueError('stock gamma knee does not admit the prototype shoulder')

    values = list(stock[:NOMINAL_KNEE + 1:gain])
    for step in range(1, span + 1):
        denominator = budget * span + (slope_scale - budget) * step
        compressed = (budget * step * slope_scale + denominator // 2) // denominator
        values.append(knee_code + step + compressed)
    return GAMMA.pack(*values)


def inspect(stock_image: bytes) -> list[dict]:
    """Check the stock copy, grey anchor and top-end range for all six LUTs."""
    rows = []
    for stock_pointer in dict.fromkeys(ROM_POINTERS):
        offset = stock_pointer - BASE
        off = gamma_table(stock_image, stock_pointer, 0)
        if off != stock_image[offset:offset + GAMMA.size]:
            raise ValueError('OFF changed stock gamma bytes')
        stock = GAMMA.unpack(off)
        stock_white = stock.index(WHITE)
        for level, gain in enumerate(GAIN[1:], start=1):
            samples = GAMMA.unpack(gamma_table(stock_image, stock_pointer, level))
            knee = NOMINAL_KNEE // gain
            if samples[:knee + 1] != stock[:NOMINAL_KNEE + 1:gain]:
                raise ValueError('compensated gamma changed the anchored midtone range')
            if samples[0] != 0 or samples[-1] != WHITE or any(
                a >= b for a, b in zip(samples[knee:], samples[knee + 1:])
            ):
                raise ValueError('compensated gamma shoulder is not strictly rising to white')
            old_white_index = (stock_white + gain - 1) // gain
            rows.append(dict(
                stock_pointer=f'0x{stock_pointer:08x}', level=level, assumed_gain_ratio=gain,
                knee_index=knee, knee_code=samples[knee], stock_white_index=stock_white,
                hdr_white_index=samples.index(WHITE),
                code_span_above_old_white=WHITE - samples[old_white_index],
            ))
    return rows


def target_table_source(stock_image: bytes) -> str:
    """Return the target-only include generated from the local stock image."""
    lines = ['/* Generated locally by ep7_single_dr_gamma.py. */',
             'static const struct gamma_row gamma_rows[] = {']
    for address in dict.fromkeys(ROM_POINTERS):
        lines.append(f'    {{0x{address:08x}u, {{')
        for level in (1, 2):
            samples = GAMMA.unpack(gamma_table(stock_image, address, level))
            lines.append('        {')
            for start in range(0, len(samples), 16):
                lines.append('            ' + ', '.join(map(str, samples[start:start + 16])) + ',')
            lines.append('        },')
        lines.append('    }},')
    lines.append('};')
    return '\n'.join(lines) + '\n'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock_main', type=Path, help='locally decoded stock main component')
    parser.add_argument('--emit-c', action='store_true', help='print the target gamma table include')
    args = parser.parse_args()
    stock_image = args.stock_main.read_bytes()
    if args.emit_c:
        print(target_table_source(stock_image), end='')
    else:
        print(json.dumps(dict(status='offline_model_only', tables=inspect(stock_image)), indent=2))


if __name__ == '__main__':
    main()
