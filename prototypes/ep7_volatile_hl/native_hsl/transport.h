#ifndef EP7H_TRANSPORT_H
#define EP7H_TRANSPORT_H
#include <stdint.h>
/* Native owners and constructor-owned 24-byte job tail; no queue/runtime API. */
void ep7h_capture_sample(uintptr_t capture);
void ep7h_capture_clone(uintptr_t destination,uintptr_t source);
void ep7h_capture_to_job(uintptr_t capture,uintptr_t parameters);
void ep7h_transport_apply(const unsigned char *setup);
#endif
