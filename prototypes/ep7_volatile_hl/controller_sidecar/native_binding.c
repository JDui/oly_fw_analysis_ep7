/* Exact native candidates. The G6 installer must establish supported object
 * lifetimes/exclusion and install ALL init/state/fresh/population/free/release
 * hooks before publication. Task checks do not create such a lifetime lease. */
#include "sidecar.h"
#include "native.h"
#include "../runtime/runtime.h"
#include "../snapshot_transport/native/producer.h"
#include <string.h>
#ifndef EP7CN_HOST_FIXTURE
_Static_assert(sizeof(uintptr_t)==4,"target-only capture source");
#endif
extern void *ep7_gcc_capture_lookup(unsigned capture_id);
extern _Noreturn void ep7_gcc_quarantine(unsigned reason);
ep7c ep7_controller_sidecar_unresolved;
static atomic_bool closed=ATOMIC_VAR_INIT(false);
static atomic_bool owner_chosen=ATOMIC_VAR_INIT(false);
static ep7n_task owner;
static ep7r *pinned_runtime;
static bool busy; /* Only the pinned controller reads/writes this, after task qualification. */
enum { WAIT_QUEUE=0x6223e7e0u,WAIT_BACKING=0x6223e7f4u,WAIT_CAP=25u };
typedef struct {
    uint32_t associated,capture;
    uint64_t generation;
    ep7q_capture_scope scope;
} wait_entry;
static struct {
    bool tracked;
    unsigned count,head,tail;
    wait_entry entries[WAIT_CAP];
} waiting;
/* Queue position, not a latest-value lookup by associated address, owns each
 * frozen value. Retirement neutralizes it without changing native FIFO order. */
static void wait_revoke(uint32_t associated,uint32_t capture)
{
    for(unsigned i=0;i<WAIT_CAP;i++) {
        wait_entry *e=&waiting.entries[i];
        if((!associated&&!capture) || (associated&&e->associated==associated) ||
           (capture&&e->capture==capture))ep7q_capture_scope_init(&e->scope,0,NULL);
    }
}
static uint32_t word(uint32_t p){return *(const volatile uint32_t *)(uintptr_t)p;}
static unsigned state(void){return *(const volatile uint16_t *)(uintptr_t)0x62234fc0u;}
static bool span(uint32_t p,uint32_t bytes){return p && !(p&3u) && p<=UINT32_MAX-bytes;}
/* Exact initialized25-slot pool: each16-byte slot has a4-byte refcount and
 * a12-byte associated payload. No heap/tail size inferred from a node pointer. */
enum { ASSOCIATED_POOL=0x6223e0dcu,ASSOCIATED_BACKING=0x6223e160u,ASSOCIATED_COUNT=25u };
static bool associated_slot(uint32_t p)
{ return p>=ASSOCIATED_BACKING+4u && p<ASSOCIATED_BACKING+16u*ASSOCIATED_COUNT && !((p-4u-ASSOCIATED_BACKING)&15u); }
static bool associated_live(uint32_t p)
{
    if(!associated_slot(p))return false;
    return word(0x6223e0d8u)==ASSOCIATED_POOL &&
        *(const volatile uint16_t *)(uintptr_t)(ASSOCIATED_POOL+8u)==ASSOCIATED_COUNT &&
        *(const volatile uint16_t *)(uintptr_t)(ASSOCIATED_POOL+10u)==4u &&
        word(ASSOCIATED_POOL+12u)==0x6223e0fcu &&
        *(const volatile uint16_t *)(uintptr_t)(ASSOCIATED_POOL+24u)==16u &&
        word(ASSOCIATED_POOL+28u)==ASSOCIATED_BACKING && word(p-4u)!=0;
}
static void close_capture(void){atomic_store_explicit(&closed,true,memory_order_release);}
static _Noreturn void fault(unsigned reason) { ep7_gcc_quarantine(0xe00u+reason); }
static ep7r *enter(uint32_t anchor,bool admitting)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;
    bool chosen=atomic_load_explicit(&owner_chosen,memory_order_acquire);
    if(chosen&&r!=pinned_runtime)fault(2);
    if(!r)return NULL; /* Pre-publication native work has no admitted sidecar users. */
    if(!ep7r_task(r,anchor,&t) || t.entry!=0x60289852u){
        close_capture();if(!admitting)fault(3);return NULL;
    }
    if(chosen){
        if(t.tid!=owner.tid || t.tcb!=owner.tcb || t.entry!=owner.entry ||
           t.domain!=owner.domain || t.stack_low!=owner.stack_low || t.stack_bytes!=owner.stack_bytes){
            close_capture();if(!admitting)fault(3);return NULL;
        }
    }else{
        if(!ep7_controller_sidecar_unresolved.initialized || ep7_controller_sidecar_unresolved.poison)return NULL;
        owner=t;pinned_runtime=r;atomic_store_explicit(&owner_chosen,true,memory_order_release);
    }
    /* A nested observer must not resume original free/state commit after merely
     * disabling future reads. Foreign destructive observers likewise stop above. */
    if(busy)fault(5);
    if(atomic_load_explicit(&closed,memory_order_acquire))return NULL;
    if(!ep7_controller_sidecar_unresolved.initialized || ep7_controller_sidecar_unresolved.poison)return NULL;
    if(!ep7cn_native_cohort_present())fault(4);
    if(admitting && !ep7r_accepting(r))return NULL;
    busy=true;return r;
}
static void leave(void) { busy=false; }
void ep7cn_initialize(unsigned initial)
{
    /* Exact inline site602897d7 before tasks use the controller. Never reset a
     * published/old sidecar on a subsequent native initialization. */
    if(initial!=0 || ep7_controller_sidecar_unresolved.initialized ||
       !ep7c_init(&ep7_controller_sidecar_unresolved,initial))fault(1);
}
void ep7_sidecar_transition_unresolved(unsigned old_state,unsigned pending)
{
    uint32_t anchor;
    if(enter((uint32_t)(uintptr_t)&anchor,false)) {
        ep7c_transition(&ep7_controller_sidecar_unresolved,old_state,pending);
        if(pending!=255u || ep7_controller_sidecar_unresolved.poison)wait_revoke(0,0);
        leave();
    }
}
void ep7cn_fresh(uint32_t node)
{
    uint64_t token;uint32_t anchor,associated,id,capture;
    if(!enter((uint32_t)(uintptr_t)&anchor,true))return;
    if(!span(node,56))goto done;
    /* Original fresh allocator returned this fully initialized, still-owned
     * prefix; registration is BEFORE its caller can publish the node pointer. */
    id=word(node);associated=word(node+8);
    if(id<1 || id>25 || !associated_live(associated))goto done;
    capture=(uint32_t)(uintptr_t)ep7_gcc_capture_lookup(id);
    if(!span(capture,24084))goto done;
    (void)ep7c_register_fresh_capture(&ep7_controller_sidecar_unresolved,state(),node,associated,id,capture,&token);
done:leave();
}
static bool prefix(unsigned observed_state,uint32_t node,uint64_t token,ep7c_prefix *out)
{
    uint32_t id,associated,capture;
    if(!span(node,56) || !ep7c_authorize(&ep7_controller_sidecar_unresolved,observed_state,node,token))return false;
    id=word(node);associated=word(node+8);
    if(id<1 || id>25 || !associated_live(associated))return false;
    capture=(uint32_t)(uintptr_t)ep7_gcc_capture_lookup(id);
    if(!span(capture,24084))return false;
    *out=(ep7c_prefix){associated,capture,id,
        *(const volatile unsigned char *)(uintptr_t)(capture+24053),
        *(const volatile unsigned char *)(uintptr_t)(capture+24083)};
    return true;
}
void ep7cn_prewrite(uint32_t capture,unsigned postpopulation)
{
    uint32_t anchor;
    /* A write/identity boundary, including stopped runtime cleanup. A foreign
     * or reentrant writer cannot resume after merely disabling admission. */
    if(!enter((uint32_t)(uintptr_t)&anchor,false))return;
    if(!span(capture,24084) || postpopulation>1u)fault(7);
    ep7c_prewrite_capture(&ep7_controller_sidecar_unresolved,state(),capture,postpopulation!=0);
    wait_revoke(0,capture);
    leave();
}
void ep7cn_population(uint32_t node,unsigned finish)
{
    uint32_t anchor;uint64_t token;unsigned s;ep7c_prefix v;ep7r *r;
    r=enter((uint32_t)(uintptr_t)&anchor,true);if(!r)return;
    s=state();if(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,s,node,&token)){leave();return;}
    bool read=prefix(s,node,token,&v);
    if(finish)(void)ep7c_finish_population(&ep7_controller_sidecar_unresolved,s,node,token,read?&v:NULL,true);
    else (void)ep7c_sample_population(&ep7_controller_sidecar_unresolved,s,node,token,read?&v:NULL,true,r->boot->core);
    leave();
}
void ep7cn_free(uint32_t node)
{
    uint32_t anchor;uint64_t token;unsigned s;
    if(!enter((uint32_t)(uintptr_t)&anchor,false))return;
    s=state();
    if(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,s,node,&token))
        (void)ep7c_forget(&ep7_controller_sidecar_unresolved,s,node,token);
    leave();
}
void ep7cn_release_capture(uint32_t registry)
{
    uint32_t anchor,capture;
    if(!enter((uint32_t)(uintptr_t)&anchor,false))return;
    /* A2 is the live native row at be5d; +12 is its actual allocated pointer.
     * Revoke the old owned allocation. Do not interpret the UDF index opcode. */
    if(!span(registry,20))fault(6);
    capture=word(registry+12);
    if(!capture)fault(6);
    ep7c_retire_capture(&ep7_controller_sidecar_unresolved,state(),capture);
    wait_revoke(0,capture);
    leave();
}
void ep7cn_associated_recycle(uint32_t pool,uint32_t header)
{
    uint32_t anchor;
    /* Generic native allocator also serves four unrelated pools. Do not query
     * their task/runtime, nor dereference their header, at this shared seam. */
    if(pool!=ASSOCIATED_POOL)return;
    if(!enter((uint32_t)(uintptr_t)&anchor,false))return;
    if(header>UINT32_MAX-4u || !associated_slot(header+4u) || word(header)!=0)fault(8);
    ep7c_retire_associated(&ep7_controller_sidecar_unresolved,state(),header+4u);
    wait_revoke(header+4u,0);
    leave();
}
void ep7cn_associated_reset(void)
{
    uint32_t anchor;
    if(!enter((uint32_t)(uintptr_t)&anchor,false))return;
    /* Fixed pool's initializer CALL only. Revoke before resetting counts/list,
     * preserving token serials even if old node objects have not been freed. */
    for(unsigned i=0;i<ASSOCIATED_COUNT;i++)
        ep7c_retire_associated(&ep7_controller_sidecar_unresolved,state(),ASSOCIATED_BACKING+4u+16u*i);
    wait_revoke(0,0);
    leave();
}
static bool capture_snapshot_locked(uint32_t id,uint32_t associated,ep7p_snapshot *out,uint32_t *capture)
{
    uint32_t node;uint64_t token;unsigned s;ep7c_prefix v;bool read,result=false;
    if(!out || id<1 || id>25 || !associated_slot(associated))return false;
    /* Associated is live in the reviewed c3de/c3f6 producer invocation. Its node
     * backlink is not read on fresh-node registration, where it is not set yet. */
    s=state();
    if(!associated_live(associated)) {
        ep7c_retire_associated(&ep7_controller_sidecar_unresolved,s,associated);
        wait_revoke(associated,0);goto done;
    }
    node=word(associated+8);
    if(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,s,node,&token))goto done;
    read=prefix(s,node,token,&v);
    if(read && (v.associated!=associated || v.capture_id!=id || word(associated)!=id))read=false;
    /* Even failed prefix validation burns an early/unsealed sampling chance. */
    result=ep7c_copyout(&ep7_controller_sidecar_unresolved,s,node,token,read?&v:NULL,out);
    if(result&&capture)*capture=v.capture;
done:return result;
}
bool ep7q_capture_snapshot_unresolved(uint32_t id,uint32_t associated,ep7p_snapshot *out)
{
    uint32_t anchor;bool result;
    if(!out || id<1 || id>25 || !associated_slot(associated) ||
       !enter((uint32_t)(uintptr_t)&anchor,true))return false;
    result=capture_snapshot_locked(id,associated,out,NULL);leave();return result;
}
static unsigned half(uint32_t p) { return *(const volatile uint16_t *)(uintptr_t)p; }
static void wait_sync(uint32_t queue)
{
    if(queue!=WAIT_QUEUE || word(0x6223e7dcu)!=WAIT_QUEUE || word(queue)!=182u ||
       half(queue+4u)!=WAIT_CAP || half(queue+6u)!=4u || word(queue+8u)!=WAIT_BACKING)fault(9);
    unsigned count=half(queue+12u),tail=half(queue+14u),head=half(queue+16u);
    if(count>WAIT_CAP || tail>=WAIT_CAP || head>=WAIT_CAP || tail!=(head+count)%WAIT_CAP)fault(9);
    if(!waiting.tracked) {
        /* Values already present at publication remain neutral forever. */
        memset(&waiting,0,sizeof waiting);waiting.tracked=true;
        waiting.count=count;waiting.tail=tail;waiting.head=head;
    }else if(waiting.count!=count || waiting.tail!=tail || waiting.head!=head)fault(9);
}
extern uint32_t ep7_gcc_wait_enqueue(uint32_t queue,uint32_t associated);
extern uint32_t ep7_gcc_wait_pop(uint32_t queue);
extern const unsigned char ep7_wait_scope_native_return[];
uint32_t ep7cn_wait_enqueue(uint32_t queue,uint32_t associated)
{
    uint32_t anchor,result;ep7r *r=enter((uint32_t)(uintptr_t)&anchor,false);
    if(!r)return ep7_gcc_wait_enqueue(queue,associated);
    wait_sync(queue);unsigned tail=waiting.tail;bool room=waiting.count<WAIT_CAP;
    if(room) {
        wait_entry *e=&waiting.entries[tail];memset(e,0,sizeof *e);e->associated=associated;
        if(ep7r_accepting(r) && associated_live(associated)) {
            ep7p_snapshot snapshot;uint32_t id=word(associated),capture=0;
            if(capture_snapshot_locked(id,associated,&snapshot,&capture)) {
                e->capture=capture;e->generation=ep7_controller_sidecar_unresolved.generation;
                ep7q_capture_scope_init(&e->scope,id,&snapshot);
            }
        }
    }
    /* Keep busy across the real operation, including its native error handler.
     * A hooked reentrant mutator cannot resume and invalidate our input. */
    result=ep7_gcc_wait_enqueue(queue,associated);
    if(result!=(room?4u:0u))fault(9);
    if(room) {
        if(word(WAIT_BACKING+4u*tail)!=associated)fault(9);
        waiting.count++;waiting.tail=(tail+1u)%WAIT_CAP;
    }
    wait_sync(queue);leave();return result;
}
uint32_t ep7cn_wait_pop(uint32_t queue,uint32_t wrapper_sp)
{
    uint32_t result,scope_address=0;ep7q_capture_scope *scope=NULL;
    ep7r *r=enter(wrapper_sp,false);
    if(atomic_load_explicit(&owner_chosen,memory_order_acquire)) {
        /* enter has revalidated this pinned task even on closed/poisoned paths.
         * Clear a previous rejected pop before attempting ANY next native pop. */
        ep7q_stack s={(const unsigned char *)(uintptr_t)owner.stack_low,owner.stack_low,owner.stack_bytes,true};
        if(!ep7q_wait_pop_layout(&s,wrapper_sp,(uint32_t)(uintptr_t)ep7_wait_scope_native_return,&scope_address))fault(10);
        scope=(ep7q_capture_scope *)(uintptr_t)scope_address;
        if(scope)ep7q_capture_scope_init(scope,0,NULL);
    }
    if(!r)return ep7_gcc_wait_pop(queue);
    wait_sync(queue);unsigned head=waiting.head;bool present=waiting.count!=0;
    uint32_t expected=present?word(WAIT_BACKING+4u*head):0;
    wait_entry *e=&waiting.entries[head];
    if(present && e->associated && e->associated!=expected)fault(9);
    result=ep7_gcc_wait_pop(queue);
    if(result!=expected)fault(9);
    if(present) {
        waiting.count--;waiting.head=(head+1u)%WAIT_CAP;wait_sync(queue);
        if(scope && ep7r_accepting(r) && !ep7_controller_sidecar_unresolved.poison && state()==33u &&
           ep7_controller_sidecar_unresolved.state==33u && e->associated==result &&
           e->generation==ep7_controller_sidecar_unresolved.generation && e->scope.state==EP7Q_SCOPE_AVAILABLE)
            *scope=e->scope;
        memset(e,0,sizeof *e);
    }else wait_sync(queue);
    leave();return result;
}
void ep7cn_wait_reset(void)
{
    uint32_t anchor;
    if(!enter((uint32_t)(uintptr_t)&anchor,false))return;
    memset(&waiting,0,sizeof waiting);leave();
}
