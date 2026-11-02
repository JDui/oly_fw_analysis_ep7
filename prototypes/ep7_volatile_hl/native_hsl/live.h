#ifndef EP7_NATIVE_HSL_LIVE_H
#define EP7_NATIVE_HSL_LIVE_H
#include <stdint.h>

/* The existing native five-slot lifetime owns each frozen H/L row. */
void ep7h_live_sample(uintptr_t owner);
void ep7h_live_to_job(uintptr_t owner,uintptr_t job);
#endif
