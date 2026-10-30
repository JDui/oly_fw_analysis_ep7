#ifndef EP7_TEXT_ROLLBACK_H
#define EP7_TEXT_ROLLBACK_H
#include <stddef.h>
#include <stdint.h>
/* Ops table and context must not alias child or any owned allocation. They
 * remain stable/alive through restore. Callbacks cannot reenter or mutate the
 * object/qualification after admission; all return normally. */
struct ep7_text_rollback_ops {
 void *context;
 /* Before ANY object byte read: exact live180 allocation, completed ctor,
    new/unattached/unpublished identity and exclusive UI ownership. */
 int (*qualify)(void *, const void *, size_t);
 /* Save previous GLOBAL UI allocator context, select bytes28/29. On failure,
    leave global context unchanged. Token is opaque, not a native ABI object. */
 int (*enter_context)(void *, uint8_t, uint8_t, uintptr_t *saved);
 /* Infallible restoration of prior context, even after object was destroyed. */
 void (*restore_context)(void *, uintptr_t saved);
};
/* 1 destroyed,0 rejected with object untouched. Normalized C contract only. */
int ep7_text_rollback(void *, const struct ep7_text_rollback_ops *);
/* Self-authored compile-only native veneer, not installed. */
void ep7_gcc_text_cleanup_destroy_unresolved(void *);
#endif
