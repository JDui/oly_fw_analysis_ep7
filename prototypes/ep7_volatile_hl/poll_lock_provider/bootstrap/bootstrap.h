#ifndef EP7_BOOTSTRAP_H
#define EP7_BOOTSTRAP_H
#include "ep7_sem_provider.h"
/* Normalized callbacks, NOT native ABI. All return normally. Caller serializes
 * startup/retry/publish, no hooks/users until publication, no object moves. */
typedef struct {uint32_t attributes,initial,maximum;} ep7b_sem_spec;
typedef struct {
 void *ctx;
 int (*create)(void *,const ep7b_sem_spec *);
 int (*delete_unpublished)(void *,unsigned int);
 ep7s_native raw;
} ep7b_native;
enum ep7b_state {EP7B_COLD,EP7B_CREATING,EP7B_RETAINED,EP7B_PREPARED,EP7B_PUBLISHED,EP7B_CLOSED,EP7B_FAILED,EP7B_QUARANTINED};
typedef struct {
 enum ep7b_state state;
 int owned_handle; /* preserve complete positive return; never truncate unknown */
 int last_native_status;
 ep7b_native native;
 ep7s_provider provider;
 ep7p *core;
} ep7b;
/* b and core genuinely fresh zero-initialized, distinct and unpublished.
 * Positive create IDs imply sole ownership under pinned raw-create contract;
 * negative/zero must not hide an allocated handle. No arbitrary wrappers. */
bool ep7b_prepare(ep7b *,ep7p *,ep7b_native);
/* State marker only: caller owns subsequent safe publication of pointers/hooks. */
bool ep7b_mark_published(ep7b *);
/* Only before publication. Context failure can retain for retry; unknown errors
 * quarantine permanently. No runtime shutdown or force-reset function exists. */
bool ep7b_abort_unpublished(ep7b *);
#endif
