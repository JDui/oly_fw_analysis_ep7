#ifndef EP7_TEXT_NATIVE_RESOURCE_H
#define EP7_TEXT_NATIVE_RESOURCE_H
#include <stdint.h>

enum { EP7_HL_TEXT_WIDGET_ID=0x7e10,EP7_TEXT_DESCRIPTOR_BYTES=94 };
struct ep7_text_resource {
    _Alignas(4) uint8_t descriptor[96];
    _Alignas(4) uint8_t layouts[16];
};
/* Native 32-bit layout only. Valid fresh112 writable bytes, independently owned
 * from all native allocations; prepare before publication and never move or
 * rewrite while a creation/native reference may use it. The G6 installer must
 * qualify the exact build1100 stock source mappings before this can execute.
 * Clones stock index53's style/font/two rectangles, changes only ID and layout
 * pointer. Retains its stock empty-navigation reference. This constructs data;
 * it neither obtains an owner nor shows/hides a widget or enables a renderer. */
void ep7_text_resource_prepare(struct ep7_text_resource *);
#endif
