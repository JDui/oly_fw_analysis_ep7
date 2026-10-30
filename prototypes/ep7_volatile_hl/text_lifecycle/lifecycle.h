#ifndef EP7_TEXT_LIFECYCLE_H
#define EP7_TEXT_LIFECYCLE_H
#include <stddef.h>
#include <stdint.h>
/* Normalized C callbacks, NOT native firmware ABI/function pointers. */
struct ep7_text_lifecycle_ops {
 void *context;
 void *(*create)(void *, void *owner, const void *qualified_descriptor);
 int (*initialized)(void *, void *child); /* factory nonnull is insufficient */
 void (*destroy_unattached)(void *, void *child); /* must handle partial init */
 int (*attach)(void *, void *owner, void *child); /* exact 1 transfers ownership;
       every other result MUST mean no list membership/ownership transfer */
 int (*bind_parent)(void *, void *child, void *owner);
 int (*set_text)(void *, void *child, const uint16_t *nul_text);
};
struct ep7_text_lifecycle { void *child; void *owner; int bound; };
enum ep7_text_create_result { EP7_TEXT_CREATE_REJECTED=-1,
 EP7_TEXT_ATTACHED_DISPLAY_FAILED=0, EP7_TEXT_ATTACHED_READY=1 };
/* Zero-initialize state. UI-thread/exclusive callbacks, non-reentrant; descriptor,
   owner and text lifetime externally qualified. No native address admission. */
int ep7_text_create_attach(struct ep7_text_lifecycle *,
 const struct ep7_text_lifecycle_ops *, void *owner,
 const void *qualified_descriptor, const uint16_t *nul_text, int qualified);
/* Called BEFORE parent's child teardown. Does NOT destroy parent-owned child. */
void ep7_text_revoke(struct ep7_text_lifecycle *);
#endif
