#ifndef EP7_CONTROLLER_SIDECAR_H
#define EP7_CONTROLLER_SIDECAR_H
#include "ep7p.h"
#define EP7C_CAP 8u /* prototype bound, NOT native capacity */
typedef struct {
 uintptr_t associated, capture;
 unsigned capture_id, raw_mode, selector;
} ep7c_prefix;
typedef struct {
 uintptr_t node, associated;
 uint64_t token,generation;
 bool attempted,sealed;
 ep7c_prefix prefix;
 ep7p_snapshot snapshot;
} ep7c_entry;
typedef struct {
 bool initialized,poison;
 unsigned state;
 uint64_t generation,serial;
 ep7c_entry entries[EP7C_CAP];
} ep7c;
/* All storage is real, distinct, nonaliasing and exclusively controller-owned.
 * Fresh zeroed runtime only; never reset/reinitialize live or poisoned storage.
 * No asynchronous use, cancellation, reentry, concurrent UI/state writer.
 * Caller supplies actual fresh3116 provenance and stable owned native lifetime.
 * Node/capture labels are opaque, never dereferenced by this module.
 */
bool ep7c_init(ep7c *,unsigned observed_state);
void ep7c_transition(ep7c *,unsigned old_state,unsigned pending);
bool ep7c_register_fresh(ep7c *,unsigned state,uintptr_t node,uintptr_t associated,uint64_t *token);
/* MUST succeed immediately BEFORE any native prefix read; remain in same
 * serialized controller interval through seal/copy. Does not pin native memory. */
bool ep7c_authorize(ep7c *,unsigned state,uintptr_t node,uint64_t token);
/* Resolve ONLY a caller-proven currently live node, inside the same exclusive
 * controller interval through authorize/prefix access/seal/copyout or forget.
 * Never use this to upgrade a queued/stale pointer into a fresh capability:
 * address reuse is indistinguishable here. No native reads or memory pinning.
 * On failure *token is unchanged; caller MUST branch on the returned status. */
bool ep7c_resolve_live(ep7c *,unsigned state,uintptr_t node,uint64_t *token);
/* Exactly one sampling attempt, at caller-proven population completion.
 * Unsupported profile/failure/early attempt permanently neutral for this token.
 * settings callbacks cannot reenter sidecar. Captured profile, NOT current GUI.
 */
bool ep7c_seal(ep7c *,unsigned state,uintptr_t node,uint64_t token,
 const ep7c_prefix *,bool population_complete,ep7p *settings);
bool ep7c_copyout(ep7c *,unsigned state,uintptr_t node,uint64_t token,
 const ep7c_prefix *,ep7p_snapshot *out);
bool ep7c_forget(ep7c *,unsigned state,uintptr_t node,uint64_t token);
extern ep7c ep7_controller_sidecar_unresolved;
void ep7_sidecar_transition_unresolved(unsigned old_state,unsigned pending);
#endif
