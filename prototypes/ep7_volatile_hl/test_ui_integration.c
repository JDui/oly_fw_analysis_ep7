#include "ep7p_ui.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

typedef struct { bool held; ep7p_task task; unsigned calls,fail_at; } host;
static bool lock_host(void *p) { host *h=p; if(h->held || ++h->calls==h->fail_at) return false; h->held=true; return true; }
static void unlock_host(void *p) { host *h=p; assert(h->held); h->held=false; }
static int current_host(void *p,ep7p_task *out) { *out=((host *)p)->task; return 0; }
static ep7p_observation observe(void *job) {
    uintptr_t b=(uintptr_t)job;
    ep7p_observation o={0};
    o.job=b; o.request=b+11364; o.operation=b+14576;
    o.request_operation=o.operation; o.operation_job=b; o.operation_request=o.request;
    o.callback=0x60355fd4; o.stage_callback=0x6036884d;
    o.stage=2; o.raw_mode=11; o.raw_selector=4;
    return o;
}
static void put16(unsigned char *p,int v) { uint16_t u=(uint16_t)v; p[0]=(unsigned char)u; p[1]=(unsigned char)(u>>8); }
int main(void) {
    ep7p core; ep7p_ui ui; host h={.task={7,1}};
    ep7p_ops ops={&h,lock_host,unlock_host,current_host};
    struct ep7_ui_session session={1,0},stale={1,0},fresh={2,0};
    struct ep7_ui_frame frame;
    ep7p_snapshot snapshot; unsigned char *memory=malloc(EP7P_EXTENT);
    unsigned char output[EP7P_OUTPUT+8],expected[sizeof output];
    ep7p_observation o; uint64_t job,scope; unsigned i;
    assert(memory && ep7p_init(&core,ops)); ep7p_ui_init(&ui,&core);
    assert(ep7p_ui_ops.open(&ui,session,64,0)==EP7_UI_REJECTED); /* stock S is not hijacked */
    assert(ep7p_ui_ops.open(&ui,session,64,4)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_VALUE_INCREASE,3)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.sync(&ui,session,64,5)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_TOGGLE_ALL,1)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_VALUE_INCREASE,2)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED);
    assert(frame.public_mode==64 && frame.category==5 && frame.selected_sector==255);
    for(i=0;i<12;i++) assert(frame.logical_steps[i]==2);
    assert(ep7p_capture(&core,11,4,&snapshot));
    assert(ep7p_register_job(&core,memory,EP7P_EXTENT,&snapshot,&job));
    assert(ep7p_register_task(&core,h.task)); o=observe(memory);
    assert(ep7p_enter(&core,job,&o,&scope));
    /* Later UI edit and close must not affect the already attached image. */
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_RESET_CURRENT_AXIS,1)==EP7_UI_CHANGED);
    ep7p_ui_ops.close(&ui,session);
    assert(ep7p_ui_ops.event(&ui,stale,EP7_UI_VALUE_INCREASE,1)==EP7_UI_REJECTED);
    memset(output,0x5a,sizeof output); memcpy(expected,output,sizeof output);
    put16(expected+706,-3000); /* captured H=3 in bin0; zero axes preserve stock */
    for(i=0;i<12;i++) put16(expected+710+24*i,50); /* captured L=2 */
    assert(ep7p_apply(&core,scope,job,&o,output,sizeof output));
    assert(memcmp(output,expected,sizeof output)==0); /* includes S and bytes976+ */
    assert(ep7p_unwind(&core,scope));
    assert(!ep7p_apply(&core,scope,job,&o,output,sizeof output));
    assert(ep7p_release_job(&core,job)); free(memory);
    assert(ep7p_release_task(&core,h.task));
    assert(ep7p_ui_ops.open(&ui,stale,64,4)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.open(&ui,fresh,64,4)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,fresh,(enum ep7_ui_event)99,1)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.event(&ui,fresh,EP7_UI_VALUE_INCREASE,0)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.event(&ui,fresh,EP7_UI_VALUE_INCREASE,65)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.event(&ui,fresh,EP7_UI_TOGGLE_ALL,2)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.sync(&ui,fresh,57,4)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.event(&ui,fresh,EP7_UI_VALUE_INCREASE,1)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.sync(&ui,fresh,64,4)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,fresh,EP7_UI_VALUE_INCREASE,64)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,fresh,EP7_UI_VALUE_INCREASE,1)==EP7_UI_UNCHANGED);
    assert(ep7p_ui_ops.event(&ui,fresh,EP7_UI_RESET_CURRENT_AXIS,1)==EP7_UI_CHANGED);
    ep7p_ui_ops.close(&ui,fresh);
    /* New boot lifetime: the whole private state is initialized neutral. */
    assert(ep7p_init(&core,ops)); assert(ep7p_capture(&core,11,4,&snapshot));
    for(i=0;i<24;i++) assert(snapshot.hl[i]==0);
    /* UI commit/result is one lock: no post-commit lock failure can report rejection. */
    ep7p_ui_init(&ui,&core);
    session=(struct ep7_ui_session){1,0};
    assert(ep7p_ui_ops.open(&ui,session,54,4)==EP7_UI_CHANGED);
    h.calls=0; h.fail_at=1;
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_VALUE_INCREASE,1)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.logical_steps[0]==0);
    h.calls=0; h.fail_at=3;
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_VALUE_INCREASE,1)==EP7_UI_CHANGED);
    assert(h.calls==1);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.logical_steps[0]==1);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_VALUE_INCREASE,1)==EP7_UI_REJECTED);
    h.fail_at=0;
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.logical_steps[0]==1);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_SECTOR_PREVIOUS,1)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.selected_sector==11);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_SECTOR_NEXT,1)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_SECTOR_NEXT,12)==EP7_UI_UNCHANGED);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_TOGGLE_ALL,1)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_SECTOR_NEXT,12)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.selected_sector==0);
    assert(ep7p_ui_ops.sync(&ui,session,54,0)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.event(&ui,session,EP7_UI_VALUE_INCREASE,1)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.sync(&ui,session,54,4)==EP7_UI_CHANGED);
    ep7p_ui_ops.close(&ui,session);
    assert(ep7p_init(&core,ops)); ep7p_ui_init(&ui,&core);
    for(i=0;i<4;i++) {
        const uint16_t modes[4]={54,55,56,64};
        session=(struct ep7_ui_session){1,i};
        assert(ep7p_ui_ops.open(&ui,session,modes[i],4)==EP7_UI_CHANGED);
        assert(ep7p_ui_ops.event(&ui,session,EP7_UI_VALUE_INCREASE,(uint16_t)(i+1))==EP7_UI_CHANGED);
        assert(ep7p_capture(&core,11,i+1,&snapshot) && snapshot.hl[0]==(int8_t)(i+1));
        ep7p_ui_ops.close(&ui,session);
    }
    session=(struct ep7_ui_session){UINT32_MAX,3};
    assert(ep7p_ui_ops.open(&ui,session,64,4)==EP7_UI_CHANGED);
    ep7p_ui_ops.close(&ui,session);
    assert(ep7p_ui_ops.open(&ui,session,64,4)==EP7_UI_REJECTED);
    session.generation=0;
    assert(ep7p_ui_ops.open(&ui,session,64,4)==EP7_UI_REJECTED);
    session.generation=2;
    assert(ep7p_ui_ops.open(&ui,session,64,4)==EP7_UI_REJECTED);
    puts("normalized UI -> captured profile -> fresh job -> scoped CPU lanes -> cleanup: PASS (host only)");
    return 0;
}
