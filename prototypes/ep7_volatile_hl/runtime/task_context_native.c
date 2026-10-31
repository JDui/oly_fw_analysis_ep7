#include "task_context.h"
#include "queue_context.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only kernel context reads");
extern int ep7_gcc_get_tid(uint16_t *);
static int query(void *ctx,uint16_t *out)
{ (void)ctx;return ep7_gcc_get_tid(out); }
static bool read_word(void *ctx,uint32_t address,uint32_t *out)
{ (void)ctx;*out=*(const volatile uint32_t *)(uintptr_t)address;return true; }
static bool read_half(void *ctx,uint32_t address,uint16_t *out)
{ (void)ctx;*out=*(const volatile uint16_t *)(uintptr_t)address;return true; }
static const ep7n_task_ops native_ops={NULL,query,read_word,read_half};
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *out)
{
    return ep7n_query_task(&native_ops,anchor,out);
}
bool ep7n_native_queue(unsigned handle,ep7n_queue *out)
{ return ep7n_query_queue(&native_ops,handle,out); }
