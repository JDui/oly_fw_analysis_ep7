#ifndef EP7_TEXT_NATIVE_LIFECYCLE_H
#define EP7_TEXT_NATIVE_LIFECYCLE_H
#include "lifecycle.h"
#include "native_create.h"

/* Zero initialize; exclusively owned by one admitted GUI operation at a time.
 * This state and qualification context must not alias owner, child or resource.
 * It must remain alive until parent teardown has revoked attached, and every
 * retained fresh allocation has been destroyed. Pointer identity is not a lease. */
struct ep7_text_native {
    struct ep7_text_lifecycle attached;
    struct ep7_text_factory_result fresh;
    void *owner;
    int busy;
};
enum { EP7_TEXT_NATIVE_RETAINED=-2 };
/* Before ANY owner/resource byte read, qualify must establish the live fully
 * initialized exact1360 display container, its initialized child list, stable
 * live GUI service, exclusive/non-reentrant UI ownership, readable94 descriptor
 * plus embedded-reference lifetimes, independent widget ID and valid font/layout.
 * This is the concrete UI entry/installer's obligation, not a boolean substitute
 * for it. Text is a separately qualified readable EP7_TEXT_UNITS UTF16 buffer.
 * The admitted scope lasts through every callback and final context restoration.
 * Return1=attached/display accepted;0=parent owns child but display/bind failed;
 * -1=rejected with no new retained allocation;-2=fresh allocation retained after
 * rejected rollback. A -2 state cannot be reused or discarded. */
int ep7_text_native_open(struct ep7_text_native *,void *owner,const void *resource,
    const uint16_t *text,
    int (*qualify)(void *,const void *,size_t,const void *,size_t),void *context);
/* Retry only in an admitted live exclusive GUI scope. Does not require owner
 * storage to survive: this fresh child was never attached or published. */
int ep7_text_native_retry_rollback(struct ep7_text_native *);
/* BEFORE parent native teardown. Never frees parent-owned children. Returns0
 * while busy or retaining an unattached allocation; caller must retain state. */
int ep7_text_native_revoke(struct ep7_text_native *);
int ep7_gcc_ui_attach(void *owner,void *child);
int ep7_gcc_text_bind(void *child,void *owner);
#endif
