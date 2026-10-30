/* Self-authored host test: real router/raw/UI/core; mocked native admission. */
#include "bridge.h"
#include "text.h"
#include "ep7p_lifecycle.h"
#include "controller_sidecar/sidecar.h"
#include "snapshot_transport/transport.h"
#include "snapshot_transport/wire.h"
#include "snapshot_transport/owned_io.h"
#include "snapshot_transport/consumer.h"
#include "snapshot_transport/native/materializer.h"
#include "snapshot_transport/native/descriptor_receive.h"
#include "snapshot_transport/native/descriptor_send.h"
#include "snapshot_transport/native/producer.h"
#include "snapshot_transport/native/queue.h"
#include "snapshot_transport/native/worker.h"
#include "snapshot_transport/native/ack.h"
#include "runtime/task_context.h"
#include <stdlib.h>
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
static ep7p core;
static ep7p_ui ui;
static struct ep7_ui_session session={1,0};
static bool renderer_ready, modal_blocked, known_stock, fail_lock, held;
static unsigned admissions,current_queries;
static int32_t full_delta;
static unsigned widget_token, text_calls;
static int setter_status=1;
static uint16_t copied_text[EP7_TEXT_UNITS];
int ep7_gcc_set_text_unresolved_binding(void *widget,const uint16_t *text){
    size_t i;assert(widget==&widget_token);++text_calls;
    for(i=0;i<EP7_TEXT_UNITS;i++){copied_text[i]=text[i];if(!text[i])break;}
    assert(i<EP7_TEXT_UNITS);return setter_status;
}
static void text_is(struct ep7_ui_frame f,const char *expected){
    size_t i;assert(ep7_text_present(&widget_token,&f)==1);
    for(i=0;expected[i];i++)assert(copied_text[i]==(unsigned char)expected[i]);
    assert(copied_text[i]==0);
}
static bool lock(void *p){(void)p;assert(!held);if(fail_lock)return false;held=true;return true;}
static void unlock(void *p){(void)p;assert(held);held=false;}
static int current(void *p,ep7p_task *t){(void)p;(void)t;++current_queries;return -1;}
int ep7_ui_native_admit_unresolved(const struct ep7_native_ui_input *in,struct ep7_ui_admission *a){
    ++admissions;
    /* Single-thread fixture owns UI execution; these booleans simulate missing
       native qualification. They are NOT evidence of a native renderer. */
    if(known_stock)return EP7_NATIVE_STOCK;
    if(in->parent!=0x12340000u || !renderer_ready || modal_blocked)return EP7_NATIVE_REJECT;
    a->ui=&ui;a->session=session;a->synchronized_full_delta=full_delta;
    return EP7_NATIVE_OWNED;
}
static uint32_t send(uint32_t event,int32_t delta){
    struct ep7_native_ui_input in={event,1,0x12340000u};
    full_delta=delta;return ep7_gcc_ui_route(&in);
}
static struct ep7_ui_frame frame(void){
    struct ep7_ui_frame f;assert(ep7p_ui_ops.frame(&ui,session,&f)==EP7_UI_UNCHANGED);return f;
}
static void unchanged(ep7p_snapshot before){
    ep7p_snapshot after;assert(ep7p_capture(&core,11,4,&after));
    assert(before.profile==after.profile);
    assert(!memcmp(before.hl,after.hl,sizeof before.hl));
}
/* Actual lifecycle callbacks are host-owned malloc/byte fixtures, not native ABI. */
typedef struct {unsigned char *owner,*job;unsigned slot,cleanups;bool neutral;unsigned char output[EP7P_OUTPUT];} capture_host;
static void put16(unsigned char *p,unsigned v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);}
static void put32(unsigned char *p,uint32_t v){unsigned i;for(i=0;i<4;i++)p[i]=(unsigned char)(v>>(8*i));}
static int construct(void *ctx,void *descriptor,ep7l_allocation *a){
    capture_host *h=ctx;assert(descriptor==h && !h->owner);
    h->owner=malloc(EP7P_EXTENT+64u);assert(h->owner);h->job=h->owner+64;
    /* Offset prevents common sanitizer low32-zero address. Refuse wire overflow;
       these 32-bit backlinks are compared, never dereferenced as host pointers. */
    assert((uint32_t)(uintptr_t)h->job && (uint32_t)(uintptr_t)h->job<=UINT32_MAX-EP7P_EXTENT);
    memset(h->job,0,EP7P_EXTENT);*a=(ep7l_allocation){h->job,EP7P_EXTENT,true};return 0;
}
static int convert(void *ctx,void *descriptor){
    capture_host *h=ctx;unsigned char *b=h->job,*r=b+11364,*op=b+14576+56*h->slot;
    uint32_t base=(uint32_t)(uintptr_t)b;assert(descriptor==h);
    put16(b+11312,2);put16(b+11314,3);put32(b+10984+24,0x6036884d);
    put32(r,0x60355fd4);put32(r+4,base+14576+56*h->slot);put16(r+10,11);put16(r+28,0x100);
    put32(op,base);put32(op+8,base+11364);return 0;
}
static int process(void *ctx,void *descriptor,ep7l_reader reader,void *reader_ctx){
    capture_host *h=ctx;assert(descriptor==h);memset(h->output,0x5a,sizeof h->output);
    assert(reader(reader_ctx,(uintptr_t)h->job+11364,h->output,sizeof h->output)==!h->neutral);
    return -123; /* preserve mock native status independently of H/L success */
}
static void cleanup(void *ctx,void *descriptor){
    capture_host *h=ctx;unsigned i;assert(descriptor==h);
    for(i=0;i<EP7P_CAP;i++)assert(!core.jobs[i].token);
    free(h->owner);h->owner=NULL;h->job=NULL;++h->cleanups;
}
static void transport_boundaries(void){
    ep7t t={0};ep7t_ticket old,now,all[EP7T_CAP],sentinel={99,99};unsigned i;
    ep7p_snapshot source={3,{0}},out={1,{0}};
    source.hl[0]=7;source.hl[23]=-7;
    assert(ep7t_init(&t,(ep7p_ops){NULL,lock,unlock,current}));
    assert(ep7t_prepare(&t,1,&source,&old));
    assert(!ep7t_claim(&t,old,&out) && out.profile==1); /* early, burned */
    assert(!ep7t_publish(&t,old));assert(ep7t_retire(&t,old));
    assert(ep7t_prepare(&t,1,&source,&now) && now.serial!=old.serial);
    assert(ep7t_publish(&t,now));
    assert(!ep7t_claim(&t,old,&out) && out.profile==1); /* reused address */
    assert(!ep7t_retire(&t,old));
    assert(ep7t_retire_owned(&t,old)); /* absent old key must not clear now */
    assert(!ep7t_prepare(&t,1,&source,&sentinel) && sentinel.serial==99);
    fail_lock=true;
    assert(!ep7t_claim(&t,now,&out) && out.profile==1);
    assert(!ep7t_retire(&t,now));
    fail_lock=false;
    assert(t.entries[0].ticket.serial==now.serial);
    /* Consumer stays neutral after failed claim; retry cleanup only. */
    assert(ep7t_retire(&t,now));assert(!ep7t_claim(&t,now,&out));
    assert(ep7t_prepare(&t,1,&source,&now));assert(ep7t_publish(&t,now));
    assert(ep7t_retire(&t,now)); /* send failure / cancellation before receive */
    assert(!ep7t_claim(&t,now,&out) && out.profile==1);
    for(i=0;i<EP7T_CAP;i++)assert(ep7t_prepare(&t,i+1,&source,&all[i]));
    assert(!ep7t_prepare(&t,100,&source,&sentinel) && sentinel.serial==99);
    assert(ep7t_publish(&t,all[0]));
    source.hl[0]=0; /* independently frozen */
    assert(ep7t_claim(&t,all[0],&out) && out.hl[0]==7 && out.hl[23]==-7);
    out.hl[0]=2;assert(!ep7t_claim(&t,all[0],&out) && out.hl[0]==2);
    assert(!ep7t_publish(&t,all[0]));
    assert(!ep7t_init(&t,(ep7p_ops){NULL,lock,unlock,current}));
    /* Teardown clears prepared/published/consumed records without resetting the
       serial or changing an independently claimed snapshot. Failed lock cannot
       report success; retries are cleanup, not a new snapshot sampling attempt. */
    assert(ep7t_publish(&t,all[1]));
    fail_lock=true;assert(!ep7t_invalidate_all(&t));fail_lock=false;
    assert(t.entries[1].ticket.serial==all[1].serial);
    assert(ep7t_invalidate_all(&t));assert(ep7t_invalidate_all(&t));
    assert(out.hl[0]==2 && out.hl[23]==-7);
    for(i=0;i<EP7T_CAP;i++)assert(!ep7t_claim(&t,all[i],&out));
    assert(!ep7t_publish(&t,all[1]));
    assert(ep7t_prepare(&t,1,&source,&now) && now.serial>all[EP7T_CAP-1].serial);
    assert(!ep7t_claim(&t,all[0],&out));
    /* Serial exhaustion refuses new work, keeps existing cleanup usable. */
    t.serial=UINT64_MAX;
    assert(ep7t_retire(&t,now));
    assert(!ep7t_prepare(&t,1,&source,&sentinel) && sentinel.serial==99);
}
static void wire_boundaries(void){
    unsigned char cmd[EP7W_COMMAND]={0},wire[EP7W_MAX],out[EP7W_DESCRIPTOR];
    ep7t_ticket t={100,UINT64_C(0xfedcba9876543210)},received={0};size_t n=99;
    put32(cmd+8,19);put32(cmd+12,100);memset(wire,0xa5,sizeof wire);
    assert(!ep7w_encode(EP7W_COMMAND,cmd,t,wire,27,&n) && n==99 && wire[0]==0xa5);
    assert(ep7w_encode(EP7W_COMMAND,cmd,t,wire,sizeof wire,&n) && n==28);
    assert(wire[16]=='E' && wire[17]=='7' && wire[18]=='T' && wire[19]=='1');
    assert(wire[20]==0x10 && wire[21]==0x32 && wire[26]==0xdc && wire[27]==0xfe);
    assert(!memcmp(wire,cmd,sizeof cmd));
    assert(ep7w_decode(EP7W_COMMAND,wire,n,out,sizeof out,&received)==EP7W_TAGGED);
    assert(received.metadata==t.metadata && received.serial==t.serial);
    memset(out,0x5a,sizeof out);
    assert(ep7w_decode(EP7W_COMMAND,wire,27,out,sizeof out,&received)==EP7W_REJECT);
    assert(!received.serial && !received.metadata && out[0]==0x5a);
    assert(ep7w_decode(EP7W_COMMAND,wire,28,out,15,&received)==EP7W_REJECT && out[0]==0x5a);
    /* Actual 16-byte legacy receive must ignore stale tail bytes in scratch. */
    received=t;
    assert(ep7w_decode(EP7W_COMMAND,wire,16,out,sizeof out,&received)==EP7W_LEGACY);
    assert(!received.serial && !memcmp(out,cmd,sizeof cmd));
    wire[16]^=1;
    assert(ep7w_decode(EP7W_COMMAND,wire,28,out,sizeof out,&received)==EP7W_LEGACY);
    assert(!received.serial && !memcmp(out,cmd,sizeof cmd));
    wire[16]^=1;memset(wire+20,0,8);
    assert(ep7w_decode(EP7W_COMMAND,wire,28,out,sizeof out,&received)==EP7W_LEGACY);
    t.metadata=101;n=99;assert(!ep7w_encode(EP7W_COMMAND,cmd,t,wire,sizeof wire,&n) && n==99);
    t.metadata=100;put32(cmd+8,16);
    assert(!ep7w_encode(EP7W_COMMAND,cmd,t,wire,sizeof wire,&n));
    assert(ep7w_encode(EP7W_COMMAND,cmd,(ep7t_ticket){0},wire,sizeof wire,&n) && n==16);
}
typedef struct {
    unsigned char bytes[EP7W_MAX];unsigned length,maximum,receives,sends;
    int raw;bool qualified;
    ep7t *claim_transport;bool claimed,fail_lock_after_send;ep7p_snapshot claimed_snapshot;
} queue_fixture;
static bool qualify_queue(void *ctx,unsigned handle,unsigned maximum){
    queue_fixture *q=ctx;assert(handle && maximum<=EP7W_MAX);
    q->maximum=maximum;return q->qualified;
}
static int receive_queue(void *ctx,unsigned handle,void *out,int timeout){
    queue_fixture *q=ctx;(void)handle;assert(timeout==0 || timeout==-1);++q->receives;
    assert(q->length<=q->maximum);memcpy(out,q->bytes,q->length);return q->raw;
}
static int send_queue(void *ctx,unsigned handle,const void *in,unsigned bytes,int timeout){
    queue_fixture *q=ctx;(void)handle;assert(timeout==-1);++q->sends;
    assert(bytes<=q->maximum);memcpy(q->bytes,in,bytes);q->length=bytes;
    if(q->claim_transport && handle==0x4b && bytes==28 && q->raw>=0){
        ep7t_ticket ticket;assert(ep7w_ticket(16,q->bytes,bytes,&ticket)==EP7W_TAGGED);
        q->claimed=ep7t_claim(q->claim_transport,ticket,&q->claimed_snapshot);assert(q->claimed);
    }
    if(q->fail_lock_after_send)fail_lock=true;
    return q->raw;
}
static ep7q_ops queue_ops(queue_fixture *q)
{ ep7q_ops ops={q,qualify_queue,receive_queue,send_queue};return ops; }
/* Models the named native send's normalized result and notification. The C
   status adapter is real; its MN10300 veneer/native wrapper are not executed. */
static queue_fixture *named_queue_fixture;
static unsigned named_notifications;
int ep7_gcc_queue_send_preserving_hooks(unsigned handle,const void *p,unsigned bytes,int timeout){
    int status;assert(named_queue_fixture);
    status=send_queue(named_queue_fixture,handle,p,bytes,timeout);++named_notifications;return status;
}
static void consumer_boundaries(void){
    ep7t transport={0};ep7t_ticket ticket,read;ep7p_snapshot frozen={3,{0}},out={1,{0}};
    unsigned char descriptor[EP7W_MAX]={0},prefix[300],guard[300];unsigned scenario;
    assert(ep7t_init(&transport,(ep7p_ops){NULL,lock,unlock,current}));frozen.hl[0]=7;
    put32(descriptor+48,100);put32(descriptor+52,19);put16(descriptor+194,0x2001);
    memcpy(prefix,descriptor,300);
    /* Success, failed claim lock, and unsupported route are each one attempt. */
    for(scenario=0;scenario<3;scenario++){
        assert(ep7t_prepare(&transport,100,&frozen,&ticket) && ep7t_publish(&transport,ticket));
        memcpy(descriptor,prefix,300);assert(ep7w_write_trailer(descriptor+300,ticket));
        out.profile=1;out.hl[0]=2;
        if(scenario==1)fail_lock=true;
        if(scenario==2)put32(descriptor+52,16);
        assert(ep7q_claim_owned(&transport,descriptor,sizeof descriptor,&out)==(scenario==0));
        assert(out.profile==(scenario==0?3u:1u) && out.hl[0]==(scenario==0?7:2));
        fail_lock=false;put32(descriptor+52,19);
        assert(!ep7q_claim_owned(&transport,descriptor,sizeof descriptor,&out));
        assert(ep7w_ticket(300,descriptor,sizeof descriptor,&read)==EP7W_LEGACY && !read.serial);
        assert(ep7w_retirement_ticket(descriptor,&read) && read.serial==ticket.serial);
        fail_lock=true;assert(!ep7q_retire_owned(&transport,descriptor,sizeof descriptor));
        assert(ep7w_retirement_ticket(descriptor,&read) && read.serial==ticket.serial);
        fail_lock=false;assert(ep7q_retire_owned(&transport,descriptor,sizeof descriptor));
        assert(ep7q_retire_owned(&transport,descriptor,sizeof descriptor));
        assert(!ep7w_retirement_ticket(descriptor,&read) && !read.serial);
        assert(!ep7t_claim(&transport,ticket,&out));
        assert(out.hl[0]==(scenario==0?7:2)); /* independent value survives cleanup */
        assert(!memcmp(descriptor,prefix,300));
    }
    /* Drain a published but never claimed descriptor; external cancellation is
       already complete and remains idempotent at ACK. */
    assert(ep7t_prepare(&transport,100,&frozen,&ticket) && ep7t_publish(&transport,ticket));
    assert(ep7w_write_trailer(descriptor+300,ticket));
    assert(ep7t_retire_owned(&transport,ticket));
    assert(ep7q_retire_owned(&transport,descriptor,sizeof descriptor));
    memset(guard,0x5a,sizeof guard);
    assert(!ep7q_claim_owned(&transport,guard,sizeof guard,&out));
    assert(!ep7q_retire_owned(&transport,guard,sizeof guard) && guard[299]==0x5a);
}
typedef struct {capture_host host;unsigned requested;bool allocation_fails;} worker_fixture;
static void *worker_allocate(void *ctx,unsigned size){
    worker_fixture *f=ctx;f->requested=size;
    if(f->allocation_fails)return NULL;
    f->host.owner=malloc(size+64u);assert(f->host.owner);f->host.job=f->host.owner+64;
    assert((uint32_t)(uintptr_t)f->host.job && (uint32_t)(uintptr_t)f->host.job<=UINT32_MAX-size);
    memset(f->host.job,0xa5,size);return f->host.job;
}
static void worker_boundaries(void){
    ep7t transport={0};ep7t_ticket ticket;ep7j_scope scope;ep7p_snapshot frozen={3,{0}};
    unsigned char descriptor[EP7W_MAX]={0},output[EP7P_OUTPUT];worker_fixture f={0};unsigned i,scenario;void *allocation;
    unsigned char bytes[556]={0};uint32_t w=0x5000,label=0x70002000;ep7q_worker_args args;
    ep7q_stack stack={bytes,w,sizeof bytes,true};
    static const unsigned layouts[][6]={
        {EP7Q_WORKER_ENTER,0,0,32,140,136},
        {EP7Q_WORKER_ALLOCATE,4,0x603537fa,136,244,240},
        {EP7Q_WORKER_PROCESS,24,0x603f2897,112,220,216},
        {EP7Q_WORKER_CLEANUP,24,0x603f28c7,112,220,216}
    };
    for(i=0;i<4;i++){
        unsigned owner=layouts[i][0]==EP7Q_WORKER_ALLOCATE?104:80;
        memset(bytes,0,sizeof bytes);stack.extent=layouts[i][4]+312;
        if(i){put32(bytes+layouts[i][1],layouts[i][2]);put32(bytes+owner,label);}
        if(i==1)put32(bytes+48,0x603f2845);
        put32(bytes+layouts[i][5],0x603f2727);put32(bytes+layouts[i][3]-8,w+layouts[i][4]);
        assert(ep7q_worker_layout(&stack,w,layouts[i][0],w+layouts[i][4],label,&args));
        assert(args.scope==w+layouts[i][3] && args.descriptor==w+layouts[i][4]);
        --stack.extent;assert(!ep7q_worker_layout(&stack,w,layouts[i][0],w+layouts[i][4],label,&args));++stack.extent;
        if(i){put32(bytes+owner,0x603f2727);assert(!ep7q_worker_layout(&stack,w,layouts[i][0],w+layouts[i][4],label,&args));}
    }
    stack.expanded_group_ready=false;stack.bytes=(const unsigned char *)(uintptr_t)1;
    assert(!ep7q_worker_layout(&stack,w,EP7Q_WORKER_ENTER,w+140,label,&args));
    assert(ep7t_init(&transport,(ep7p_ops){NULL,lock,unlock,current}));frozen.hl[0]=3;
    put32(descriptor+48,100);put32(descriptor+52,19);put16(descriptor+194,0x2001);
    for(scenario=0;scenario<4;scenario++){
        assert(ep7t_prepare(&transport,100,&frozen,&ticket) && ep7t_publish(&transport,ticket));
        assert(ep7w_write_trailer(descriptor+300,ticket));ep7j_begin(&scope,&transport,descriptor,sizeof descriptor);
        assert(scope.state==EP7J_FROZEN);assert(ep7q_retire_owned(&transport,descriptor,sizeof descriptor));
        f.allocation_fails=scenario==3;
        allocation=ep7j_allocate(&scope,EP7P_STOCK,worker_allocate,&f);
        assert(allocation==f.host.job && f.requested==EP7P_EXTENT);
        if(f.allocation_fails){assert(!scope.allocation && !ep7j_register(&scope,&core,NULL));continue;}
        assert(f.host.job[0]==0xa5 && f.host.job[EP7P_STOCK-1]==0xa5);
        for(i=EP7P_STOCK;i<EP7P_EXTENT;i++)assert(f.host.job[i]==0);
        memset(f.host.job,0,EP7P_STOCK);assert(convert(&f.host,&f.host)==0);
        if(scenario==1)fail_lock=true;
        assert(ep7j_register(&scope,&core,scenario==2?NULL:f.host.job)==(scenario==0));
        fail_lock=false;assert(!ep7j_register(&scope,&core,f.host.job));
        memset(output,0x5a,sizeof output);
        assert(ep7p_direct_apply(&core,(uintptr_t)f.host.job+11364,output,sizeof output)==(scenario==0));
        if(scenario==0){
            assert(output[706]==0x48 && output[707]==0xf4);
            fail_lock=true;assert(!ep7j_revoke(&scope,&core) && scope.job);fail_lock=false;
        }else for(i=0;i<sizeof output;i++)assert(output[i]==0x5a);
        assert(ep7j_revoke(&scope,&core) && !scope.job);assert(ep7j_revoke(&scope,&core));
        cleanup(&f.host,&f.host);
    }
    /* No captured capability uses exactly the stock request and cannot register. */
    ep7j_begin(&scope,NULL,NULL,0);f.allocation_fails=false;
    allocation=ep7j_allocate(&scope,EP7P_STOCK,worker_allocate,&f);
    assert(allocation==f.host.job && f.requested==EP7P_STOCK);
    assert(!ep7j_register(&scope,&core,f.host.job));cleanup(&f.host,&f.host);
}
static void ack_boundaries(void){
    static const uint32_t cases[][3]={
        {0x603dfc6c,100,EP7Q_ACK_NORMAL},{0x603e05cb,44,EP7Q_ACK_DRAIN},{0x603f2770,36,EP7Q_ACK_WORKER}
    };
    unsigned char bytes[412]={0},prefix[300];uint32_t w=0x6000;unsigned i,notifications=0;
    ep7q_stack stack={bytes,w,sizeof bytes,true};ep7q_ack_args args;
    ep7t transport={0};ep7t_ticket ticket;ep7p_snapshot frozen={3,{0}},out;
    assert(ep7t_init(&transport,(ep7p_ops){NULL,lock,unlock,current}));
    for(i=0;i<3;i++){
        unsigned char *d=bytes+cases[i][1];memset(bytes,0,sizeof bytes);
        put32(bytes+32,cases[i][0]);if(!i)put32(bytes+80,0x603df8c0);
        stack.extent=cases[i][1]+312;
        assert(ep7q_ack_layout(&stack,w,w+cases[i][1],&args) && args.origin==cases[i][2]);
        --stack.extent;assert(!ep7q_ack_layout(&stack,w,w+cases[i][1],&args));++stack.extent;
        assert(!ep7q_ack_layout(&stack,w,w+cases[i][1]+4,&args));
        put32(d+48,100);put32(d+52,19);put16(d+194,0x2001);
        assert(ep7t_prepare(&transport,100,&frozen,&ticket) && ep7t_publish(&transport,ticket));
        assert(ep7w_write_trailer(d+300,ticket));
        if(i==2)assert(ep7q_claim_owned(&transport,d,312,&out));
        if(i==1)put32(d+52,16); /* drain cleanup ignores the changed route */
        memcpy(prefix,d,300);
        fail_lock=true;
        if(ep7q_retire_owned(&transport,d,312))++notifications;
        assert(notifications==i); /* modeled original ACK must remain withheld */
        fail_lock=false;
        if(ep7q_retire_owned(&transport,d,312))++notifications;
        assert(notifications==i+1 && !memcmp(prefix,d,300) && !d[300]);
        assert(!ep7t_claim(&transport,ticket,&out));
    }
    put32(bytes+32,0x12345678);assert(!ep7q_ack_layout(&stack,w,w+36,&args));
    stack.expanded_group_ready=false;stack.bytes=(const unsigned char *)(uintptr_t)1;
    assert(!ep7q_ack_layout(&stack,w,w+36,&args));
}
typedef struct {
    unsigned queries,reads;uint16_t id,tcb_id;uint32_t cpu,root,cell,tcb,entry,base,bytes;
    bool query_error,late_query_error,changed_id,changed_tcb;
} task_fixture;
static int task_get(void *ctx,uint16_t *out){
    task_fixture *t=ctx;++t->queries;
    if(t->query_error || (t->late_query_error && t->queries==2))return -25;
    *out=(uint16_t)(t->id+(t->changed_id && t->queries==2?1u:0u));return 0;
}
static bool task_read32(void *ctx,uint32_t address,uint32_t *out){
    task_fixture *t=ctx;++t->reads;
    if(address==0x8050)*out=t->cpu;
    else if(address==0x8ff00004+4*t->cpu)*out=t->root;
    else if(address==t->root+96)*out=t->cell;
    else if(address==t->cell)*out=t->tcb+(t->changed_tcb && t->queries==2?4u:0u);
    else if(address==t->tcb+76)*out=t->entry;
    else if(address==t->tcb+84)*out=t->bytes;
    else if(address==t->tcb+88)*out=t->base;
    else return false;
    return true;
}
static bool task_read16(void *ctx,uint32_t address,uint16_t *out){
    task_fixture *t=ctx;++t->reads;if(address!=t->tcb+16)return false;*out=t->tcb_id;return true;
}
static void task_context_boundaries(void){
    task_fixture seed={.id=0x6c,.tcb_id=0x6c,.root=0x1000,.cell=0x2000,.tcb=0x3000,
        .entry=0x603f26a1,.base=0x8000,.bytes=8192},t=seed;
    ep7n_task_ops ops={&t,task_get,task_read32,task_read16};ep7n_task out;unsigned scenario;
    assert(ep7n_query_task(&ops,0x9000,&out));
    assert(out.tid==0x6c && out.domain==0 && out.tcb==0x3000 && out.entry==0x603f26a1 && out.stack_low==0x8000 && out.stack_bytes==8192);
    for(scenario=0;scenario<9;scenario++){
        t=seed;
        switch(scenario){
        case 0:t.query_error=true;break;
        case 1:t.cpu=1;break;
        case 2:t.tcb_id=0x6d;break;
        case 3:t.base=UINT32_MAX-3;break;
        case 4:t.late_query_error=true;break;
        case 5:t.changed_id=true;break;
        case 6:t.changed_tcb=true;break;
        case 7:t.root=UINT32_MAX-3;break;
        default:t.bytes=16;break;
        }
        assert(!ep7n_query_task(&ops,0x9000,&out) && !out.tcb && !out.stack_bytes);
        if(scenario==0)assert(!t.reads);
        if(scenario==1)assert(t.reads==1); /* reject domain before any root/TCB read */
    }
    t=seed;assert(!ep7n_query_task(&ops,0xa000,&out));
    t=seed;assert(!ep7n_query_task(&ops,0x7ffc,&out));
    t=seed;assert(ep7n_query_task(&ops,0x8000,&out));
    t=seed;t.id=t.tcb_id=0x106c;t.cpu=1;
    assert(ep7n_query_task(&ops,0x9000,&out) && out.domain==1); /* view only; no pipeline admission */
}
static void materializer_boundaries(void){
    unsigned char bytes[864]={0};uint32_t w=0x1000;ep7q_materializer_args a;
    ep7q_stack s={bytes,w,sizeof bytes,true};unsigned char *command=bytes+196;
    queue_fixture q={0};ep7q_ops ops=queue_ops(&q);ep7q_result r;ep7t_ticket t={100,3};size_t n;
    put32(bytes+44,0x603dfca2);put32(bytes+48,UINT32_MAX);
    put32(bytes+484,0x603dfb7d);put32(bytes+532,0x603df8c0);put32(bytes+56,w+552);
    assert(ep7q_materializer_layout(&s,w,0x4b,&a));
    assert(a.command==w+196 && a.descriptor==w+552 && a.timeout==-1 && a.origin==EP7Q_NORMAL);
    /* Resolve actual fixture addresses and run the owned receiver from this
       bounded frame map. Materializer prefix writes and native entry stay mocked. */
    put32(command+8,19);put32(command+12,100);
    assert(ep7w_encode(16,command,t,q.bytes,sizeof q.bytes,&n));
    q.length=(unsigned)n;q.raw=(int)n;q.qualified=true;
    r=ep7q_command_receive(&ops,0x4b,a.timeout,bytes+(a.command-w),16,bytes+(a.descriptor-w),312);
    assert(r.status==0 && r.ticket.serial==3 && bytes[852]=='E');
    s.extent--;assert(!ep7q_materializer_layout(&s,w,0x4b,&a) && !a.descriptor);s.extent++;
    put32(bytes+56,w+556);assert(!ep7q_materializer_layout(&s,w,0x4b,&a));put32(bytes+56,w+552);
    put32(bytes+532,0);assert(!ep7q_materializer_layout(&s,w,0x4b,&a));
    put32(bytes+484,0x603e0594);put32(bytes+56,w+496);s.extent=808;
    assert(ep7q_materializer_layout(&s,w,0x4b,&a) && a.origin==EP7Q_DRAIN_FIRST && a.descriptor==w+496);
    put32(bytes+484,0x603e05d2);
    assert(ep7q_materializer_layout(&s,w,0x4b,&a) && a.origin==EP7Q_DRAIN_NEXT);
    put32(bytes+484,0x603dfb7d);s.extent=488;
    assert(!ep7q_materializer_layout(&s,w,0x4b,&a)); /* no parent word mapped */
    put32(bytes+484,0x12345678);
    assert(!ep7q_materializer_layout(&s,w,0x4b,&a)); /* unknown call chain */
    put32(bytes+44,0);assert(!ep7q_materializer_layout(&s,w,0x4b,&a));
    /* Inactive publication must reject before accessing the supplied mapping. */
    s.expanded_group_ready=false;s.bytes=(const unsigned char *)(uintptr_t)1;
    assert(!ep7q_materializer_layout(&s,w,0x4b,&a));
    s.bytes=bytes;s.expanded_group_ready=true;
    assert(!ep7q_materializer_layout(&s,w,0x4c,&a));
    assert(!ep7q_materializer_layout(&s,w+1,0x4b,&a));
    s.low=UINT32_MAX-3;
    assert(!ep7q_materializer_layout(&s,UINT32_MAX-3,0x4b,&a)); /* address wrap */
}
static void owned_io_boundaries(void){
    queue_fixture q={0};ep7q_ops ops=queue_ops(&q);ep7q_result r;unsigned calls;
    struct {unsigned char prefix[16];uint32_t guard;} command;
    unsigned char descriptor[EP7W_MAX];ep7t_ticket ticket={100,1},read;
    memset(command.prefix,0xcc,sizeof command.prefix);command.guard=0x12345678;
    memset(descriptor,0xa5,sizeof descriptor);
    q.qualified=true;q.length=148;q.raw=148;memset(q.bytes,0x5a,sizeof q.bytes);
    r=ep7q_command_receive(&ops,0x4b,0,command.prefix,16,descriptor,sizeof descriptor);
    assert(r.called && r.status==-1 && !r.ticket.serial && command.guard==0x12345678);
    assert(command.prefix[0]==0xcc && descriptor[300]==0);
    calls=q.receives;
    r=ep7q_command_receive(&ops,0x4b,0,command.prefix,16,descriptor,300);
    assert(!r.called && q.receives==calls); /* extent cannot be upgraded by size/tag */
    q.length=0;q.raw=-50;
    assert(ep7w_write_trailer(descriptor+300,ticket));
    r=ep7q_descriptor_receive(&ops,0x4c,0,descriptor,sizeof descriptor);
    assert(r.called && r.status==-2 && descriptor[300]==0);
    q.raw=-42;r=ep7q_descriptor_receive(&ops,0x4f,0,descriptor,sizeof descriptor);
    assert(r.called && r.status==-1);
    q.raw=255;r=ep7q_command_receive(&ops,0x4b,0,command.prefix,16,descriptor,sizeof descriptor);
    assert(r.called && r.status==-1 && command.prefix[0]==0xcc); /* not bytes copied */
    q.qualified=false;calls=q.receives;assert(ep7w_write_trailer(descriptor+300,ticket));
    r=ep7q_descriptor_receive(&ops,0xab,0,descriptor,sizeof descriptor);
    assert(!r.called && q.receives==calls && descriptor[300]==0);
    q.qualified=true;q.raw=300;q.length=300;memset(q.bytes,0,sizeof q.bytes);
    put32(q.bytes+48,100);put32(q.bytes+52,19);put16(q.bytes+194,0x2001);
    assert(ep7w_write_trailer(descriptor+300,ticket));
    r=ep7q_descriptor_receive(&ops,0x4d,0,descriptor,sizeof descriptor);
    assert(r.called && r.status==0 && r.wire_status==EP7W_LEGACY && !r.ticket.serial);
    assert(ep7w_ticket(300,descriptor,312,&read)==EP7W_LEGACY);
    assert(ep7w_write_trailer(descriptor+300,ticket));q.raw=-50;
    r=ep7q_descriptor_send(&ops,0x4c,-1,descriptor,sizeof descriptor);
    assert(r.called && r.status==-2 && r.ticket.serial==ticket.serial && q.length==312);
    assert(descriptor[300]==0);q.raw=0;
    r=ep7q_descriptor_send(&ops,0x4c,-1,descriptor,sizeof descriptor);
    assert(r.called && r.status==0 && !r.ticket.serial && q.length==300);
    assert(ep7w_write_trailer(descriptor+300,ticket));calls=q.sends;
    r=ep7q_descriptor_send(&ops,0x999,-1,descriptor,sizeof descriptor);
    assert(!r.called && q.sends==calls && r.ticket.serial==ticket.serial && descriptor[300]==0);
}
static void descriptor_receive_boundaries(void){
    static const uint32_t cases[][5]={
        {0x603ef8ba,0,0x4c,56,EP7Q_DUAL_RECEIVER},
        {0x603ef902,0,0x4c,56,EP7Q_DUAL_RECEIVER},
        {0x603ef8d7,0,0x4d,56,EP7Q_DUAL_RECEIVER},
        {0x603ef91f,0,0x4d,56,EP7Q_DUAL_RECEIVER},
        {0x603dfa0b,0x603ef962,0xab,64,EP7Q_KIND19_RELAY},
        {0x603dfa0b,0x603f26bb,0x4f,64,EP7Q_KIND19_WORKER}
    };
    unsigned char bytes[376],prefix[300]={0};uint32_t w=0x2000;unsigned i;
    ep7q_stack s={bytes,w,sizeof bytes,true};ep7q_receive_input in;
    ep7q_receive_args args;queue_fixture q={0};ep7q_ops ops=queue_ops(&q);ep7q_result r;size_t n;
    put32(prefix+48,100);put32(prefix+52,19);put16(prefix+194,0x2001);q.qualified=true;
    for(i=0;i<sizeof cases/sizeof cases[0];i++){
        memset(bytes,0xa5,sizeof bytes);put32(bytes+44,cases[i][0]);put32(bytes+60,cases[i][1]);
        put32(bytes+48,0);s.extent=cases[i][3]+312;
        in=(ep7q_receive_input){cases[i][2],300,w+cases[i][3],0};
        assert(ep7q_descriptor_receive_layout(&s,w,&in,&args));
        assert(args.origin==cases[i][4] && args.descriptor==in.descriptor && args.timeout==0);
        assert(ep7w_encode(300,prefix,in.handle==0x4d?(ep7t_ticket){0}:(ep7t_ticket){100,17},q.bytes,sizeof q.bytes,&n));
        q.length=(unsigned)n;q.raw=(int)n;
        r=ep7q_descriptor_receive(&ops,in.handle,args.timeout,bytes+(args.descriptor-w),312);
        assert(r.status==0 && r.ticket.serial==(in.handle==0x4d?0u:17u));
        assert(bytes[cases[i][3]+300]==(in.handle==0x4d?0:'E'));
        --s.extent;assert(!ep7q_descriptor_receive_layout(&s,w,&in,&args) && !args.descriptor);++s.extent;
        ++in.descriptor;assert(!ep7q_descriptor_receive_layout(&s,w,&in,&args));--in.descriptor;
        in.nominal_bytes=312;assert(!ep7q_descriptor_receive_layout(&s,w,&in,&args));in.nominal_bytes=300;
        in.handle=0x50;assert(!ep7q_descriptor_receive_layout(&s,w,&in,&args));
    }
    in=(ep7q_receive_input){0x4f,300,w+64,0};put32(bytes+60,0x12345678);
    assert(!ep7q_descriptor_receive_layout(&s,w,&in,&args));
    s.expanded_group_ready=false;s.bytes=(const unsigned char *)(uintptr_t)1;
    assert(!ep7q_descriptor_receive_layout(&s,w,&in,&args));
    assert(ep7q_receive_rejection(0x4c)==-1 && ep7q_receive_rejection(0xab)==-1 && ep7q_receive_rejection(0x4f)==-1);
    assert(ep7q_receive_rejection(0x4d)==256 && ep7q_receive_rejection(0x50)==256);
}
typedef struct {ep7t *transport;ep7t_ticket pending;unsigned calls;} retirement_fixture;
static void take_retirement(void *ctx,ep7t_ticket ticket){
    retirement_fixture *owner=ctx;++owner->calls;assert(!owner->pending.serial);
    if(!ep7t_retire_owned(owner->transport,ticket))owner->pending=ticket;
}
static void descriptor_send_boundaries(void){
    static const uint32_t cases[][4]={
        {0x603dfc44,124,0x4c,EP7Q_NORMAL_SENDER},
        {0x603ef93e,68,0xab,EP7Q_DUAL_SENDER},
        {0x603ef993,60,0x4f,EP7Q_KIND19_SENDER}
    };
    unsigned char bytes[436]={0};uint32_t w=0x3000;unsigned i,calls;unsigned char *d;
    ep7q_stack s={bytes,w,sizeof bytes,true};ep7q_send_input in;ep7q_send_args args;
    queue_fixture q={0};ep7t transport={0};ep7t_ticket ticket,read;ep7p_snapshot snapshot={0,{0}},out;
    retirement_fixture owner={&transport,{0},0};ep7q_forward_ops ops={queue_ops(&q),&owner,take_retirement};
    q.qualified=true;assert(ep7t_init(&transport,(ep7p_ops){NULL,lock,unlock,current}));
    for(i=0;i<sizeof cases/sizeof cases[0];i++){
        memset(bytes,0,sizeof bytes);put32(bytes+36,0x603dfaa8);put32(bytes+40,UINT32_MAX);
        put32(bytes+56,cases[i][0]);put32(bytes+104,0x603df8c0);s.extent=cases[i][1]+312;
        in=(ep7q_send_input){cases[i][2],w+cases[i][1],0};
        assert(ep7q_descriptor_send_layout(&s,w,&in,&args) && args.origin==cases[i][3] && args.timeout==-1);
        --s.extent;assert(!ep7q_descriptor_send_layout(&s,w,&in,&args) && !args.descriptor);++s.extent;
        ++in.descriptor;assert(!ep7q_descriptor_send_layout(&s,w,&in,&args));--in.descriptor;
        assert(ep7q_descriptor_send_layout(&s,w,&in,&args));d=bytes+(args.descriptor-w);
        memset(d,0,300);put32(d+48,100);put32(d+52,19);put16(d+194,0x2001);
        assert(ep7t_prepare(&transport,100,&snapshot,&ticket) && ep7t_publish(&transport,ticket));
        assert(ep7w_write_trailer(d+300,ticket));q.raw=0;
        assert(ep7q_forward_send(&ops,in.handle,args.timeout,d,312)==0 && !owner.calls && q.length==312 && d[300]==0);
        assert(ep7w_ticket(300,q.bytes,q.length,&read)==EP7W_TAGGED && read.serial==ticket.serial);
        assert(ep7t_claim(&transport,read,&out) && ep7t_retire(&transport,read));
    }
    d=bytes+60; /* already tested live owned descriptor; failures below use it */
    assert(ep7t_prepare(&transport,100,&snapshot,&ticket) && ep7t_publish(&transport,ticket));
    assert(ep7w_write_trailer(d+300,ticket));q.raw=-50;fail_lock=true;
    assert(ep7q_forward_send(&ops,0x4f,-1,d,312)==-2 && owner.calls==1 && owner.pending.serial==ticket.serial);
    fail_lock=false;assert(ep7t_retire(&transport,owner.pending));owner.pending=(ep7t_ticket){0};
    q.raw=0;assert(ep7q_forward_send(&ops,0x4f,-1,d,312)==0 && q.length==300 && owner.calls==1);
    /* Changed route loses apply admission, retains only cleanup identity. */
    assert(ep7t_prepare(&transport,100,&snapshot,&ticket) && ep7t_publish(&transport,ticket));
    assert(ep7w_write_trailer(d+300,ticket));put32(d+52,16);
    assert(ep7w_ticket(300,d,312,&read)==EP7W_LEGACY && !read.serial);
    assert(ep7q_forward_send(&ops,0x4f,-1,d,312)==0 && q.length==300 && owner.calls==2);
    assert(!ep7t_claim(&transport,ticket,&out));put32(d+52,19);
    assert(ep7t_prepare(&transport,100,&snapshot,&ticket) && ep7t_publish(&transport,ticket));
    assert(ep7w_write_trailer(d+300,ticket));calls=q.sends;
    assert(ep7q_forward_send(&ops,0xac,-1,d,312)==256 && q.sends==calls && owner.calls==3 && !d[300]);
    assert(!ep7t_claim(&transport,ticket,&out));
    assert(ep7t_prepare(&transport,100,&snapshot,&ticket) && ep7t_publish(&transport,ticket));
    assert(ep7w_write_trailer(d+300,ticket));
    assert(ep7q_forward_send(&ops,0x4d,-1,d,312)==0 && q.length==300 && owner.calls==4);
    assert(!ep7t_claim(&transport,ticket,&out));
    put32(bytes+56,0x12345678);assert(!ep7q_descriptor_send_layout(&s,w,&in,&args));
    s.expanded_group_ready=false;s.bytes=(const unsigned char *)(uintptr_t)1;
    assert(!ep7q_descriptor_send_layout(&s,w,&in,&args));
}
static void producer_boundaries(void){
    ep7t transport={0};queue_fixture q={0};retirement_fixture owner={&transport,{0},0};
    ep7q_producer_ops ops={&transport,{queue_ops(&q),&owner,take_retirement}};
    ep7p_snapshot snapshot={3,{0}};ep7q_capture_scope scope;ep7t_ticket ticket;
    unsigned char command[16]={0},bytes[180]={0};uint32_t w=0x4000,label=0x70001000;unsigned calls;
    ep7q_stack stack={bytes,w,sizeof bytes,true};ep7q_producer_input in={0x4b,16,w+52,UINT32_MAX};ep7q_producer_args args;
    assert(ep7t_init(&transport,(ep7p_ops){NULL,lock,unlock,current}));
    put32(command+8,19);put32(command+12,100);q.qualified=true;snapshot.hl[0]=3;
    ep7q_capture_scope_init(&scope,7,&snapshot);snapshot.hl[0]=0;q.claim_transport=&transport;
    assert(ep7q_producer_send(&ops,&scope,0x4b,-1,command,16)==0 && scope.state==EP7Q_SCOPE_CONSUMED);
    assert(q.claimed && q.claimed_snapshot.profile==3 && q.claimed_snapshot.hl[0]==3);
    assert(ep7w_ticket(16,q.bytes,q.length,&ticket)==EP7W_TAGGED && ep7t_retire(&transport,ticket));
    q.claim_transport=NULL;calls=q.sends;
    assert(ep7q_producer_send(&ops,&scope,0x4b,-1,command,16)==256 && q.sends==calls);
    ep7q_capture_scope_init(&scope,7,&snapshot);fail_lock=true;
    assert(ep7q_producer_send(&ops,&scope,0x4b,-1,command,16)==256 && scope.state==EP7Q_SCOPE_CONSUMED);
    fail_lock=false;
    assert(ep7q_producer_send(&ops,&scope,0x4b,-1,command,16)==256 && q.sends==calls); /* no late backfill */
    ep7q_capture_scope_init(&scope,7,&snapshot);q.raw=-2;q.fail_lock_after_send=true;
    named_queue_fixture=&q;ops.forward.queue.send=ep7q_send_local_preserving;
    assert(ep7q_producer_send(&ops,&scope,0x4b,-1,command,16)==-2 && owner.pending.serial && owner.calls==1);
    assert(named_notifications==1);named_queue_fixture=NULL;ops.forward.queue.send=send_queue;
    fail_lock=false;q.fail_lock_after_send=false;assert(ep7t_retire(&transport,owner.pending));owner.pending=(ep7t_ticket){0};
    ep7q_capture_scope_init(&scope,7,&snapshot);q.qualified=false;calls=q.sends;
    assert(ep7q_producer_send(&ops,&scope,0x4b,-1,command,16)==256 && q.sends==calls && owner.calls==1);
    put32(bytes+48,0x602ac870);put32(bytes+80,label);put32(bytes+176,0x602ac3e3);
    put32(bytes+44,7);put32(bytes+96,7);put32(bytes+104,7);
    assert(ep7q_producer_layout(&stack,w,&in,label,&args) && args.scope==w+104 && args.command==w+52 && args.timeout==-1);
    --stack.extent;assert(!ep7q_producer_layout(&stack,w,&in,label,&args) && !args.scope);++stack.extent;
    put32(bytes+96,8);assert(!ep7q_producer_layout(&stack,w,&in,label,&args));put32(bytes+96,7);
    put32(bytes+80,0x602ac3e3);assert(!ep7q_producer_layout(&stack,w,&in,label,&args));put32(bytes+80,label);
    ++in.command;assert(!ep7q_producer_layout(&stack,w,&in,label,&args));--in.command;
    assert(!ep7q_producer_layout(&stack,w,&in,0,&args));
    stack.expanded_group_ready=false;stack.bytes=(const unsigned char *)(uintptr_t)1;
    assert(!ep7q_producer_layout(&stack,w,&in,label,&args));
}
static ep7t_ticket wire_relay_fixture(ep7t *transport,ep7q_capture_scope *scope,unsigned char *delivered){
    unsigned char cmd[EP7W_COMMAND]={0},native[EP7W_MAX];
    queue_fixture q={0};ep7q_ops ops=queue_ops(&q);ep7q_result result;
    retirement_fixture owner={transport,{0},0};ep7q_forward_ops forward={ops,&owner,take_retirement};
    ep7q_producer_ops producer={transport,forward};ep7t_ticket ticket;
    unsigned i;static const unsigned queues[]={0x4c,0xab,0x4f};
    q.qualified=true;
    put32(cmd+8,19);put32(cmd+12,100);q.raw=0;
    assert(ep7q_producer_send(&producer,scope,0x4b,-1,cmd,sizeof cmd)==0 && q.length==28 && !owner.calls);
    assert(ep7w_ticket(16,q.bytes,q.length,&ticket)==EP7W_TAGGED);q.raw=(int)q.length;
    result=ep7q_command_receive(&ops,0x4b,-1,cmd,sizeof cmd,native,sizeof native);
    assert(result.called && result.status==0 && result.ticket.serial==ticket.serial);
    /* Materializer is still a native fixture; serializer/relay codec is real.
       Arbitrary prefix bytes model fields owned by stock preprocessing. */
    memset(native,0x5a,EP7W_DESCRIPTOR); /* preserve independently owned trailer */
    put32(native+48,ticket.metadata);put32(native+52,19);put16(native+194,0x2001);
    for(i=0;i<3;i++){
        q.raw=0;assert(ep7q_forward_send(&forward,queues[i],-1,native,sizeof native)==0);
        assert(!owner.calls && q.length==312 && native[300]==0);
        assert(!memcmp(native,q.bytes,300));memset(native,0,sizeof native);
        q.raw=(int)q.length;result=ep7q_descriptor_receive(&ops,queues[i],-1,native,sizeof native);
        assert(result.called && result.status==0 && result.wire_status==EP7W_TAGGED);
        assert(result.ticket.serial==ticket.serial && result.ticket.metadata==ticket.metadata);
        assert(!memcmp(native,q.bytes,300));native[192]=(unsigned char)i;
    }
    memcpy(delivered,native,sizeof native);return result.ticket;
}
static void capture_vertical_slice(void){
    ep7p_snapshot frozen,after;capture_host h={0};unsigned i,j;
    ep7c sidecar={0};ep7c_prefix prefix={2,3,1,11,3};uint64_t token,resolved;
    ep7t transport={0};ep7t_ticket ticket,previous={0};
    ep7p_snapshot delivered;
    ep7l_ops ops={&h,construct,convert,process,cleanup};
    assert(ep7p_ui_ops.sync(&ui,session,56,4)==EP7_UI_CHANGED);
    /* Prior session was in ALL; leave it before selecting bin0. */
    assert(send(0x9014,0)==1);assert(frame().selected_sector==0);
    assert(send(0x9032,3)==1);text_is(frame(),"H 01 +3");
    assert(ep7p_ui_ops.sync(&ui,session,56,5)==EP7_UI_CHANGED);
    assert(send(0x9032,-2)==1);text_is(frame(),"L 01 -2");
    /* Host-owned node labels and exclusive single-thread lifetime. No native
       prefix is read; this tests real sidecar -> owned value -> real job code,
       not an implementation of native metadata/descriptor transport. */
    assert(ep7c_init(&sidecar,33));
    assert(ep7c_register_fresh(&sidecar,33,1,2,&token));
    assert(ep7c_resolve_live(&sidecar,33,1,&resolved) && resolved==token);
    assert(ep7c_authorize(&sidecar,33,1,resolved));
    assert(ep7c_seal(&sidecar,33,1,resolved,&prefix,true,&core));
    assert(ep7c_copyout(&sidecar,33,1,resolved,&prefix,&frozen));
    assert(frozen.hl[0]==3 && frozen.hl[12]==-2);
    assert(ep7c_forget(&sidecar,33,1,token));
    ep7c_transition(&sidecar,33,33);
    assert(!ep7c_resolve_live(&sidecar,33,1,&resolved));
    assert(send(0x9032,2)==1);assert(ep7p_ui_ops.sync(&ui,session,56,4)==EP7_UI_CHANGED);
    assert(send(0x9032,-3)==1);text_is(frame(),"H 01 +0");
    assert(ep7p_capture(&core,11,3,&after));assert(after.hl[0]==0 && after.hl[12]==0);
    assert(ep7t_init(&transport,(ep7p_ops){NULL,lock,unlock,current}));
    for(i=0;i<16;i++){
        ep7l_result result;ep7q_capture_scope scope;unsigned char descriptor[EP7W_MAX];h.slot=i;
        /* Each fixture job gets a new ticket. Native relay is still modeled:
           every copied descriptor must explicitly carry THIS full ticket. */
        ep7q_capture_scope_init(&scope,7,&frozen);
        assert(!ep7t_claim(&transport,previous,&delivered));
        ticket=wire_relay_fixture(&transport,&scope,descriptor);
        assert(ep7q_claim_owned(&transport,descriptor,sizeof descriptor,&delivered));
        assert(!ep7q_claim_owned(&transport,descriptor,sizeof descriptor,&after));
        assert(ep7q_retire_owned(&transport,descriptor,sizeof descriptor));previous=ticket;
        result=ep7l_run(&core,&ops,&h,&delivered);
        assert(result.registered && result.applied==1 && result.readers==1 && result.cleaned && !result.quarantined);
        assert(result.native_status==-123 && h.cleanups==i+1 && !h.owner);
        /* Captured H+3 -> comparative -3000; L-2 -> -50, despite later UI0. */
        assert(h.output[706]==0x48 && h.output[707]==0xf4);
        assert(h.output[710]==0xce && h.output[711]==0xff);
        for(j=0;j<sizeof h.output;j++)if(j!=706 && j!=707 && j!=710 && j!=711)assert(h.output[j]==0x5a);
    }
    /* Premature publication consumes the node's sampling opportunity. Native
       processing still executes neutral; a later UI snapshot must not backfill. */
    assert(ep7c_register_fresh(&sidecar,33,1,2,&resolved) && resolved!=token);
    assert(!ep7c_authorize(&sidecar,33,1,token));
    assert(!ep7c_copyout(&sidecar,33,1,resolved,&prefix,&after));
    assert(!ep7c_seal(&sidecar,33,1,resolved,&prefix,true,&core));
    h.neutral=true;
    {
        ep7l_result result=ep7l_run(&core,&ops,&h,NULL);
        assert(result.invoked && !result.registered && !result.applied && result.readers==1);
        assert(result.cleaned && !result.quarantined && result.native_status==-123);
        assert(h.cleanups==17 && !h.owner);
        for(j=0;j<sizeof h.output;j++)assert(h.output[j]==0x5a);
    }
    assert(ep7c_forget(&sidecar,33,1,resolved));
}
int main(void){
    ep7p_snapshot snap;struct ep7_ui_frame f;unsigned i,n;
    assert(ep7p_init(&core,(ep7p_ops){NULL,lock,unlock,current}));ep7p_ui_init(&ui,&core);
    assert(ep7p_ui_ops.open(&ui,session,64,4)==EP7_UI_CHANGED);
    assert(ep7p_capture(&core,11,4,&snap));
    assert(send(0x9032,3)==0);unchanged(snap); /* no renderer */
    renderer_ready=true;modal_blocked=true;assert(send(0x9032,3)==0);unchanged(snap);modal_blocked=false;
    known_stock=true;assert(send(0x9032,3)==256);unchanged(snap);known_stock=false;
    assert(send(0x9032,3)==1);f=frame();assert(f.logical_steps[0]==3);text_is(f,"H 01 +3"); /* full3, packet1 ignored */
    assert(send(0x9031,2)==1);assert(frame().selected_sector==2);
    assert(send(0x9032,-2)==1);assert(frame().logical_steps[2]==-2);
    assert(send(0x9031,-3)==1);assert(frame().selected_sector==11);
    assert(send(0x9032,0)==0);assert(send(0x9031,0)==0);
    assert(ep7p_capture(&core,11,4,&snap));
    {const int32_t invalid[]={65,-65,INT32_MIN,INT32_MAX};
     for(i=0;i<sizeof invalid/sizeof invalid[0];++i){assert(send(0x9032,invalid[i])==0);assert(send(0x9031,invalid[i])==0);unchanged(snap);}}
    assert(send(0x9014,INT32_MIN)==1);assert(frame().selected_sector==255);text_is(frame(),"H ALL MIX");
    assert(send(0x9032,64)==1);f=frame();assert(f.logical_steps[0]==7 && f.logical_steps[2]==2 && f.logical_steps[11]==4);
    assert(send(0x9032,64)==0); /* uniform ALL at positive bound is unchanged */
    assert(send(0x9031,1)==1);assert(frame().selected_sector==0);
    assert(ep7p_ui_ops.sync(&ui,session,64,5)==EP7_UI_CHANGED);
    assert(send(0x9032,-4)==1);assert(ep7p_capture(&core,11,4,&snap));assert(snap.hl[12]==-4 && snap.hl[0]==7);
    {const uint32_t delegated[]={0x9004,0x9006,0x900c,0x9016,0x903e,0xffffffff};n=admissions;
     for(i=0;i<sizeof delegated/sizeof delegated[0];++i)assert(send(delegated[i],42)==256);
     assert(admissions==n);unchanged(snap);}
    fail_lock=true;assert(send(0x9032,1)==0);assert(send(0x9014,0)==0);fail_lock=false;unchanged(snap);
    assert(ep7p_ui_ops.sync(&ui,session,57,5)==EP7_UI_REJECTED);assert(send(0x9032,0)==0);assert(send(0x9014,0)==0);unchanged(snap);
    assert(ep7p_ui_ops.sync(&ui,session,64,5)==EP7_UI_CHANGED);
    ep7p_ui_ops.close(&ui,session);assert(send(0x9032,1)==0);assert(send(0x9014,0)==0);unchanged(snap);
    {struct ep7_ui_session newer={2,0};assert(ep7p_ui_ops.open(&ui,newer,64,4)==EP7_UI_CHANGED);
     assert(send(0x9032,1)==0);unchanged(snap);session=newer;assert(send(0x9032,-1)==1);assert(frame().logical_steps[0]==6);}
    /* Real newly selected profile/axis -> uniform ALL label; setter remains mock. */
    assert(ep7p_ui_ops.sync(&ui,session,54,5)==EP7_UI_CHANGED);
    assert(send(0x9014,0)==1);assert(send(0x9032,-7)==1);text_is(frame(),"L ALL -7");
    setter_status=0;f=frame();assert(ep7_text_present(&widget_token,&f)==0);setter_status=1;
    n=text_calls;f.category=1;assert(ep7_text_present(&widget_token,&f)==0);assert(text_calls==n);
    transport_boundaries();wire_boundaries();consumer_boundaries();worker_boundaries();ack_boundaries();task_context_boundaries();materializer_boundaries();owned_io_boundaries();descriptor_receive_boundaries();descriptor_send_boundaries();producer_boundaries();capture_vertical_slice();
    assert(!held && current_queries==0);
    puts("router -> sidecar -> owned command receive -> three owned forward/receive relays -> ticket -> 16 job slots: PASS; native queue backend/ABI/materializer mocked");return 0;
}
