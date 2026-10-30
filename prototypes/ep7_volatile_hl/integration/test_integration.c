/* Self-authored host test: real router/raw/UI/core; mocked native admission. */
#include "bridge.h"
#include "text.h"
#include "ep7p_lifecycle.h"
#include "controller_sidecar/sidecar.h"
#include "snapshot_transport/transport.h"
#include "snapshot_transport/wire.h"
#include "snapshot_transport/owned_io.h"
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
    assert(!ep7t_prepare(&t,1,&source,&sentinel) && sentinel.serial==99);
    fail_lock=true;
    assert(!ep7t_claim(&t,now,&out) && out.profile==1);
    assert(!ep7t_retire(&t,now));
    fail_lock=false;
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
    assert(bytes<=q->maximum);memcpy(q->bytes,in,bytes);q->length=bytes;return q->raw;
}
static ep7q_ops queue_ops(queue_fixture *q)
{ ep7q_ops ops={q,qualify_queue,receive_queue,send_queue};return ops; }
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
static ep7t_ticket wire_relay_fixture(ep7t_ticket ticket){
    unsigned char cmd[EP7W_COMMAND]={0},native[EP7W_MAX];
    queue_fixture q={0};ep7q_ops ops=queue_ops(&q);ep7q_result result;
    size_t n;unsigned i;static const unsigned queues[]={0x4c,0xab,0x4f};
    q.qualified=true;
    put32(cmd+8,19);put32(cmd+12,(uint32_t)ticket.metadata);
    assert(ep7w_encode(EP7W_COMMAND,cmd,ticket,q.bytes,sizeof q.bytes,&n));
    q.length=(unsigned)n;q.raw=(int)n;
    result=ep7q_command_receive(&ops,0x4b,-1,cmd,sizeof cmd,native,sizeof native);
    assert(result.called && result.status==0 && result.ticket.serial==ticket.serial);
    /* Materializer is still a native fixture; serializer/relay codec is real.
       Arbitrary prefix bytes model fields owned by stock preprocessing. */
    memset(native,0x5a,EP7W_DESCRIPTOR); /* preserve independently owned trailer */
    put32(native+48,ticket.metadata);put32(native+52,19);put16(native+194,0x2001);
    for(i=0;i<3;i++){
        q.raw=0;result=ep7q_descriptor_send(&ops,queues[i],-1,native,sizeof native);
        assert(result.called && result.status==0 && q.length==312 && native[300]==0);
        assert(!memcmp(native,q.bytes,300));memset(native,0,sizeof native);
        q.raw=(int)q.length;result=ep7q_descriptor_receive(&ops,queues[i],-1,native,sizeof native);
        assert(result.called && result.status==0 && result.wire_status==EP7W_TAGGED);
        assert(result.ticket.serial==ticket.serial && result.ticket.metadata==ticket.metadata);
        assert(!memcmp(native,q.bytes,300));native[192]=(unsigned char)i;
    }
    return result.ticket;
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
        ep7l_result result;h.slot=i;
        /* Each fixture job gets a new ticket. Native relay is still modeled:
           every copied descriptor must explicitly carry THIS full ticket. */
        assert(ep7t_prepare(&transport,100,&frozen,&ticket));
        assert(ep7t_publish(&transport,ticket));
        assert(!ep7t_claim(&transport,previous,&delivered));
        ticket=wire_relay_fixture(ticket);
        assert(ep7t_claim(&transport,ticket,&delivered));
        assert(!ep7t_claim(&transport,ticket,&after));
        assert(ep7t_retire(&transport,ticket));previous=ticket;
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
    transport_boundaries();wire_boundaries();owned_io_boundaries();capture_vertical_slice();
    assert(!held && current_queries==0);
    puts("router -> sidecar -> owned command receive -> three owned queue relays -> ticket -> 16 job slots: PASS; native queue backend/ABI/materializer mocked");return 0;
}
