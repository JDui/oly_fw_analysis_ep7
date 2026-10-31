#ifndef EP7_NATIVE_UI_OWNER_H
#define EP7_NATIVE_UI_OWNER_H
#include "../text_lifecycle/native_lifecycle.h"
#include "../text_lifecycle/native_resource.h"
#include "../runtime/task_context.h"
#include <stdatomic.h>

struct ep7u_screen_call {
    void *service;
    uint32_t request;
    int32_t result;
    uint32_t admitted;
};
/* Permanent zero-initialized G6-owned storage, never reset/moved live. All
 * mutable fields except started belong to the pinned GUI task. No field here
 * authorizes MVC input, viewer rendering, installation, or cross-task access. */
struct ep7u_owner {
    atomic_bool started;
    ep7n_task task;
    void *service,*owner;
    uint32_t generation,depth;
    unsigned active,display_ready,opening,stopped;
    struct ep7_text_native text;
    struct ep7_text_resource resource;
};
extern struct ep7u_owner ep7_native_ui_owner;

/* Actual table cohort check, not an enable parameter. Cold G6 installation must
 * still prove source mappings, task/service lifetime, all bypass paths and GUI
 * exclusion. Four equal table words alone are not those proofs. */
int ep7u_native_cohort_present(void);
/* Only the native full-method bridges may supply these call boundaries.
 * enter suspends admission but retains old ownership across native failure.
 * leave observes the just-completed request278 allocation/bind/publication
 * chain; it is not a public pointer-based registration API. */
void ep7u_screen_enter(struct ep7u_screen_call *);
void ep7u_screen_leave(struct ep7u_screen_call *);
/* Before matching owner cleanup, bulk cleanup AND destructor; no child reads
 * occur after revocation. Inconsistent/reentrant live operations quarantine
 * before native destruction, using the existing terminal hold implementation. */
enum { EP7U_CLEANUP=1,EP7U_BULK=2,EP7U_DESTRUCTOR=3 };
void ep7u_before_retire(void *owner,unsigned stage);
/* Update only the captured, still-member native text child in the pinned GUI
 * scope. Failure invalidates display readiness for this owner; no fresh retry.
 * Success optionally returns the current owner generation, not an input lease. */
int ep7u_present(const uint16_t *text,uint32_t *generation);
#endif
