#include "cold_bootstrap.h"
#include "runtime.h"
#include "../controller_sidecar/native.h"
#include "../controller_sidecar/sidecar.h"
#include "../snapshot_transport/native/cohort.h"
#include "../target/postbuilder/cohort.h"

static struct { ep7p core; ep7b boot; ep7r runtime; } storage;
static unsigned entered;
extern ep7b_native ep7b_unresolved_native(void);
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);

static bool installed(void *ctx)
{
    (void)ctx;
    /* early_cohort first proves the local section flags before any section2
     * bytes below are read. It is an observation, not a transfer/cache proof. */
    const ep7c *capture=&ep7_controller_sidecar_unresolved;
    return ep7r_native_early_cohort_present() && capture->initialized && !capture->poison &&
        !capture->state && !capture->serial && !capture->generation && ep7cn_native_cohort_present() &&
        ep7q_native_cohort_present() && ep7n_postbuilder_cohort_present();
}

void ep7r_bootstrap_initialize(void)
{
    ep7n_task task;
    if(entered || ep7r_get(&ep7_native_runtime_slot))ep7_gcc_quarantine(0xf01u);
    entered=1; /* Serialize through the single reviewed startup call, no retry. */
    if(!ep7n_native_current_task((uint32_t)(uintptr_t)&task,&task) ||
       task.tid!=0x2du || task.domain || task.entry!=0x601912fbu ||
       task.stack_bytes!=2048u)ep7_gcc_quarantine(0xf02u);
    if(!ep7r_native_cold_context(task.tcb))ep7_gcc_quarantine(0xf06u);
    if(!installed(NULL))ep7_gcc_quarantine(0xf03u);
    if(!ep7b_prepare(&storage.boot,&storage.core,ep7b_unresolved_native()))
        ep7_gcc_quarantine(0xf04u); /* ep7b already owns its failure/abort policy. */
    if(!ep7r_prepare(&storage.runtime,&storage.boot,ep7r_native_environment(NULL,installed)) ||
       !ep7r_publish(&ep7_native_runtime_slot,&storage.runtime)){
        (void)ep7b_abort_unpublished(&storage.boot);
        ep7_gcc_quarantine(0xf05u); /* Never start the modified receivers without a runtime. */
    }
}
