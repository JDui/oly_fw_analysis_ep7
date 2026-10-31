#include "runtime.h"
#include "../snapshot_transport/native/producer.h"
#include "../snapshot_transport/native/descriptor_receive.h"
#include "../snapshot_transport/native/descriptor_send.h"
#include "../snapshot_transport/native/worker.h"
#include "../snapshot_transport/native/ack.h"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
typedef struct {
    uint16_t tid;uint32_t entry;
    bool installed,task_valid,old_maximum,changed_instance,held;
    int poll_status,signal_status,delay_status;
    unsigned creates,deletes,delays,quarantines,last_reason;
    jmp_buf escape;
} fixture;
/* Static test storage remains defined across longjmp; the production runtime
 * never longjmps and never reinitializes published objects. */
static fixture f;
static ep7b boot;
static ep7p core;
static ep7r runtime;
static ep7t_ticket pending;
static ep7j_scope job;
static uint32_t allocation[EP7P_EXTENT/4];
static int get_tid(void *ctx,uint16_t *out)
{ fixture *m=ctx;*out=m->tid;return 0; }
static int create(void *ctx,const ep7b_sem_spec *spec)
{
    fixture *m=ctx;assert(!spec->attributes && spec->initial==1 && spec->maximum==1);
    m->creates++;return 1;
}
static int drop(void *ctx,unsigned handle)
{ fixture *m=ctx;assert(handle==1);m->deletes++;return 0; }
static int poll(void *ctx,uint16_t handle)
{
    fixture *m=ctx;assert(handle==1);
    if(m->poll_status)return m->poll_status;
    assert(!m->held);m->held=true;return 0;
}
static int signal_sem(void *ctx,uint16_t handle)
{ fixture *m=ctx;assert(handle==1 && m->held);m->held=false;return m->signal_status; }
static bool installed(void *ctx){return ((fixture *)ctx)->installed;}
static bool task(void *ctx,uint32_t anchor,ep7n_task *out)
{
    fixture *m=ctx;if(!m->task_valid)return false;
    *out=(ep7n_task){m->tid,(uint16_t)(m->tid>>12),0x1000,m->entry,anchor&~0xfffu,0x1000};
    return true;
}
static bool queue(void *ctx,unsigned handle,ep7n_queue *out)
{
    fixture *m=ctx;
    unsigned maximum=handle==0x4b?148:(handle==0x4d?300:312);
    unsigned ring=handle==0x4b?4864:(handle==0x4d?9728:10112);
    *out=(ep7n_queue){(uint16_t)handle,0,0x1000,0x2000,0x3000+64*handle,128,maximum,ring,0x100000+0x4000*handle};
    if(m->old_maximum && handle==0x4c)out->maximum=300;
    if(m->changed_instance)out->backing+=4;
    return true;
}
static int delay(void *ctx)
{ fixture *m=ctx;assert(!m->held);m->delays++;m->poll_status=0;return m->delay_status; }
static void quarantine(void *ctx,unsigned reason)
{ fixture *m=ctx;m->quarantines++;m->last_reason=reason;longjmp(m->escape,1); }
static void ticket(void)
{
    ep7p_snapshot s={0};s.hl[0]=3;
    assert(ep7t_prepare(&runtime.transport,0x10000,&s,&pending));
    assert(ep7t_publish(&runtime.transport,pending));
}
static bool retained(void)
{
    unsigned i;
    for(i=0;i<EP7T_CAP;i++)if(runtime.transport.entries[i].ticket.serial==pending.serial)return true;
    return false;
}
static void exercise_contexts(void)
{
    ep7q_materializer_context recv;ep7q_send_context send;ep7q_producer_context prod;
    ep7q_worker_context worker;ep7q_ack_context ack;
    f.entry=0x603df803;
    assert(ep7q_materializer_context_unresolved(0x4b,0x100100,&recv));
    assert(recv.stack.expanded_group_ready && recv.queue_context==&runtime && recv.qualify_queue(&runtime,0x4b,148));
    assert(ep7q_descriptor_send_context_unresolved(0x777,0x100100,&send));
    assert(send.forward.retirement_context==&runtime && send.forward.retire_owned==ep7r_retire);
    assert(ep7q_ack_context_unresolved(0x100100,&ack));
    assert(ack.transport==&runtime.transport && ack.wait_retirement==ep7r_progress);
    assert(ep7q_producer_context_unresolved(0x4b,0x100100,&prod));
    assert(prod.producer.transport==&runtime.transport);
    f.entry=0x603ef892;assert(ep7q_descriptor_receive_context_unresolved(0x4c,0x100100,&recv));
    assert(ep7q_descriptor_receive_context_unresolved(0x4d,0x100100,&recv));
    assert(!ep7q_descriptor_receive_context_unresolved(0xab,0x100100,&recv));
    f.entry=0x603ef94a;assert(ep7q_descriptor_receive_context_unresolved(0xab,0x100100,&recv));
    f.entry=0x603f26a1;assert(ep7q_descriptor_receive_context_unresolved(0x4f,0x100100,&recv));
    assert(ep7q_worker_context_unresolved(EP7Q_WORKER_CLEANUP,0x100100,&worker));
    assert(worker.core==&core && worker.transport==&runtime.transport && worker.wait_cleanup==ep7r_progress);
}
int main(void)
{
    ep7b_native n={&f,create,drop,{&f,get_tid,poll,signal_sem}};
    ep7r_environment env={&f,installed,task,queue,delay,quarantine};
    ep7q_worker_context worker;ep7q_ack_context ack;ep7q_producer_context prod;ep7p_snapshot s={0};
    f.tid=0x6c;f.entry=0x603f26a1;f.task_valid=true;
    assert(!ep7r_get(&ep7_native_runtime_slot));ep7q_owned_context_lost();
    assert(ep7b_prepare(&boot,&core,n));assert(ep7r_prepare(&runtime,&boot,env));
    assert(!ep7r_publish(&ep7_native_runtime_slot,&runtime));assert(!ep7r_accepting(&runtime));
    f.installed=true;f.old_maximum=true;assert(!ep7r_publish(&ep7_native_runtime_slot,&runtime));
    assert(!ep7r_get(&ep7_native_runtime_slot) && boot.state==EP7B_PREPARED);
    f.old_maximum=false;assert(ep7r_publish(&ep7_native_runtime_slot,&runtime));
    assert(ep7r_accepting(&runtime) && !ep7r_publish(&ep7_native_runtime_slot,&runtime));
    assert(!ep7b_abort_unpublished(&boot) && !f.deletes && f.creates==1);
    exercise_contexts();
    ticket();f.poll_status=-50;ep7r_retire(&runtime,pending);
    assert(f.delays==1 && !retained() && !f.quarantines);
    ticket();ep7r_stop(&runtime);
    assert(!ep7q_producer_context_unresolved(0x4b,0x100100,&prod));
    assert(ep7q_worker_context_unresolved(EP7Q_WORKER_CLEANUP,0x100100,&worker));
    assert(ep7q_ack_context_unresolved(0x100100,&ack));
    assert(ep7r_qualify_queue(&runtime,0x4f,312));ep7r_retire(&runtime,pending);assert(!retained());
    assert(core.ops.lock(core.ops.ctx));
    if(!setjmp(f.escape)){ep7r_progress(&runtime);assert(!"slept while owning core lock");}
    assert(f.last_reason==EP7R_FAULT_CONTEXT && f.held && f.delays==1);
    core.ops.unlock(core.ops.ctx); /* Fixture resumes after simulated quarantine only. */
    /* Delay failure must escape only to the fixture, retaining the full key. */
    ticket();f.poll_status=-50;f.delay_status=-25;
    if(!setjmp(f.escape)){ep7r_retire(&runtime,pending);assert(!"cleanup returned after failed delay");}
    assert(f.last_reason==EP7R_FAULT_DELAY && retained());f.delay_status=0;
    ep7r_retire(&runtime,pending);assert(!retained());
    f.changed_instance=true;
    if(!setjmp(f.escape)){(void)ep7r_qualify_queue(&runtime,0x4c,312);assert(!"changed queue was accepted");}
    assert(f.last_reason==EP7R_FAULT_QUEUE);f.changed_instance=false;
    /* Keep a real core job and a transport ticket live while native poll poisons. */
    s.hl[0]=4;assert(ep7p_register_job(&core,allocation,sizeof allocation,&s,&job.job));
    job.state=EP7J_REGISTERED;ticket();f.poll_status=-42;
    if(!setjmp(f.escape)){ep7r_retire(&runtime,pending);assert(!"poisoned cleanup returned");}
    assert(f.last_reason==EP7R_FAULT_LOCK && ep7s_poisoned(&boot.provider) && retained());
    assert(!ep7r_accepting(&runtime) && ep7r_get(&ep7_native_runtime_slot)==&runtime);
    assert(ep7q_worker_context_unresolved(EP7Q_WORKER_CLEANUP,0x100100,&worker));
    assert(ep7q_ack_context_unresolved(0x100100,&ack));
    assert(!ep7j_revoke(&job,worker.core) && job.job && core.jobs[0].token==job.job);
    if(!setjmp(f.escape)){ep7q_owned_context_lost();assert(!"lost owned layout returned");}
    assert(f.last_reason==EP7R_FAULT_OWNED_LAYOUT && job.job && retained());
    f.task_valid=false;
    if(!setjmp(f.escape)){(void)ep7q_ack_context_unresolved(0x100100,&ack);assert(!"lost task context returned");}
    assert(f.last_reason==EP7R_FAULT_CONTEXT && job.job && retained() && !f.deletes);
    puts("runtime: permanent publication, real bootstrap/core/transport, six providers, contention progress and retained poison/delay/context/queue failures passed; native environment mocked");
    return 0;
}
