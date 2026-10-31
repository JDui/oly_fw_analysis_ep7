#include "runtime.h"
#include "../ep7p_direct.h"
static const unsigned handles[EP7R_QUEUES]={0x4b,0x4c,0x4d,0xab,0x4f};
static const unsigned maximums[EP7R_QUEUES]={148,312,300,312,312};
static const unsigned rings[EP7R_QUEUES]={4864,10112,9728,10112,10112};
bool ep7r_prepare(ep7r *r,ep7b *b,ep7r_environment env)
{
    if(!r || !b || r->state!=EP7R_COLD || b->state!=EP7B_PREPARED || !b->core || !b->core->ready ||
       (b->provider.handle&0x7000u) || ep7s_poisoned(&b->provider) ||
       !env.installation_ready || !env.task || !env.queue || !env.delay_one || !env.quarantine)return false;
    if(!ep7t_init(&r->transport,ep7s_ops(&b->provider)))return false;
    r->boot=b;r->env=env;atomic_init(&r->stopped,false);atomic_init(&r->io_closed,false);atomic_init(&r->fault,0);
    r->state=EP7R_PREPARED;return true;
}
ep7r *ep7r_get(const ep7r_slot *slot)
{ return slot?atomic_load_explicit(&slot->published,memory_order_acquire):NULL; }
bool ep7r_apply(const ep7r_slot *slot,uintptr_t request,unsigned char *out,size_t length)
{
    ep7r *r=ep7r_get(slot);
    return r && ep7p_direct_apply(r->boot->core,request,out,length);
}
bool ep7r_publish(ep7r_slot *slot,ep7r *r)
{
    unsigned i;
    if(!slot || !r || ep7r_get(slot) || r->state!=EP7R_PREPARED ||
       r->boot->state!=EP7B_PREPARED || ep7s_poisoned(&r->boot->provider) ||
       !r->env.installation_ready(r->env.ctx))return false;
    for(i=0;i<EP7R_QUEUES;i++){
        ep7n_queue *q=&r->queues[i];
        if(!r->env.queue(r->env.ctx,handles[i],q) || q->handle!=handles[i] || q->domain ||
           q->attributes!=128 || q->maximum!=maximums[i] || q->ring_bytes!=rings[i])return false;
    }
    if(!ep7b_mark_published(r->boot))return false;
    r->state=EP7R_PUBLISHED;
    atomic_store_explicit(&slot->published,r,memory_order_release);return true;
}
bool ep7r_accepting(const ep7r *r)
{
    return r && r->state==EP7R_PUBLISHED && !atomic_load_explicit(&r->stopped,memory_order_acquire) &&
        !atomic_load_explicit(&r->fault,memory_order_acquire) && !ep7s_poisoned(&r->boot->provider);
}
void ep7r_stop(ep7r *r)
{ if(r && r->state==EP7R_PUBLISHED)atomic_store_explicit(&r->stopped,true,memory_order_release); }
bool ep7r_task(ep7r *r,uint32_t anchor,ep7n_task *out)
{
    ep7n_task view={0};
    if(!out)return false;
    *out=view;
    if(!r || r->state!=EP7R_PUBLISHED || !r->env.task(r->env.ctx,anchor,&view) ||
       !view.tid || view.tid>0xfffu || view.domain || !view.tcb || !view.entry ||
       !view.stack_low || ((view.stack_low|view.stack_bytes|anchor)&3u) || view.stack_bytes<20 ||
       view.stack_bytes>UINT32_MAX-view.stack_low || anchor<view.stack_low ||
       anchor-view.stack_low>=view.stack_bytes)return false;
    *out=view;return true; /* Health does NOT erase an already-published context. */
}
_Noreturn void ep7r_fault(ep7r *r,unsigned reason)
{
    ep7r_stop(r);atomic_store_explicit(&r->fault,reason,memory_order_release);
    /* The native callback traps without return. Even a broken returning callback
     * must never let a pending cleanup fall through into native ACK/free. */
    for(;;)r->env.quarantine(r->env.ctx,reason);
}
bool ep7r_qualify_queue(void *ctx,unsigned handle,unsigned maximum)
{
    ep7r *r=ctx;ep7n_queue view;unsigned i;
    if(!ep7r_io_open(r))return false;
    for(i=0;i<EP7R_QUEUES;i++)if(handles[i]==handle)break;
    if(i==EP7R_QUEUES || maximum!=maximums[i])return false;
    if(!r->env.queue(r->env.ctx,handle,&view) || !ep7n_same_queue(&view,&r->queues[i])){
        /* Deletion may have run during the unlocked preliminary query. Its
         * monotonic observer closes I/O before clearing or replacing anything. */
        if(!ep7r_io_open(r))return false;
        ep7r_fault(r,EP7R_FAULT_QUEUE);
    }
    return ep7r_io_open(r);
}
bool ep7r_io_open(const ep7r *r)
{ return r && r->state==EP7R_PUBLISHED && !atomic_load_explicit(&r->io_closed,memory_order_acquire); }
bool ep7r_guard_queue(const ep7r *r,const ep7r_queue_object *view)
{
    unsigned i;
    if(!view || !ep7r_io_open(r))return false;
    for(i=0;i<EP7R_QUEUES;i++){
        const ep7n_queue *q=&r->queues[i];
        if(q->object==view->object)return q->handle==view->handle && q->attributes==view->attributes &&
            q->maximum==view->maximum && q->ring_bytes==view->ring_bytes && q->backing==view->backing;
    }
    return false;
}
void ep7r_note_queue_delete(ep7r *r,uint32_t object)
{
    unsigned i;
    if(!r || r->state!=EP7R_PUBLISHED)return;
    for(i=0;i<EP7R_QUEUES;i++)if(r->queues[i].object==object){
        atomic_store_explicit(&r->io_closed,true,memory_order_release);
        ep7r_stop(r);return;
    }
}
void ep7r_progress(void *ctx)
{
    ep7r *r=ctx;ep7n_task task;
    if(ep7s_poisoned(&r->boot->provider))ep7r_fault(r,EP7R_FAULT_LOCK);
    if(!ep7r_task(r,(uint32_t)(uintptr_t)&task,&task))ep7r_fault(r,EP7R_FAULT_CONTEXT);
    if(atomic_load_explicit(&r->boot->provider.owner,memory_order_relaxed)==task.tid)
        ep7r_fault(r,EP7R_FAULT_CONTEXT); /* Never sleep while owning the core lock. */
    if(r->env.delay_one(r->env.ctx)!=0)ep7r_fault(r,EP7R_FAULT_DELAY);
    if(ep7s_poisoned(&r->boot->provider))ep7r_fault(r,EP7R_FAULT_LOCK);
}
void ep7r_retire(void *ctx,ep7t_ticket ticket)
{
    ep7r *r=ctx;
    if(!ticket.metadata || !ticket.serial)ep7r_fault(r,EP7R_FAULT_TICKET);
    while(!ep7t_retire_owned(&r->transport,ticket))ep7r_progress(r);
}
