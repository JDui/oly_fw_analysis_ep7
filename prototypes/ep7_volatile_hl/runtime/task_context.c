#include "task_context.h"
static bool id_shape(uint16_t id)
{ return !(id&0x8000u) && (id&0xfffu) && (id&0x7000u)<=0x2000u; }
static bool word_address(uint32_t address,unsigned last_offset)
{ return address && !(address&3u) && last_offset<=UINT32_MAX-address; }
static bool current_tcb(const ep7n_task_ops *ops,unsigned domain,uint32_t *tcb)
{
    uint32_t cpu,root,cell;
    return ops->read32(ops->ctx,0x8050u,&cpu) && cpu==domain &&
        ops->read32(ops->ctx,0x8ff00004u+4u*cpu,&root) && word_address(root,99) &&
        ops->read32(ops->ctx,root+96,&cell) && word_address(cell,3) &&
        ops->read32(ops->ctx,cell,tcb) && word_address(*tcb,91);
}
bool ep7n_query_task(const ep7n_task_ops *ops,uint32_t anchor,ep7n_task *out)
{
    ep7n_task view={0};uint16_t id,again;uint32_t tcb;
    if(!out)return false;
    *out=view;
    if(!ops || !ops->get_tid || !ops->read32 || !ops->read16 || (anchor&3u) ||
       ops->get_tid(ops->ctx,&view.tid)!=0 || !id_shape(view.tid))return false;
    view.domain=(uint16_t)(view.tid>>12);
    if(!current_tcb(ops,view.domain,&view.tcb) ||
       !ops->read16(ops->ctx,view.tcb+16,&id) || id!=view.tid ||
       !ops->read32(ops->ctx,view.tcb+76,&view.entry) || !view.entry ||
       !ops->read32(ops->ctx,view.tcb+84,&view.stack_bytes) || view.stack_bytes<20 ||
       !ops->read32(ops->ctx,view.tcb+88,&view.stack_low) || !view.stack_low ||
       ((view.stack_low|view.stack_bytes)&3u) || view.stack_bytes>UINT32_MAX-view.stack_low ||
       anchor<view.stack_low || anchor-view.stack_low>=view.stack_bytes ||
       ops->get_tid(ops->ctx,&again)!=0 || again!=view.tid ||
       !current_tcb(ops,view.domain,&tcb) || tcb!=view.tcb)return false;
    *out=view;return true;
}
