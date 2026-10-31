/* Exact native candidates. The G6 installer must establish supported object
 * lifetimes/exclusion and install ALL init/state/fresh/population/free/release
 * hooks before publication. Task checks do not create such a lifetime lease. */
#include "sidecar.h"
#include "../runtime/runtime.h"
#include "../snapshot_transport/native/producer.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only capture source");
extern void *ep7_gcc_capture_lookup(unsigned capture_id);
ep7c ep7_controller_sidecar_unresolved;
static atomic_bool closed=ATOMIC_VAR_INIT(false);
static bool owner_chosen;
static ep7n_task owner;
static uint32_t word(uint32_t p){return *(const volatile uint32_t *)(uintptr_t)p;}
static unsigned state(void){return *(const volatile uint16_t *)(uintptr_t)0x62234fc0u;}
static bool span(uint32_t p,uint32_t bytes){return p && !(p&3u) && p<=UINT32_MAX-bytes;}
static void close_capture(void){atomic_store_explicit(&closed,true,memory_order_release);}
static ep7r *context(uint32_t anchor,bool admitting)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7n_task t;
    if(!r || atomic_load_explicit(&closed,memory_order_acquire))return NULL;
    if(!ep7r_task(r,anchor,&t) || t.entry!=0x60289852u){close_capture();return NULL;}
    if(!ep7_controller_sidecar_unresolved.initialized || ep7_controller_sidecar_unresolved.poison)return NULL;
    if(owner_chosen){
        if(t.tid!=owner.tid || t.tcb!=owner.tcb || t.stack_low!=owner.stack_low || t.stack_bytes!=owner.stack_bytes){
            close_capture();return NULL;
        }
    }else{owner=t;owner_chosen=true;}
    if(admitting && !ep7r_accepting(r))return NULL;
    return r;
}
void ep7cn_initialize(unsigned initial)
{
    /* Exact inline site602897d7 before tasks use the controller. Never reset a
     * published/old sidecar on a subsequent native initialization. */
    if(initial!=0 || ep7_controller_sidecar_unresolved.initialized ||
       !ep7c_init(&ep7_controller_sidecar_unresolved,initial))close_capture();
}
void ep7_sidecar_transition_unresolved(unsigned old_state,unsigned pending)
{
    uint32_t anchor;
    if(context((uint32_t)(uintptr_t)&anchor,false))
        ep7c_transition(&ep7_controller_sidecar_unresolved,old_state,pending);
}
void ep7cn_fresh(uint32_t node)
{
    uint64_t token;uint32_t anchor,associated,id,capture;
    if(!context((uint32_t)(uintptr_t)&anchor,true) || !span(node,56))return;
    /* Original fresh allocator returned this fully initialized, still-owned
     * prefix; registration is BEFORE its caller can publish the node pointer. */
    id=word(node);associated=word(node+8);
    if(id<1 || id>25 || !span(associated,12))return;
    capture=(uint32_t)(uintptr_t)ep7_gcc_capture_lookup(id);
    if(!span(capture,24084))return;
    (void)ep7c_register_fresh_capture(&ep7_controller_sidecar_unresolved,state(),node,associated,id,capture,&token);
}
static bool prefix(unsigned observed_state,uint32_t node,uint64_t token,ep7c_prefix *out)
{
    uint32_t id,associated,capture;
    if(!span(node,56) || !ep7c_authorize(&ep7_controller_sidecar_unresolved,observed_state,node,token))return false;
    id=word(node);associated=word(node+8);
    if(id<1 || id>25 || !span(associated,12))return false;
    capture=(uint32_t)(uintptr_t)ep7_gcc_capture_lookup(id);
    if(!span(capture,24084))return false;
    *out=(ep7c_prefix){associated,capture,id,
        *(const volatile unsigned char *)(uintptr_t)(capture+24053),
        *(const volatile unsigned char *)(uintptr_t)(capture+24083)};
    return true;
}
void ep7cn_population(uint32_t node,unsigned finish)
{
    uint32_t anchor;uint64_t token;unsigned s;ep7c_prefix v;ep7r *r;
    r=context((uint32_t)(uintptr_t)&anchor,true);if(!r)return;
    s=state();if(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,s,node,&token))return;
    bool read=prefix(s,node,token,&v);
    if(finish)(void)ep7c_finish_population(&ep7_controller_sidecar_unresolved,s,node,token,read?&v:NULL,true);
    else (void)ep7c_sample_population(&ep7_controller_sidecar_unresolved,s,node,token,read?&v:NULL,true,r->boot->core);
}
void ep7cn_free(uint32_t node)
{
    uint32_t anchor;uint64_t token;unsigned s;
    if(!context((uint32_t)(uintptr_t)&anchor,false))return;
    s=state();
    if(ep7c_resolve_live(&ep7_controller_sidecar_unresolved,s,node,&token))
        (void)ep7c_forget(&ep7_controller_sidecar_unresolved,s,node,token);
}
void ep7cn_release_capture(uint32_t registry)
{
    uint32_t anchor,capture;
    if(!context((uint32_t)(uintptr_t)&anchor,false))return;
    /* A2 is the live native row at be5d; +12 is its actual allocated pointer.
     * Revoke the old owned allocation. Do not interpret the UDF index opcode. */
    if(!span(registry,20)){close_capture();return;}
    capture=word(registry+12);
    if(!capture){close_capture();return;}
    ep7c_retire_capture(&ep7_controller_sidecar_unresolved,state(),capture);
}
bool ep7q_capture_snapshot_unresolved(uint32_t id,uint32_t associated,ep7p_snapshot *out)
{
    uint32_t anchor,node;uint64_t token;unsigned s;ep7c_prefix v;bool read;
    if(!out || id<1 || id>25 || !span(associated,12) ||
       !context((uint32_t)(uintptr_t)&anchor,true))return false;
    /* Associated is live in the reviewed c3de producer invocation. Its node
     * backlink is not read on fresh-node registration, where it is not set yet. */
    node=word(associated+8);s=state();
    if(!ep7c_resolve_live(&ep7_controller_sidecar_unresolved,s,node,&token))return false;
    read=prefix(s,node,token,&v);
    if(read && (v.associated!=associated || v.capture_id!=id || word(associated)!=id))read=false;
    /* Even failed prefix validation burns an early/unsealed sampling chance. */
    return ep7c_copyout(&ep7_controller_sidecar_unresolved,s,node,token,read?&v:NULL,out);
}
