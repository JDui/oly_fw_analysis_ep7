#ifndef EP7_COLD_BOOTSTRAP_H
#define EP7_COLD_BOOTSTRAP_H
#include <stdbool.h>
#include <stdint.h>
/* Resident early group only: never dereferences the later section6 UI tables.
 * Byte agreement does not establish RAM ownership, cache visibility or complete
 * task/lifetime closure. Those remain offline installation prerequisites. */
bool ep7r_native_early_cohort_present(void);
/* Read-only cold-context admission, after a valid domain0 Usr3 current-task
 * query in the same normally returning invocation. Does not disable task
 * exceptions, acquire a kernel lock or turn the observation into a TCB lease. */
bool ep7r_native_cold_context(uint32_t tcb);
/* Once, from the reviewed Usr3 CALL60191371, after private cold clear and before
 * starting the modified pipeline tasks. Failure does not return to stock boot.
 * The permanent core/boot/runtime objects are never moved, reset or unpublished. */
void ep7r_bootstrap_initialize(void);
#endif
