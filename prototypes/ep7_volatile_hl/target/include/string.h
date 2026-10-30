/* Self-authored freestanding declarations only. No implementation/linkage. */
#ifndef EP7_ABI_PROBE_STRING_H
#define EP7_ABI_PROBE_STRING_H
#include <stddef.h>
void *memcpy(void *, const void *, size_t);
void *memset(void *, int, size_t);
int memcmp(const void *, const void *, size_t);
#endif
