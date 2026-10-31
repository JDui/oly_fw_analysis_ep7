#include "gate.h"
#define EP7_UI_GATE_INTEGRATION
#define EP7_INPUT_TEST_MAIN input_regressions
#include "../ui_native/test_input.c"

volatile uint32_t ep7_stock_selector_initializer_unresolved,ep7_stock_ui_active_content_unresolved;
const unsigned char ep7_native_selector_init_bridge[1]={31};
const uint32_t ep7_stock_mvc_category_keys_unresolved[32]={
    57,0x13b6,58,0x13b7,59,0x13b8,65,0x140d,54,0x13b3,55,0x13b4,56,0x13b5,64,0x140c,
    57,0x13b9,58,0x13ba,59,0x13bb,65,0x140e,54,0x140f,55,0x1410,56,0x1411,64,0x1412};
static unsigned stock_creates,stock_selected,timer_stops,stock_fail,stock_reentry;
static uint32_t stock_category,stock_args[2];
void *ep7_gcc_mvc_stock_create(unsigned category,const uint32_t args[2])
{
    assert(ep7_native_mvc.busy&&ep7_native_mvc.category>=4&&getpointer(parent+80)==&allocation);
    assert(ep7_native_content.child==&allocation&&category<4);
    assert(!ep7_stock_ui_active_content_unresolved&&!ep7_stock_ui_input_gate_unresolved);
    stock_creates++;stock_category=category;stock_args[0]=args[0];stock_args[1]=args[1];
    ep7_stock_ui_active_content_unresolved=7;ep7_stock_ui_input_gate_unresolved=8;
    if (stock_reentry==1) ep7m_before_parent_destroy(parent);
    if (stock_reentry==2) ep7m_before_viewer_destroy(viewer);
    if (stock_reentry==3) ep7c_rebuild(parent);
    if (stock_fail) return NULL;
    memset(stock_content,0xa5,sizeof stock_content);
    const uint32_t vt[4]={0x61155a7c,0x61187534,0x61187534,0x61159ea8};
    put32(stock_content,vt[category]);return stock_content;
}
void ep7_gcc_mvc_stock_selected(void *p)
{ assert(p==parent&&ep7_native_mvc.busy&&ep7_native_mvc.category==0&&getpointer(parent+80)==stock_content);stock_selected++; }
void ep7_gcc_mvc_transition_timers(void)
{ assert(ep7_native_mvc.busy);timer_stops++; }
static void gate_case(int runtime)
{
    input_poll_callback=NULL;memset(&ep7_native_ui_gate,0,sizeof ep7_native_ui_gate);
    ep7_stock_selector_initializer_unresolved=(uint32_t)(uintptr_t)ep7_native_selector_init_bridge;
    stock_creates=stock_selected=timer_stops=stock_fail=stock_reentry=0;
    ep7_stock_ui_active_content_unresolved=0;
    render_case(runtime);input_install_fixture();
}
static void ready_case(void)
{ gate_case(1);owner_complete();native_draw();assert(!masks[8]&&!masks[10]&&ep7_native_ui_gate.available); }
static void gated_hl(unsigned category)
{
    assert(!masks[8]&&!masks[10]);select_category(category);ep7c_rebuild(parent);native_draw();
    assert(ep7_native_mvc.category==category&&ep7_native_ui_receipt.ready);
}
static void expect_stock(unsigned category)
{
    assert(ep7_native_mvc.category==category&&selector[86]==category&&ep7_stock_selector_remembered_unresolved==category);
    assert(!ep7_native_content.child&&getpointer(parent+80)==stock_content&&!ep7_native_ui_receipt.ready);
    assert(!ep7_native_ui_model.session.generation&&!ep7_native_mvc.busy);
    assert(getpointer(viewer+392)==stock_content&&viewer[396]==category);
    assert(!get32(stock_content+32)&&!get32(stock_content+36));
}
int main(void)
{
    /*1 Actual runtime, owner, mode and complete cohorts enable only masks4/5. */
    gate_case(0);owner_complete();native_draw();assert(masks[8]&&masks[10]);
    select_category(4);ep7c_rebuild(parent);assert(selector[86]==2&&!allocations);
    assert(ep7r_publish(&ep7_native_runtime_slot,&shared_runtime));native_draw();assert(!masks[8]);
    gate_case(1);native_draw();assert(masks[8]);owner_complete();assert(!masks[8]);
    ep7_stock_selector_initializer_unresolved=0;native_draw();assert(masks[8]&&masks[10]);
    ep7_stock_selector_initializer_unresolved=(uint32_t)(uintptr_t)ep7_native_selector_init_bridge;
    ep7_input_far_calls[4*EP7_FAR_CALL_BYTES+4]=4;native_draw();assert(masks[8]);
    input_install_fixture();native_draw();assert(!masks[8]);
    const uint32_t color_modes[]={54,55,56,64};
    put16(masks+2,0x1234);uint8_t stock_masks[8];memcpy(stock_masks,masks,8);
    for (unsigned i=0;i<4;i++) { public_mode=color_modes[i];native_draw();assert(!masks[8]&&!masks[10]); }
    assert(!memcmp(stock_masks,masks,8)&&!timer_stops);

    /*2 Real admission, raw wheel and INFO; H/L/profile changes retain focus. */
    ready_case();put32(parent+16,3);put32(parent+20,0x9014);put32(parent+44,1);put32(parent+84,1);
    gated_hl(4);assert(timer_stops==1&&!get32(parent+16)&&!get32(parent+20)&&!get32(parent+44)&&!get32(parent+84));
    prepare_wheel(1,3,0);assert(deliver()==1);expect_text("H 01 +3");
    put32(packet,0x9014);ep7i_prepare_begin(packet);ep7i_prepare_end(packet,0);assert(deliver()==1);expect_text("H ALL MIX");
    uint32_t serial=ep7_native_ui_model.session.generation;
    gated_hl(5);expect_text("L ALL +0");public_mode=55;native_draw();expect_text("L ALL +0");
    assert(ep7_native_ui_model.session.generation==serial&&timer_stops==1);

    /*3 Every native factory kind is reused, with both original stack words. */
    for (unsigned category=0;category<4;category++) {
        ready_case();gated_hl(4);unsigned freed=private_frees;
        select_category(category);ep7c_rebuild(parent);native_draw();expect_stock(category);
        assert(stock_creates==1&&stock_category==category&&private_frees==freed+1&&timer_stops==2);
        assert(stock_args[0]==(category==0?111:category==3?383:category==1?0x13b3:0x140f));
        assert(stock_args[1]==54&&stock_selected==(category==0));
        assert(!stock_calls); /* The unsafe generic NULL post-write was not called. */
    }

    /*4 Exact32-bit mode, existing stock masks and last stock category determine exit. */
    ready_case();gated_hl(4);public_mode=57;native_draw();expect_stock(2);assert(stock_args[0]==0x13b9&&masks[8]);
    ready_case();select_category(1);ep7c_rebuild(parent);native_draw();gated_hl(5);
    public_mode=57;native_draw();expect_stock(1);assert(stock_args[0]==0x13b6);
    ready_case();gated_hl(4);public_mode=0x10036;put16(masks,1);put16(masks+4,1);
    memcpy(stock_masks,masks,8);native_draw();expect_stock(3);
    assert(stock_args[1]==0x10036&&!memcmp(stock_masks,masks,8)&&masks[8]&&masks[10]);
    ready_case();gated_hl(4);ep7r_stop(&shared_runtime);native_draw();expect_stock(2);assert(masks[8]);

    /*5 No eligible stock or allocation failure preserves ownership and blocks edits. */
    ready_case();gated_hl(4);for (unsigned i=0;i<4;i++) put16(masks+2*i,1);
    public_mode=57;native_draw();assert(!stock_creates&&ep7_native_content.child==&allocation&&masks[8]&&masks[10]);
    assert(selector[86]==4&&ep7_stock_selector_remembered_unresolved==4&&!ep7_native_ui_receipt.ready);
    assert(!ep7_native_ui_model.session.generation);expect_text("");
    put16(masks+4,0);native_draw();expect_stock(2);
    ready_case();gated_hl(5);stock_fail=1;public_mode=57;
    ep7_stock_ui_active_content_unresolved=101;ep7_stock_ui_input_gate_unresolved=102;
    unsigned stopped=timer_stops;native_draw();
    assert(stock_creates==1&&timer_stops==stopped+1&&!private_frees&&ep7_native_content.child==&allocation);
    assert(ep7_stock_ui_active_content_unresolved==101&&ep7_stock_ui_input_gate_unresolved==102);
    assert(selector[86]==5&&ep7_stock_selector_remembered_unresolved==5&&!ep7_native_ui_receipt.ready&&masks[8]);
    stock_fail=0;native_draw();expect_stock(2);assert(stock_creates==2&&private_frees==1);

    /*6 A wheel which causes H/L exit, including repeat delivery, never edits S. */
    ready_case();gated_hl(4);prepare_wheel(1,4,0);public_mode=57;
    struct ep7i_dispatch call=dispatch_call();unsigned held=ep7i_dispatch_begin(&call);put16(machine+8,137);
    assert(!route_current());expect_stock(2);assert(ep7_native_ui_input_scope.consumed==2);
    assert(!route_current());ep7i_dispatch_end(held);
    prepare_wheel(1,2,0);assert(deliver()==EP7_NATIVE_CALL_STOCK);
    ep7p_snapshot snapshot;assert(ep7p_capture(&shared_core,11,1,&snapshot));assert(snapshot.hl[0]==0);

    /*7 Text/owner failure normalizes without following foreign owner pointers. */
    ready_case();reject_text=1;native_draw();assert(masks[8]&&masks[10]&&!stock_creates&&!allocations);
    ready_case();select_category(4);ep7c_rebuild(parent);reject_text=1;ep7v_refresh();
    expect_stock(2);assert(masks[8]&&stock_creates==1); /* Old viewer cache cannot hide clear failure. */
    ready_case();gated_hl(4);reject_text=1;native_draw();expect_stock(2);
    assert(!ep7_native_ui_owner.display_ready&&masks[8]&&stock_creates==1);
    ready_case();gated_hl(5);unsigned sets=text_sets;pointer(ui_service+416,(void *)1);
    native_draw();expect_stock(2);assert(text_sets==sets&&masks[8]);
    ready_case();ep7_native_ui_model.serial=UINT32_MAX;native_draw();assert(masks[8]&&masks[10]);
    select_category(4);ep7c_rebuild(parent);assert(!allocations&&selector[86]==2);

    /*8 Factory callbacks cannot retire or rebuild the held graph before publish. */
    for (volatile unsigned i=1;i<=3;i++) {
        ready_case();gated_hl(4);stock_reentry=i;public_mode=57;
        if (!setjmp(fatal)) { native_draw();assert(!"stock creator reentry escaped"); }
        assert(quarantines==1&&ep7_native_mvc.busy&&!private_frees&&ep7_native_content.child==&allocation);
    }
    return 0;
}
