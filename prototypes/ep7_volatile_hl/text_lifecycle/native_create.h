#ifndef EP7_TEXT_NATIVE_CREATE_H
#define EP7_TEXT_NATIVE_CREATE_H

struct ep7_text_factory_result { void *child; int initialized; };
/* GCC ABI, not a cast of the native factory. Caller independently qualifies:
 * - live serialized GUI service, stable allocator selection and layout state;
 * - live owner with the audited +248 context getter;
 * - readable type8010 resource (94 bytes), all embedded data, count/index;
 * - independent writable result, no alias with owner/resource/service storage.
 * The factory selects the owner's allocator and this veneer restores the prior
 * service selection on every NORMAL return. No task/object admission is added.
 * child==NULL means allocation failed; initialized is then normalized to0.
 * Nonnull child with initialized==0 is still a live, fresh, unattached allocation
 * and must be rolled back. Never attach it or drop the returned ownership.
 * No child field is appended and no existing object is borrowed. */
void ep7_gcc_text_factory(void *owner,const void *resource,
    struct ep7_text_factory_result *result);
#endif
