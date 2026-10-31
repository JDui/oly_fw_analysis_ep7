#ifndef EP7_NATIVE_UI_MVC_LIFETIME_H
#define EP7_NATIVE_UI_MVC_LIFETIME_H
#include "../runtime/task_context.h"
#include <stdatomic.h>

/* Permanent G6-owned storage. Fields after started are GUI-task-only; callers
 * must retain the same serialized native operation while using a returned view.
 * This records construction provenance, not H/L content or renderer admission. */
struct ep7m_lifetime {
    atomic_bool started;
    ep7n_task task;
    uint32_t generation,constructing,stopped,selector_count,invalidated;
    void *container,*parent,*viewer,*selector,*masks;
};
extern struct ep7m_lifetime ep7_native_mvc;
int ep7m_native_cohort_present(void);
void ep7m_gui_begin(void);
void ep7m_gui_complete(void *original_result);
void ep7m_before_gui_exit(void);
void ep7m_before_parent_destroy(void *parent);
void ep7m_before_viewer_destroy(void *viewer);
/* Only inside pinned GUI calls. NULL before construction/after teardown or if
 * current native relationships changed. Never accepts an arbitrary pointer. */
const struct ep7m_lifetime *ep7m_current(void);
#endif
