#include "input.h"
#define EP7_UI_INPUT_INTEGRATION
#define EP7_VIEWER_TEST_MAIN viewer_regressions
#include "../ui_render/test_viewer.c"
volatile uint32_t ep7_stock_gui_machine_unresolved,ep7_stock_ui_input_gate_unresolved;
volatile uint32_t ep7_stock_ui_repeat_context_unresolved;
volatile unsigned char ep7_stock_ui_preprocess_call_unresolved[7],ep7_stock_ui_dispatch_call_unresolved[7];
volatile unsigned char ep7_stock_ui_wheel_1_call_unresolved[5],ep7_stock_ui_wheel_0_call_unresolved[5];
volatile unsigned char ep7_stock_ui_wheel_2_call_unresolved[5],ep7_stock_ui_wheel_4_call_unresolved[5];
volatile unsigned char ep7_stock_ui_wheel_3_call_unresolved[5];
unsigned char ep7_input_far_calls[5*EP7_FAR_CALL_BYTES];
__asm__(".globl ep7_input_far_calls_end\n.set ep7_input_far_calls_end,ep7_input_far_calls+150");
const unsigned char ep7_native_ui_preprocess_bridge[1]={21},ep7_native_ui_dispatch_bridge[1]={22};
const unsigned char ep7_native_ui_event_bridge[1]={23};
volatile unsigned char ep7_fixture_sample_target[1];
extern const unsigned char ep7_native_ui_wheel_sample_bridge[];
__asm__(".globl ep7_native_ui_wheel_sample_bridge\n"
        ".set ep7_native_ui_wheel_sample_bridge,ep7_fixture_sample_target");
static uint8_t packet[28],machine[12];
static unsigned info_drops;
static uint32_t get32(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
void ep7_gcc_ui_drop_info(void)
{ assert(ep7_native_mvc.busy&&ep7_native_ui_owner.text.busy);info_drops++; }
static void patch_input_call(volatile unsigned char *p,const void *target,unsigned wide,unsigned mask,unsigned frame)
{
    intptr_t delta=(intptr_t)target-(intptr_t)p;
    if (!wide) assert(delta>=INT16_MIN&&delta<=INT16_MAX);
    uint32_t d=(uint32_t)delta;p[0]=wide?0xdd:0xcd;
    for (unsigned i=0;i<(wide?4u:2u);i++) p[1+i]=(uint8_t)(d>>(8*i));
    p[wide?5:3]=(uint8_t)mask;p[wide?6:4]=(uint8_t)frame;
}
static void input_install_fixture(void)
{
    memset(&ep7_native_ui_input_scope,0,sizeof ep7_native_ui_input_scope);
    atomic_init(&ep7_native_ui_input_scope.started,false);
    memset(packet,0,sizeof packet);memset(machine,0,sizeof machine);machine[0]=4;machine[1]=29;
    ep7_stock_gui_machine_unresolved=(uint32_t)(uintptr_t)machine;
    ep7_stock_ui_input_gate_unresolved=ep7_stock_ui_repeat_context_unresolved=info_drops=0;
    ep7_stock_mvc_parent_vtable_unresolved[0]=(uint32_t)(uintptr_t)ep7_native_ui_event_bridge;
    patch_input_call(ep7_stock_ui_preprocess_call_unresolved,ep7_native_ui_preprocess_bridge,1,0xb0,224);
    patch_input_call(ep7_stock_ui_dispatch_call_unresolved,ep7_native_ui_dispatch_bridge,1,0xf0,48);
    volatile unsigned char *sites[]={ep7_stock_ui_wheel_1_call_unresolved,ep7_stock_ui_wheel_0_call_unresolved,
        ep7_stock_ui_wheel_2_call_unresolved,ep7_stock_ui_wheel_4_call_unresolved,ep7_stock_ui_wheel_3_call_unresolved};
    for (unsigned i=0;i<5;i++) ep7_far_fixture(sites[i],ep7_input_far_calls+i*EP7_FAR_CALL_BYTES,
                                              ep7_native_ui_wheel_sample_bridge,0,0);
    assert(ep7i_native_cohort_present());
}
static void input_case(unsigned category)
{
    input_poll_callback=NULL;render_case(1);input_install_fixture();owner_complete();enter_hl(category);
}
static const uint32_t source_event[5]={0x9031,0x9032,0x904f,0x9051,0x9050};
static const uint32_t sample_pc[5]={0x60ea0075,0x60ea00fc,0x60ea0d75,0x60ea0df0,0x60ea0e6b};
static const uint32_t output_event[5]={0x9031,0x9032,0x9031,0x9031,0x9032};
static void prepare_wheel(unsigned source,int32_t delta,unsigned status)
{
    put32(packet,source_event[source]);put32(packet+12,123);put32(packet+16,17);
    ep7i_prepare_begin(packet);
    struct ep7i_sample sample={(uint32_t)(uintptr_t)packet,(uint32_t)delta,sample_pc[source],status,status};
    ep7i_sample_wheel(&sample);
    put32(packet,output_event[source]);
    int32_t normalized=delta>0?(output_event[source]==0x9031&&delta>=2?2:1):-1;
    put32(packet+12,(uint32_t)normalized);ep7i_prepare_end(packet,0);
}
static struct ep7i_dispatch dispatch_call(void)
{
    return (struct ep7i_dispatch){get32(packet),get32(packet+12),get32(packet+16),
        (uint32_t)(uintptr_t)machine,(uint32_t)(uintptr_t)packet};
}
static uint32_t route_current(void)
{
    struct ep7_native_ui_input in={get32(packet),get32(packet+12),(uint32_t)(uintptr_t)parent,
        0x60e4d101,(uint32_t)(uintptr_t)container};
    return ep7_gcc_ui_route(&in);
}
static unsigned deliver(void)
{
    struct ep7i_dispatch call=dispatch_call();unsigned held=ep7i_dispatch_begin(&call);
    put16(machine+8,137);unsigned result=route_current();
    if (result==1) native_draw();
    ep7i_dispatch_end(held);return result;
}
static void recursive_screen(void)
{ struct ep7u_screen_call call={ui_service,278,0,0};ep7u_screen_enter(&call); }
static void recursive_prepare(void) { ep7i_prepare_begin(packet); }
static void recursive_retire(void) { ep7m_before_parent_destroy(parent); }
#ifndef EP7_INPUT_TEST_MAIN
#define EP7_INPUT_TEST_MAIN main
#endif
int EP7_INPUT_TEST_MAIN(void)
{
    assert(!viewer_regressions());
    /*1 Five actual sample origins; packet direction/capped count is never delta. */
    for (unsigned i=0;i<5;i++) {
        input_case(4);prepare_wheel(i,5,0);assert(deliver()==1);
        expect_text(output_event[i]==0x9031?"H 06 +0":"H 01 +5");
        assert(!ep7_native_ui_input_scope.phase&&!ep7_native_mvc.busy&&!ep7_native_ui_owner.text.busy);
    }
    input_case(5);prepare_wheel(1,-4,0);assert(deliver()==1);expect_text("L 01 -4");
    ep7p_snapshot frozen;assert(ep7p_capture(&shared_core,11,1,&frozen));assert(frozen.hl[12]==-4);
    prepare_wheel(1,2,0);assert(deliver()==1);expect_text("L 01 -2");assert(frozen.hl[12]==-4);
    /*2 Complete preprocess/engine scope, one-use consumption, and duplicate sample rejection. */
    input_case(4);prepare_wheel(1,3,0);assert(route_current()==0);
    struct ep7i_dispatch call=dispatch_call();unsigned held=ep7i_dispatch_begin(&call);assert(held==1);
    put16(machine+8,137);assert(route_current()==1);native_draw();assert(route_current()==0);
    ep7i_dispatch_end(held);assert(route_current()==0);expect_text("H 01 +3");
    input_case(4);put32(packet,0x9032);ep7i_prepare_begin(packet);
    struct ep7i_sample sample={(uint32_t)(uintptr_t)packet,7,0x60ea00fc,0,0};
    ep7i_sample_wheel(&sample);ep7i_sample_wheel(&sample);put32(packet+12,1);ep7i_prepare_end(packet,0);
    assert(!deliver());expect_text("H 01 +0");
    /*3 Service failure, bounded full counts, altered packet and machine identity. */
    input_case(4);prepare_wheel(1,7,1);assert(!deliver());
    prepare_wheel(1,-32768,0);assert(!deliver());prepare_wheel(1,65,0);assert(!deliver());
    prepare_wheel(1,0,0);assert(!deliver());expect_text("H 01 +0");
    prepare_wheel(1,3,0);call=dispatch_call();call.parameter=3;assert(!ep7i_dispatch_begin(&call));assert(!route_current());
    prepare_wheel(1,3,0);call=dispatch_call();call.extra++;assert(!ep7i_dispatch_begin(&call));
    prepare_wheel(1,3,0);machine[1]=28;assert(!deliver());machine[1]=29;
    prepare_wheel(1,3,0);ep7_stock_gui_machine_unresolved=1;assert(!deliver());expect_text("H 01 +0");
    /*4 INFO follows its zero-only modal gate; no invented hold/reset mapping. */
    input_case(4);put32(packet,0x9014);ep7i_prepare_begin(packet);ep7i_prepare_end(packet,0);
    ep7_stock_ui_input_gate_unresolved=0x9014;assert(!deliver()&&!info_drops);expect_text("H 01 +0");
    ep7_stock_ui_input_gate_unresolved=0;ep7i_prepare_begin(packet);ep7i_prepare_end(packet,0);
    ep7_stock_ui_repeat_context_unresolved=1;assert(deliver()==1&&info_drops==1);expect_text("H ALL +0");
    assert(get32(parent+24)==0x9014&&get32(parent+28)==get32(packet+12)&&parent[36]==200&&!parent[37]);
    prepare_wheel(1,2,0);assert(deliver()==1);expect_text("H ALL +2");
    /*5 Receipt, mode, masks and actual owner membership all required. */
    input_case(4);prepare_wheel(1,3,0);ep7_native_ui_receipt.session_generation++;assert(!deliver());
    native_draw();prepare_wheel(1,3,0);put16(masks+8,1);assert(!deliver());put16(masks+8,0);
    native_draw();prepare_wheel(1,3,0);public_mode=55;assert(!deliver());
    input_case(4);prepare_wheel(1,3,0);pointer(ui_service+416,(void *)1);assert(!deliver());
    assert(!ep7_native_ui_owner.display_ready&&!ep7_native_ui_receipt.ready);
    input_case(4);prepare_wheel(1,3,0);text_member=0;assert(!deliver());
    input_case(4);prepare_wheel(1,3,0);poll_fail=1;assert(!deliver());poll_fail=0;native_draw();expect_text("H 01 +0");
    /*6 Native/core callbacks cannot retire either owner or nest preparation. */
    void (*callbacks[])(void)={recursive_screen,recursive_prepare,recursive_retire};
    for (volatile unsigned i=0;i<3;i++) {
        input_case(4);prepare_wheel(1,3,0);input_poll_callback=callbacks[i];
        if (!setjmp(fatal)) { (void)deliver();assert(!"input hold escaped"); }
        assert(quarantines==1&&ep7_native_mvc.busy&&ep7_native_ui_owner.text.busy);
    }
    input_poll_callback=NULL;
    /*7 Stock categories/unowned objects/unsupported keys retain native route. */
    input_case(4);struct ep7_native_ui_input in={0x9004,0,(uint32_t)(uintptr_t)parent,0,0};
    assert(ep7_gcc_ui_route(&in)==256);in.event=0x9016;assert(ep7_gcc_ui_route(&in)==256);
    in.event=0x9032;in.parent=1;assert(ep7_gcc_ui_route(&in)==256);
    select_category(1);ep7c_rebuild(parent);native_draw();in.parent=(uint32_t)(uintptr_t)parent;
    assert(ep7_gcc_ui_route(&in)==256);
    /*8 Actual CALL cohort and packet extent fail before arbitrary reads. */
    input_case(4);ep7_input_far_calls[4*EP7_FAR_CALL_BYTES+4]=4;assert(!ep7i_native_cohort_present());
    if (!setjmp(fatal)) { ep7i_prepare_begin(packet);assert(!"broken cohort accepted"); }
    assert(quarantines==1);
    input_case(4);if (!setjmp(fatal)) { ep7i_prepare_begin((void *)1);assert(!"foreign packet read"); }
    assert(quarantines==1);
    return 0;
}
