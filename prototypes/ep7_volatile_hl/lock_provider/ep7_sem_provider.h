#ifndef EP7_SEM_PROVIDER_H
#define EP7_SEM_PROVIDER_H
#include "ep7p.h"
#include <stdatomic.h>
/* Mockable normalized callbacks, NOT the camera ABI. Raw veneers unbound.
 * All callbacks return normally, do not reenter, and preserve output on failure.
 * Caller proves private-handle lifetime, supported task context and no migration.
 * Atomic implementation must be qualified before native deployment. */
typedef struct {
 void *ctx;
 int (*get_tid)(void *, uint16_t *);
 int (*wait_poll)(void *, uint16_t); /* raw timeout0, exact0 acquired */
 int (*signal)(void *, uint16_t); /* exact0 confirmed, anything else uncertain */
} ep7s_native;
enum { EP7S_READY, EP7S_BUSY, EP7S_POISON };
typedef struct {
 ep7s_native native; uint16_t handle, owner;
 atomic_uint state;
} ep7s_provider;
/* Once-before-publication, valid distinct objects. Does not create a semaphore.
 * Handle qualification is a trusted integration fact, not proved by its shape. */
bool ep7s_init(ep7s_provider *, ep7s_native, uint16_t private_handle);
ep7p_ops ep7s_ops(ep7s_provider *);
bool ep7s_poisoned(const ep7s_provider *);
#endif
