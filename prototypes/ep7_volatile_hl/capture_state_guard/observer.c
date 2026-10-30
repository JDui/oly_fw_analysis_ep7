/* TARGET ONLY. Serialized controller snapshot, stable through native commit.
 * Volatile byte loads do NOT establish atomicity/exclusion. Callback must not
 * change state words, reenter controller or retain asynchronous context. */
#include <stdint.h>
_Static_assert(sizeof(uintptr_t)==4,"32-bit target only");
/* Invalidate old33 for ANY actual transition including33->33. Entering33 must
 * create a fresh generation. Synchronization/failure policy remain UNBOUND;
 * native continuation cannot be vetoed through this void callback interface. */
extern void ep7_sidecar_transition_unresolved(unsigned int old_state,
                                             unsigned int pending_state);
static unsigned int read16(const volatile unsigned char *p)
{
 return (unsigned int)p[0] | (unsigned int)p[1]<<8;
}
void ep7_gcc_state_transition_observer(void)
{
 const volatile unsigned char *p=(const volatile unsigned char *)(uintptr_t)0x62234fc0u;
 unsigned int old_state=read16(p);
 unsigned int pending=read16(p+2);
 if(pending!=255u) ep7_sidecar_transition_unresolved(old_state,pending);
}
