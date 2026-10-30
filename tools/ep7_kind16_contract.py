"""Host-only proposed guard for the verified kind16 selection branch.

This models selection operands, NOT native firmware execution. No offsets are written,
no firmware is loaded, and no generation/ownership guarantee is manufactured.
"""
from dataclasses import dataclass, field

class ContractError(ValueError):
    pass

def unsigned(value, bits, name):
    if type(value) is not int or not 0 <= value < (1 << bits):
        raise ContractError(f'{name} must be an unsigned {bits}-bit integer')
    return value

def capture_id(value):
    unsigned(value,32,'capture ID')
    if not 1 <= value <= 25:
        raise ContractError('capture registry ID must be 1..25')
    return value

def identity_slot(kind_class, value):
    """Separate domain from capture IDs; returns logical tuple, NOT RAM address."""
    unsigned(kind_class,8,'identity class')
    unsigned(value,32,'identity ID')
    if kind_class > 2 or not 1 <= value <= 27:
        raise ContractError('identity class must be 0..2 and ID 1..27')
    return kind_class,value

@dataclass(frozen=True)
class Selection:
    index: int
    capture_id: int
    identity: tuple
    requires_generation_qualification: bool = field(default=True, init=False)
    permits_firmware_use: bool = field(default=False, init=False)

def select_kind16(candidates, dispatch, *, initial_capture_marker=None):
    """Require 15 raw uint32 fields; unused fields may be zero.

    For0x100c, marker must be from the initially resolved first capture. This
    function cannot establish that provenance; callers must supply it explicitly.
    """
    if not isinstance(candidates,(list,tuple)) or len(candidates)!=15:
        raise ContractError('exactly15 candidate words required')
    words=tuple(unsigned(v,32,'candidate') for v in candidates)
    unsigned(dispatch,16,'dispatch')
    index=1 if dispatch in (0x1002,0x1005) else 0
    if dispatch==0x100c:
        capture_id(words[0]) # Native branch first resolves this pointer to read marker.
        if initial_capture_marker is None:
            raise ContractError('0x100c requires initial capture marker evidence')
        unsigned(initial_capture_marker,8,'initial capture marker')
        if initial_capture_marker==11:
            index=1
    selected=capture_id(words[index])
    return Selection(index,selected,identity_slot(0,selected))

@dataclass
class MetadataWindow:
    """Proposed conservative host contract; not a discovered firmware lease.

    ACK closes caller-metadata access even if processing iterations continue.
    A pre-ACK snapshot is data only: it is still not a generation-safe H/L lease.
    """
    acknowledged: bool=False

    def snapshot(self,candidates,dispatch,**kwargs):
        if self.acknowledged:
            raise ContractError('caller metadata unavailable after acknowledgement')
        return select_kind16(candidates,dispatch,**kwargs)

    def acknowledge(self):
        self.acknowledged=True
