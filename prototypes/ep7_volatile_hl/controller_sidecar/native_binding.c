/* Exact native candidates. The G6 installer must establish supported object
 * lifetimes/exclusion and install ALL init/state/fresh/population/free/release
 * hooks before publication. Task checks do not create such a lifetime lease. */
#include "sidecar.h"
#include "native.h"
#include "../runtime/runtime.h"
#include "../snapshot_transport/native/producer.h"
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
    leave();
}
bool ep7q_capture_snapshot_unresolved(uint32_t id,uint32_t associated,ep7p_snapshot *out)
{
    uint32_t anchor,node;uint64_t token;unsigned s;ep7c_prefix v;bool read,result=false;
    if(!out || id<1 || id>25 || !associated_slot(associated) ||
       !enter((uint32_t)(uintptr_t)&anchor,true))return false;
    /* Associated is live in the reviewed c3de producer invocation. Its node
     * backlink is not read on fresh-node registration, where it is not set yet. */
    s=state();
    if(!associated_live(associated)) {
        ep7c_retire_associated(&ep7_controller_sidecar_unresolved,s,associated);goto done;
    }
    node=word(associated+8);
    if(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,s,node,&token))goto done;
    read=prefix(s,node,token,&v);
    if(read && (v.associated!=associated || v.capture_id!=id || word(associated)!=id))read=false;
    /* Even failed prefix validation burns an early/unsealed sampling chance. */
    result=ep7c_copyout(&ep7_controller_sidecar_unresolved,s,node,token,read?&v:NULL,out);
done:leave();return result;
}
