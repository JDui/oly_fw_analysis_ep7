#ifndef EP7_NATIVE_UI_CONTENT_H
#define EP7_NATIVE_UI_CONTENT_H
#include "../ui_mvc/lifetime.h"

/* Explicit scalar allocation, never a stock S child with a changed type tag.
 * The 48-byte native base and private fields have independently owned extent. */
struct ep7c_child { uint8_t native[48];uint32_t generation,category; };
/* Permanent G6-owned GUI-only state; no live reset or move. */
struct ep7c_content { struct ep7c_child *child;uint32_t generation; };
extern struct ep7c_content ep7_native_content;
extern const unsigned char ep7_content_vtable[] __asm__("ep7_native_content_vtable");
void ep7c_rebuild(void *parent);
void ep7c_before_destroy(void *child);
void ep7c_require_owned(const struct ep7m_lifetime *);
/* These assembly veneers implement the native allocation/base/destructor ABI. */
void *ep7_gcc_mvc_scalar_new(uint32_t bytes);
void ep7_gcc_mvc_base_init(void *child);
void ep7_gcc_mvc_dispose(void *child);
void ep7_gcc_mvc_stock_rebuild(void *parent);
#endif
