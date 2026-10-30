#include "sidecar.h"
/* Exact callback used by compiled state observer. Runtime init/native hook
 * still unresolved. No locks, allocation, fallible callback, or async handoff. */
void ep7_sidecar_transition_unresolved(unsigned old_state,unsigned pending)
{ ep7c_transition(&ep7_controller_sidecar_unresolved,old_state,pending); }
