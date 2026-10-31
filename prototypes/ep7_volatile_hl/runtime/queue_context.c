#include "queue_context.h"
static bool id_shape(unsigned id)
{ return id<=0x7fffu && (id&0xfffu) && (id&0x7000u)<=0x2000u; }
static bool word_address(uint32_t address,unsigned last)
{ return address && !(address&3u) && last<=UINT32_MAX-address; }
static bool read_view(const ep7n_task_ops *ops,unsigned handle,ep7n_queue *v)
{
    uint32_t cpu,limits,cell;uint16_t count,id;unsigned index=(handle&0xfffu)-1u;
    v->handle=(uint16_t)handle;v->domain=(uint16_t)(handle>>12);
    if(!ops->read32(ops->ctx,0x8050u,&cpu) || cpu!=v->domain ||
       !ops->read32(ops->ctx,0x8ff00004u+4u*cpu,&v->root) || !word_address(v->root,235) ||
       !ops->read32(ops->ctx,v->root+60,&limits) || !word_address(limits,27) ||
       !ops->read16(ops->ctx,limits+26,&count) || !count || count>0x7fffu || index>=count ||
       !ops->read32(ops->ctx,v->root+232,&v->table) || !word_address(v->table,4u*index+3u))return false;
    cell=v->table+4u*index;
    if(!ops->read32(ops->ctx,cell,&v->object) || !word_address(v->object,35) ||
       !ops->read16(ops->ctx,v->object,&id) || id!=handle ||
       !ops->read32(ops->ctx,v->object+20,&v->attributes) ||
       !ops->read32(ops->ctx,v->object+24,&v->maximum) || !v->maximum ||
       !ops->read32(ops->ctx,v->object+28,&v->ring_bytes) || v->ring_bytes<4 ||
       v->maximum>v->ring_bytes-4 ||
       !ops->read32(ops->ctx,v->object+32,&v->backing) ||
       !word_address(v->backing,v->ring_bytes) || (v->ring_bytes&3u))return false;
    return true;
}
bool ep7n_same_queue(const ep7n_queue *a,const ep7n_queue *b)
{
    return a && b && a->handle==b->handle && a->domain==b->domain && a->root==b->root &&
        a->table==b->table && a->object==b->object && a->attributes==b->attributes &&
        a->maximum==b->maximum && a->ring_bytes==b->ring_bytes && a->backing==b->backing;
}
bool ep7n_query_queue(const ep7n_task_ops *ops,unsigned handle,ep7n_queue *out)
{
    ep7n_queue first={0},second={0};uint16_t tid,again;
    if(!out)return false;
    *out=first;
    if(!ops || !ops->get_tid || !ops->read32 || !ops->read16 || !id_shape(handle) ||
       ops->get_tid(ops->ctx,&tid)!=0 || !id_shape(tid) || (tid>>12)!=(handle>>12) ||
       !read_view(ops,handle,&first) || !read_view(ops,handle,&second) ||
       !ep7n_same_queue(&first,&second) || ops->get_tid(ops->ctx,&again)!=0 || again!=tid)return false;
    *out=first;return true;
}
