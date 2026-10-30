/* Host only: rename BOTH definitions and declarations with the test command.
 * The sanitizer and libc retain their own standard symbol names. */
#include <assert.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
void *memcpy(void *, const void *, size_t);
void *memset(void *, int, size_t);

int main(void)
{
    unsigned char source[192], destination[192];
    static const int fills[] = {-257,-1,0,1,127,128,255,256,511,INT_MIN,INT_MAX};
    size_t src_offset, dst_offset, count, i, fill;
    unsigned long cases = 0;
    for (src_offset = 0; src_offset < 8; ++src_offset)
        for (dst_offset = 0; dst_offset < 8; ++dst_offset)
            for (count = 0; count <= 128; ++count) {
                for (i = 0; i < sizeof source; ++i) {
                    source[i] = (unsigned char)(i * 37u + src_offset);
                    destination[i] = 0xa5;
                }
                assert(memcpy(destination + 16 + dst_offset,
                              source + 16 + src_offset, count)
                       == destination + 16 + dst_offset);
                for (i = 0; i < sizeof destination; ++i) {
                    unsigned char expected = 0xa5;
                    if (i >= 16 + dst_offset && i < 16 + dst_offset + count)
                        expected = source[16 + src_offset + i - 16 - dst_offset];
                    assert(destination[i] == expected);
                    assert(source[i] == (unsigned char)(i * 37u + src_offset));
                }
                ++cases;
            }
    for (dst_offset = 0; dst_offset < 8; ++dst_offset)
        for (count = 0; count <= 128; ++count)
            for (fill = 0; fill < sizeof fills / sizeof fills[0]; ++fill) {
                for (i = 0; i < sizeof destination; ++i)
                    destination[i] = 0x5a;
                assert(memset(destination + 16 + dst_offset, fills[fill], count)
                       == destination + 16 + dst_offset);
                for (i = 0; i < sizeof destination; ++i) {
                    unsigned char expected = 0x5a;
                    if (i >= 16 + dst_offset && i < 16 + dst_offset + count)
                        expected = (unsigned char)fills[fill];
                    assert(destination[i] == expected);
                }
                ++cases;
            }
    printf("freestanding byte operations: %lu host cases passed\n", cases);
    return 0;
}
