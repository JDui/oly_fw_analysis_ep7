"""Host-only E-P7 H1 storage-format design, not a firmware/bank writer.

Format attribution: upstream PEN-F settings.s (H1, 0x4831CCVV).
E-P7 alternate cells are u32, but S-part1 ownership/durability is NOT qualified.
The -7..7 format range is not an E-P7 pixel calibration or safe patch claim.
"""
PROFILE_BASES = {54: 927, 55: 939, 56: 951, 64: 1655}
TAG = 0x4831

def property_id(public_mode, sector):
    if type(public_mode) is not int or public_mode not in PROFILE_BASES:
        raise ValueError('only four exact COLOR modes are modeled')
    if type(sector) is not int or not 0 <= sector < 12:
        raise ValueError('sector must be 0..11')
    return PROFILE_BASES[public_mode] + sector

def profile_sector(setting_id):
    if type(setting_id) is not int:
        raise ValueError('integer setting ID required')
    for mode, base in PROFILE_BASES.items():
        if base <= setting_id < base + 12:
            return mode, setting_id - base
    raise ValueError('not one of the 48 E-P7 profile S IDs')

def _axis(value):
    if type(value) is not int or not -7 <= value <= 7:
        raise ValueError('H1 axis must be integer -7..7')
    return value & 15

def encode(hue, luminance):
    packed = _axis(hue) | (_axis(luminance) << 4)
    return (TAG << 16) | ((packed ^ 255) << 8) | packed

def decode(cell):
    """Invalid/missing/stock-reset format is neutral, not an accepted H1 cell."""
    if type(cell) is not int or not 0 <= cell <= 0xffffffff or cell >> 16 != TAG:
        return (0, 0)
    packed = cell & 255
    if ((cell >> 8) & 255) != packed ^ 255:
        return (0, 0)
    h, l = packed & 15, packed >> 4
    h = h - 16 if h & 8 else h
    l = l - 16 if l & 8 else l
    return (h, l) if -7 <= h <= 7 and -7 <= l <= 7 else (0, 0)

def edit_axis(cell, setting_id, axis, value):
    """Return a proposed word only. Never opens files/devices or writes a bank."""
    profile_sector(setting_id)
    _axis(value)
    h, l = decode(cell)
    if axis == 'hue': h = value
    elif axis == 'luminance': l = value
    else: raise ValueError('axis must be hue or luminance')
    return encode(h, l)

def candidate_index(public_mode, sector, bank=None):
    """Modeled u32-cell index, not an authorized writable address."""
    pid = property_id(public_mode, sector)
    if bank is not None and (type(bank) is not int or not 0 <= bank < 9):
        raise ValueError('nine internal slots only; not nine user custom modes')
    return 1769 + pid + (0 if bank is None else bank * 3538)
