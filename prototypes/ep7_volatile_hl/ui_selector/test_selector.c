#include "selector.h"
#include "../runtime/task_context.h"
#include <assert.h>
#include <string.h>

volatile uint32_t ep7_stock_selector_initializer_unresolved;
const unsigned char ep7_native_selector_init_bridge[1]={1};
static uint8_t selector[124],old_masks[8],new_masks[12];
static unsigned queries,allocations,deletions,wrong_task,fail_allocate;
static uint16_t half(const uint8_t *p) { return (uint16_t)(p[0]|((uint16_t)p[1]<<8)); }
static uint32_t word(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static void put16(uint8_t *p,uint16_t n) { p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8); }
static void put32(uint8_t *p,uint32_t n)
{ for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *task)
{
    (void)anchor;queries++;
    *task=(ep7n_task){0x101,0,0x1000,wrong_task?0:0x60dd5067,0x2000,16384};
    return true;
}
void *ep7_gcc_mvc_array_new(unsigned n)
{ assert(n==12);allocations++;return fail_allocate?NULL:new_masks; }
void ep7_gcc_mvc_array_delete(void *p)
{
    assert(p==old_masks&&half(selector+84)==6&&half(selector+86)==2);
    assert(word(selector+88)==(uint32_t)(uintptr_t)new_masks);
    assert(word(selector+92)==(uint32_t)(uintptr_t)ep7s_categories);
    assert(half(new_masks+8)==1&&half(new_masks+10)==1);
    deletions++;memset(old_masks,0xa5,sizeof old_masks);
}
static void reset(void)
{
    assert((uintptr_t)new_masks<=UINT32_MAX&&(uintptr_t)ep7s_categories<=UINT32_MAX);
    queries=allocations=deletions=wrong_task=fail_allocate=0;
    memset(selector,0,sizeof selector);memset(new_masks,0xcc,sizeof new_masks);
    for (unsigned i=0;i<4;i++) put16(old_masks+2*i,(uint16_t)(i==1?7:0));
    put32(selector,0x6114f7e4);put32(selector+80,193);put16(selector+84,4);put16(selector+86,2);
    put32(selector+88,(uint32_t)(uintptr_t)old_masks);put32(selector+92,0x6114e050);
    put16(selector+106,3);put32(selector+48,0x60de1550);put32(selector+52,0x60de1567);
    ep7_stock_selector_initializer_unresolved=(uint32_t)(uintptr_t)ep7_native_selector_init_bridge;
}
int main(void)
{
    uint8_t saved[124],masks[8];
    /*1 Actual initializer entry and GUI checks precede all selector reads. */
    reset();ep7_stock_selector_initializer_unresolved=0;
    assert(!ep7s_expand_after_init((void *)1,193)&&!queries&&!allocations);
    reset();wrong_task=1;assert(!ep7s_expand_after_init((void *)1,193)&&queries==1&&!allocations);
    /*2 New allocation failure leaves the entire original object/array intact. */
    reset();memcpy(saved,selector,sizeof saved);memcpy(masks,old_masks,8);fail_allocate=1;
    assert(!ep7s_expand_after_init(selector,193)&&allocations==1&&!deletions);
    assert(!memcmp(saved,selector,sizeof saved)&&!memcmp(masks,old_masks,8));
    /*3 Full new storage precedes old free; preserve stock masks/focus/callbacks. */
    reset();memcpy(masks,old_masks,8);
    assert(ep7s_expand_after_init(selector,193)==1&&allocations==1&&deletions==1);
    assert(!memcmp(masks,new_masks,8)&&half(selector+104)==0&&half(selector+106)==5);
    assert(word(selector+48)==0x60de1550&&word(selector+52)==0x60de1567);
    assert(!ep7s_expand_after_init(selector,193)&&allocations==1&&deletions==1);
    /*4 Unsupported shape is left alone; no claim about arbitrary pointers. */
    reset();selector[106]=2;memcpy(saved,selector,sizeof saved);
    assert(!ep7s_expand_after_init(selector,193)&&!allocations&&!deletions);
    assert(!memcmp(saved,selector,sizeof saved));
    return 0;
}
