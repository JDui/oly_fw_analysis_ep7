/* Self-authored freestanding byte operations. No vendor/libc source copied.
 * Compile with -fno-builtin -fno-tree-loop-distribute-patterns to prevent
 * compiler-generated recursive calls to the functions being implemented.
 * Callers provide valid accessible objects for count bytes. memcpy ranges must
 * not overlap (not memmove). No volatile/MMIO, atomicity, or DMA semantics. */
#include <stddef.h>

void *memcpy(void *destination, const void *source, size_t count)
{
    unsigned char *to = (unsigned char *)destination;
    const unsigned char *from = (const unsigned char *)source;
    size_t i;
    for (i = 0; i < count; ++i)
        to[i] = from[i];
    return destination;
}

void *memset(void *destination, int value, size_t count)
{
    unsigned char *to = (unsigned char *)destination;
    unsigned char byte = (unsigned char)value;
    size_t i;
    for (i = 0; i < count; ++i)
        to[i] = byte;
    return destination;
}
