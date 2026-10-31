#ifndef EP7_NATIVE_UI_SELECTOR_H
#define EP7_NATIVE_UI_SELECTOR_H
#include <stdint.h>
/* Permanent read-only native list storage. This is not an enable/ready flag. */
extern const uint16_t ep7s_categories[6];
/* Internal post-boundary only: full original ID193 initializer just returned
 * on its live124-byte selector, before the native constructor publishes it.
 * G6 must exclude other concurrent/direct reload and pool-reset paths.
 * Return1 expands storage with H/L disabled;0 leaves stock state untouched. */
int ep7s_expand_after_init(void *selector,uint32_t id);
void *ep7_gcc_mvc_array_new(unsigned bytes);
void ep7_gcc_mvc_array_delete(void *);
#endif
