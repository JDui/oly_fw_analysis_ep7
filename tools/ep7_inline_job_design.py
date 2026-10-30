"""Pure host design fixture, NOT an allocator, firmware probe or usable pointer API.

An opaque allocation ticket represents a hypothetical independently qualified
constructor path. Issuing it here is a simulation assumption, not camera evidence.
Shape observations never mint tickets. No firmware/memory/device access occurs.
"""
from dataclasses import dataclass

STOCK_BYTES = 15488
TRAILER_BYTES = 24
EXPANDED_BYTES = STOCK_BYTES + TRAILER_BYTES
REQUEST_OFFSET = 11364
OP_OFFSET = 14576
OP_STRIDE = 56
CALLBACK = 0x60355fd4


class Rejected(ValueError):
    pass


@dataclass(frozen=True)
class Snapshot:
    """Capture-time values, not a pointer back into UI/capture storage.

    capture_label is fixture bookkeeping, NOT a proven firmware generation.
    Units/ranges of actual E-P7 H/L remain unqualified.
    """
    capture_label: str
    values: tuple

    def __post_init__(self):
        if not isinstance(self.capture_label, str) or not self.capture_label:
            raise Rejected('fixture capture identity required')
        if type(self.values) is not tuple or len(self.values) != TRAILER_BYTES:
            raise Rejected('exactly 24 immutable scalar values required')
        if any(type(v) is not int or not -128 <= v <= 127 for v in self.values):
            raise Rejected('synthetic signed-byte representation only')


@dataclass(frozen=True)
class Shape:
    job: int
    request: int
    operation: int
    callback: int
    request_operation: int
    operation_job: int
    operation_request: int


def shape_for(job, slot):
    if type(slot) is not int or not 0 <= slot < 16:
        raise Rejected('slot outside fixture')
    request = job + REQUEST_OFFSET
    operation = job + OP_OFFSET + OP_STRIDE * slot
    return Shape(job, request, operation, CALLBACK, operation, job, request)


def slot_index(shape):
    """Shape alone establishes neither extent nor lifetime."""
    if not isinstance(shape, Shape):
        raise Rejected('shape required')
    if any(type(v) is not int or not 0 <= v < 2**32 for v in vars(shape).values()):
        raise Rejected('invalid address-shaped fixture value')
    job = shape.job
    if not job or job % 4 or job + STOCK_BYTES > 2**32:
        raise Rejected('invalid job shape')
    offset = shape.operation - job - OP_OFFSET
    if offset < 0 or offset % OP_STRIDE or offset // OP_STRIDE >= 16:
        raise Rejected('operation membership mismatch')
    if (shape.request != job + REQUEST_OFFSET or shape.callback != CALLBACK or
            shape.request_operation != shape.operation or shape.operation_job != job or
            shape.operation_request != shape.request):
        raise Rejected('link mismatch')
    return offset // OP_STRIDE


@dataclass(frozen=True)
class Coefficients:
    """Scalar-only stand-in for native output; deliberately no pointer/ticket.

    This identity transform is NOT E-P7 coefficient math or pixel processing.
    """
    values: tuple


@dataclass
class _Allocation:
    address: int
    extent: int
    live: bool = True
    snapshot: object = None


class Fixture:
    """Single-threaded synthetic lifetime model, no concurrency qualification.

    Tickets, not matching addresses, distinguish reused synthetic allocations.
    Native feasibility of such pre-read provenance is an unresolved requirement.
    """
    def __init__(self):
        self._allocations = {}
        self._live_at = {}
        self.trailer_reads = 0

    def assume_qualified_allocation(self, address, extent=EXPANDED_BYTES, *, failed=False):
        """Explicit TEST ASSUMPTION: trusted constructor evidence, not derived shape."""
        if failed:
            return None
        if (type(address) is not int or not address or address % 4 or
                type(extent) is not int or extent < STOCK_BYTES or
                address < 0 or address + extent > 2**32 or address in self._live_at):
            raise Rejected('invalid synthetic allocation')
        if any(record.live and address < record.address + record.extent and
               record.address < address + extent for record in self._allocations.values()):
            raise Rejected('overlapping synthetic allocation')
        ticket = object()
        self._allocations[ticket] = _Allocation(address, extent)
        self._live_at[address] = ticket
        return ticket

    def _qualified(self, ticket, shape):
        slot_index(shape)  # This does not authorize the read.
        if type(ticket) is not object:
            raise Rejected('opaque fixture allocation ticket required')
        record = self._allocations.get(ticket)
        if (record is None or not record.live or record.address != shape.job or
                self._live_at.get(shape.job) is not ticket or record.extent < EXPANDED_BYTES):
            raise Rejected('no independent live expanded-allocation provenance')
        return record

    def initialize(self, ticket, shape, snapshot):
        record = self._qualified(ticket, shape)
        if type(snapshot) is not Snapshot or record.snapshot is not None:
            raise Rejected('immutable initialization required exactly once')
        record.snapshot = snapshot

    def clone_values(self, source_ticket, source_shape, destination_ticket, destination_shape):
        """Explicit snapshot transfer; never assume the native clone copy carries it."""
        source = self._qualified(source_ticket, source_shape)
        if source.snapshot is None:
            raise Rejected('source has no initialized snapshot')
        self.trailer_reads += 1  # Explicit value transfer is a qualified read too.
        copied = Snapshot(source.snapshot.capture_label, tuple(v for v in source.snapshot.values))
        self.initialize(destination_ticket, destination_shape, copied)

    def read_to_coefficients(self, ticket, shape):
        record = self._qualified(ticket, shape)
        if record.snapshot is None:
            raise Rejected('uninitialized trailer')
        # Simulated CPU reader; all provenance/lifetime/initialization gates precede it.
        self.trailer_reads += 1
        return Coefficients(tuple(v for v in record.snapshot.values))

    def release(self, ticket):
        record = self._allocations.get(ticket)
        if record is None or not record.live:
            raise Rejected('unknown/already released allocation')
        record.live = False
        record.snapshot = None
        del self._live_at[record.address]
