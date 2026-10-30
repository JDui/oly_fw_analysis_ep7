#include "ep7p_ui_raw.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { unsigned acquisitions; bool fail; } host;
static bool lock(void *p){host *h=p; ++h->acquisitions;return !h->fail;}
static void unlock(void *p){(void)p;}
static int current(void *p,ep7p_task *t){(void)p;*t=(ep7p_task){1,1};return 0;}
static int send(ep7p_ui *ui,struct ep7_ui_session session,uint32_t event,int32_t delta){
    const struct ep7p_ui_raw_event input={event,delta};
    return ep7p_ui_raw_dispatch(ui,session,&input);
}
int main(void){
    ep7p core;ep7p_ui ui;host h={0,false};struct ep7_ui_session session={1,0};
    struct ep7_ui_frame frame;ep7p_snapshot captured;unsigned i;
    assert(ep7p_init(&core,(ep7p_ops){&h,lock,unlock,current}));ep7p_ui_init(&ui,&core);
    assert(ep7p_ui_ops.open(&ui,session,64,4)==EP7_UI_CHANGED);
    /* The FULL supplied count3—not a hypothetical compressed packet+1—is used. */
    assert(send(&ui,session,0x9032,3)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.logical_steps[0]==3);
    assert(send(&ui,session,0x9031,2)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.selected_sector==2);
    assert(send(&ui,session,0x9032,-2)==EP7_UI_CHANGED);
    assert(send(&ui,session,0x9031,-3)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.selected_sector==11 && frame.logical_steps[2]==-2);
    /* INFO has one action per admitted call; wheel delta is irrelevant. */
    assert(send(&ui,session,0x9014,INT32_MIN)==EP7_UI_CHANGED);
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.selected_sector==255);
    assert(send(&ui,session,0x9032,64)==EP7_UI_CHANGED);
    assert(ep7p_capture(&core,11,4,&captured));
    assert(captured.hl[0]==7 && captured.hl[2]==2); /* uniform ALL delta4 */
    assert(send(&ui,session,0x9031,1)==EP7_UI_CHANGED); /* exits ALL */
    assert(ep7p_ui_ops.frame(&ui,session,&frame)==EP7_UI_UNCHANGED && frame.selected_sector==0);
    assert(send(&ui,session,0x9032,0)==EP7_UI_UNCHANGED);
    { const int32_t invalid[]={-32768,-65,65,32768,INT32_MIN,INT32_MAX};
      for(i=0;i<sizeof invalid/sizeof invalid[0];i++)assert(send(&ui,session,0x9032,invalid[i])==EP7_UI_REJECTED); }
    /* UP/DOWN/OK/hold/reset/unknown are delegated without touching UI/core. */
    { const uint32_t delegated[]={0x9004,0x9006,0x900c,0x903e,0x9016,0xffffffff};unsigned before=h.acquisitions;
      for(i=0;i<sizeof delegated/sizeof delegated[0];i++)assert(send(&ui,session,delegated[i],42)==EP7P_UI_RAW_DELEGATE);
      assert(before==h.acquisitions); }
    assert(ep7p_ui_ops.sync(&ui,session,64,5)==EP7_UI_CHANGED);
    assert(send(&ui,session,0x9032,-4)==EP7_UI_CHANGED);
    assert(ep7p_capture(&core,11,4,&captured) && captured.hl[12]==-4 && captured.hl[0]==7);
    /* Real portable integration: attached capture is independent of later UI. */
    { unsigned char *memory=malloc(EP7P_EXTENT),output[EP7P_OUTPUT];
      ep7p_observation o={0}; uint64_t job,scope; uintptr_t b=(uintptr_t)memory;
      assert(memory && ep7p_register_job(&core,memory,EP7P_EXTENT,&captured,&job));
      assert(ep7p_register_task(&core,(ep7p_task){1,1}));
      o.job=b;o.request=b+11364;o.operation=b+14576;o.request_operation=o.operation;
      o.operation_job=b;o.operation_request=o.request;o.callback=0x60355fd4;
      o.stage=2;o.stage_callback=0x6036884d;o.raw_mode=11;o.raw_selector=4;
      assert(ep7p_enter(&core,job,&o,&scope));
      assert(send(&ui,session,0x9032,4)==EP7_UI_CHANGED); /* L now0, captured L still-4 */
      memset(output,0x5a,sizeof output);
      assert(ep7p_apply(&core,scope,job,&o,output,sizeof output));
      assert((unsigned)(output[706]+256u*output[707])==(uint16_t)-7000);
      assert((unsigned)(output[710]+256u*output[711])==(uint16_t)-150);
      for(i=0;i<12;i++)assert(output[708+24*i]==0x5a && output[709+24*i]==0x5a);
      assert(ep7p_unwind(&core,scope));assert(ep7p_release_job(&core,job));free(memory);
      assert(ep7p_release_task(&core,(ep7p_task){1,1})); }
    assert(ep7p_ui_ops.sync(&ui,session,57,4)==EP7_UI_REJECTED);
    assert(send(&ui,session,0x9032,0)==EP7_UI_REJECTED);
    assert(send(&ui,session,0x9014,0)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.sync(&ui,session,64,1)==EP7_UI_REJECTED);
    assert(send(&ui,session,0x9032,1)==EP7_UI_REJECTED);
    assert(ep7p_ui_ops.sync(&ui,session,64,4)==EP7_UI_CHANGED);
    h.fail=true;assert(send(&ui,session,0x9032,1)==EP7_UI_REJECTED);h.fail=false;
    ep7p_ui_ops.close(&ui,session);
    assert(send(&ui,session,0x9032,1)==EP7_UI_REJECTED);
    assert(send(&ui,session,0x9014,0)==EP7_UI_REJECTED);
    assert(ep7p_ui_raw_dispatch(&ui,session,NULL)==EP7_UI_REJECTED);
    puts("raw logical event + event-owned full delta -> normalized volatile H/L: PASS (host only)");
    return 0;
}
