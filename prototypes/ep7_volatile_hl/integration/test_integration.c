/* Self-authored host test: real router/raw/UI/core; mocked native admission. */
#include "bridge.h"
#include "text.h"
#include "ep7p_lifecycle.h"
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
typedef struct {unsigned char *owner,*job;unsigned slot,cleanups;unsigned char output[EP7P_OUTPUT];} capture_host;
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
    assert(reader(reader_ctx,(uintptr_t)h->job+11364,h->output,sizeof h->output));
    return -123; /* preserve mock native status independently of H/L success */
}
static void cleanup(void *ctx,void *descriptor){
    capture_host *h=ctx;unsigned i;assert(descriptor==h);
    for(i=0;i<EP7P_CAP;i++)assert(!core.jobs[i].token);
    free(h->owner);h->owner=NULL;h->job=NULL;++h->cleanups;
}
static void capture_vertical_slice(void){
    ep7p_snapshot frozen,after;capture_host h={0};unsigned i,j;
    ep7l_ops ops={&h,construct,convert,process,cleanup};
    assert(ep7p_ui_ops.sync(&ui,session,56,4)==EP7_UI_CHANGED);
    /* Prior session was in ALL; leave it before selecting bin0. */
    assert(send(0x9014,0)==1);assert(frame().selected_sector==0);
    assert(send(0x9032,3)==1);text_is(frame(),"H 01 +3");
    assert(ep7p_ui_ops.sync(&ui,session,56,5)==EP7_UI_CHANGED);
    assert(send(0x9032,-2)==1);text_is(frame(),"L 01 -2");
    assert(ep7p_capture(&core,11,3,&frozen));assert(frozen.hl[0]==3 && frozen.hl[12]==-2);
    assert(send(0x9032,2)==1);assert(ep7p_ui_ops.sync(&ui,session,56,4)==EP7_UI_CHANGED);
    assert(send(0x9032,-3)==1);text_is(frame(),"H 01 +0");
    assert(ep7p_capture(&core,11,3,&after));assert(after.hl[0]==0 && after.hl[12]==0);
    for(i=0;i<16;i++){
        ep7l_result result;h.slot=i;result=ep7l_run(&core,&ops,&h,&frozen);
        assert(result.registered && result.applied==1 && result.readers==1 && result.cleaned && !result.quarantined);
        assert(result.native_status==-123 && h.cleanups==i+1 && !h.owner);
        /* Captured H+3 -> comparative -3000; L-2 -> -50, despite later UI0. */
        assert(h.output[706]==0x48 && h.output[707]==0xf4);
        assert(h.output[710]==0xce && h.output[711]==0xff);
        for(j=0;j<sizeof h.output;j++)if(j!=706 && j!=707 && j!=710 && j!=711)assert(h.output[j]==0x5a);
    }
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
    capture_vertical_slice();
    assert(!held && current_queries==0);
    puts("real router -> raw adapter -> UI -> core -> text/capture/direct lifecycle: PASS; native admission mocked, no renderer/hardware");return 0;
}
