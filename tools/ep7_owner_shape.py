"""Host-only E-P7 1100 embedded request/operation shape checks.

No firmware, camera, memory or pointer is read. Values are supplied observations
or synthetic fixtures. Matching shape does NOT prove allocation validity,
generation, liveness, completion, supported image mode or safe H/L access.
External/nonembedded request paths are deliberately rejected.
"""
JOB_BYTES = 15488
REQUEST_OFFSET = 11364
OPERATION_OFFSET = 14576
OPERATION_STRIDE = 56
OPERATION_COUNT = 16
CALLBACK = 0x60355fd4


def embedded_operation_index(*, job, request, operation, request_callback,
                             request_operation, operation_job, operation_request):
    """Return the matched slot index, or None. Never dereference an address."""
    values = (job, request, operation, request_callback, request_operation,
              operation_job, operation_request)
    if any(type(value) is not int or not 0 <= value < 2**32 for value in values):
        return None
    if job == 0 or job % 4 or job + JOB_BYTES > 2**32:
        return None
    if request != job + REQUEST_OFFSET or request_callback != CALLBACK:
        return None
    offset = operation - job - OPERATION_OFFSET
    if offset < 0 or offset % OPERATION_STRIDE:
        return None
    index = offset // OPERATION_STRIDE
    if index >= OPERATION_COUNT:
        return None
    if request_operation != operation or operation_job != job or operation_request != request:
        return None
    return index
