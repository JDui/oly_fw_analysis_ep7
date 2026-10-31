#include "runtime.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only native runtime callbacks");
extern int ep7_gcc_task_delay_one(void);
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
static bool task(void *ctx,uint32_t anchor,ep7n_task *out)
{ (void)ctx;return ep7n_native_current_task(anchor,out); }
static bool queue(void *ctx,unsigned handle,ep7n_queue *out)
{ (void)ctx;return ep7n_native_queue(handle,out); }
static int delay_one(void *ctx)
{ (void)ctx;return ep7_gcc_task_delay_one(); }
static void quarantine(void *ctx,unsigned reason)
{ (void)ctx;ep7_gcc_quarantine(reason); }
ep7r_environment ep7r_native_environment(void *ctx,bool (*ready)(void *))
{ ep7r_environment e={ctx,ready,task,queue,delay_one,quarantine};return e; }
