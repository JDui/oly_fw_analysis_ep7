/* Object-only GCC ABI witness: pointer result is read from a0 into integer d0. */
#include "worker.h"
uintptr_t ep7_probe_worker_allocation(unsigned size)
{ return (uintptr_t)ep7_gcc_job_allocate(size); }
