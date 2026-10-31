#include "viewer.h"
#include "../ui_model/model.h"
#include "../ui_owner/owner.h"
#include "../text_rollback/native_context.h"
#include "../text_viewer/text.h"
#define EP7_UI_RENDER_INTEGRATION
#define EP7_CONTENT_TEST_MAIN content_regressions
#include "../ui_content/test_content.c"

volatile uint32_t ep7_stock_ui_service_vtable_unresolved[197],ep7_stock_ui_display_vtable_unresolved[109];
const unsigned char ep7_native_ui_screen_bridge[1]={11},ep7_native_ui_owner_cleanup_bridge[1]={12};
const unsigned char ep7_native_ui_owner_bulk_bridge[1]={13},ep7_native_ui_owner_destructor_bridge[1]={14};
static uint8_t ui_service[2880],display_owner[1360],text_child[180];
static uint16_t rendered[EP7_TEXT_UNITS];
static unsigned text_sets,text_allocs,text_member,reject_text,reenter_text,poll_held,poll_fail;
static uint32_t public_mode;
static ep7p shared_core;
static ep7b shared_boot;
static ep7r shared_runtime;
#ifdef EP7_UI_INPUT_INTEGRATION
static void (*input_poll_callback)(void);
#endif
uint32_t ep7_gcc_ui_public_mode(void) { assert(ep7_native_mvc.busy);return public_mode; }
void *ep7_gcc_ui_service(void) { return ui_service; }
uint16_t ep7_gcc_ui_context_exchange(void *p,uint16_t value)
{
    assert(p==ui_service);uint16_t prior=(uint16_t)(ui_service[28]|((uint16_t)ui_service[29]<<8));
    put16(ui_service+28,value);return prior;
}
void ep7_gcc_ui_context_select(void *p,uint16_t value) { (void)ep7_gcc_ui_context_exchange(p,value); }
void ep7_text_resource_prepare(struct ep7_text_resource *r)
{
    memset(r,0,sizeof *r);put16(r->descriptor,0x8010);put16(r->descriptor+2,EP7_HL_TEXT_WIDGET_ID);
    pointer(r->descriptor+4,r->layouts);put32(r->descriptor+12,0x61030a5c);
    r->descriptor[8]=9;r->descriptor[48]=1;
}
void *ep7_gcc_ui_find_child(void *o,uint16_t id)
{ assert(o==display_owner&&id==EP7_HL_TEXT_WIDGET_ID);return text_member?text_child:NULL; }
void ep7_gcc_text_factory(void *o,const void *r,struct ep7_text_factory_result *out)
{
    assert(o==display_owner&&r==ep7_native_ui_owner.resource.descriptor&&!text_member);
    assert(ep7_native_ui_owner.opening&&ui_service[28]==6&&ui_service[29]==0);
    text_allocs++;memset(text_child,0,sizeof text_child);put32(text_child,0x60faec7c);
    put16(text_child+4,0x8010);put16(text_child+6,EP7_HL_TEXT_WIDGET_ID);text_child[28]=6;
    *out=(struct ep7_text_factory_result){text_child,1};
}
int ep7_gcc_ui_attach(void *o,void *c)
{ assert(o==display_owner&&c==text_child&&!text_member);text_member=1;return 1; }
int ep7_gcc_text_bind(void *c,void *o) { assert(c==text_child&&text_member);pointer(text_child+20,o);return -1; }
void ep7_gcc_text_cleanup_destroy_unresolved(void *c)
{ assert(c==text_child&&!text_member);memset(c,0xcd,sizeof text_child); }
int ep7_gcc_set_text_unresolved_binding(void *c,const uint16_t *text)
{
    assert(c==text_child&&text_member&&ep7_native_ui_owner.text.busy);
    assert(ui_service[28]==6&&ui_service[29]==0);text_sets++;
    if (reenter_text==1) { struct ep7u_screen_call call={ui_service,278,0,0};ep7u_screen_enter(&call); }
    if (reenter_text==2) ep7m_before_parent_destroy(parent);
    if (reenter_text==3) (void)ep7v_draw_begin(viewer);
    if (reject_text) return 0;
    for (unsigned i=0;i<EP7_TEXT_UNITS;i++) { rendered[i]=text[i];if (!text[i]) return 1; }
    assert(!"unterminated text");return 0;
}
static int sem_tid(void *ctx,uint16_t *tid) { (void)ctx;*tid=0x101;return 0; }
static int sem_create(void *ctx,const ep7b_sem_spec *spec)
{ (void)ctx;assert(!spec->attributes&&spec->initial==1&&spec->maximum==1);return 1; }
static int sem_delete(void *ctx,unsigned id) { (void)ctx;assert(id==1);return 0; }
static int sem_poll(void *ctx,uint16_t id)
{
    (void)ctx;assert(id==1&&!poll_held);
#ifdef EP7_UI_INPUT_INTEGRATION
    if (input_poll_callback) input_poll_callback();
#endif
    if (poll_fail) return -50;
    poll_held=1;return 0;
}
static int sem_signal(void *ctx,uint16_t id) { (void)ctx;assert(id==1&&poll_held);poll_held=0;return 0; }
static bool installed_fixture(void *ctx) { (void)ctx;return true; }
static bool env_task(void *ctx,uint32_t anchor,ep7n_task *out)
{ (void)ctx;return ep7n_native_current_task(anchor,out); }
static bool env_queue(void *ctx,unsigned id,ep7n_queue *out)
{
    (void)ctx;unsigned maximum=id==0x4b?148:id==0x4d?300:312;
    unsigned ring=id==0x4b?4864:id==0x4d?9728:10112;
    *out=(ep7n_queue){(uint16_t)id,0,0x1000,0x2000,0x3000+id*32,128,maximum,ring,0x10000+id*0x10000};return true;
}
static int env_delay(void *ctx) { (void)ctx;assert(!"UI path must not sleep");return 0; }
static void env_fatal(void *ctx,unsigned reason) { (void)ctx;(void)reason;assert(!"unexpected runtime fault"); }
static void render_case(int publish_runtime)
{
    memset(&ep7_native_ui_owner,0,sizeof ep7_native_ui_owner);atomic_init(&ep7_native_ui_owner.started,false);
    memset(&ep7_native_ui_model,0,sizeof ep7_native_ui_model);memset(&ep7_native_ui_receipt,0,sizeof ep7_native_ui_receipt);
    memset(&shared_core,0,sizeof shared_core);memset(&shared_boot,0,sizeof shared_boot);
    memset(&shared_runtime,0,sizeof shared_runtime);atomic_store(&ep7_native_runtime_slot.published,NULL);
    memset(ui_service,0,sizeof ui_service);memset(display_owner,0,sizeof display_owner);
    memset(text_child,0,sizeof text_child);memset(rendered,0,sizeof rendered);
    text_sets=text_allocs=text_member=reject_text=reenter_text=poll_held=poll_fail=0;public_mode=54;
    put32(ui_service,0x60faaab4);put16(ui_service+4,0x0101);put16(ui_service+80,2);
    ui_service[28]=0x81;ui_service[29]=0xfe;
    ep7_stock_ui_service_vtable_unresolved[196]=(uint32_t)(uintptr_t)ep7_native_ui_screen_bridge;
    ep7_stock_ui_display_vtable_unresolved[38]=(uint32_t)(uintptr_t)ep7_native_ui_owner_cleanup_bridge;
    ep7_stock_ui_display_vtable_unresolved[108]=(uint32_t)(uintptr_t)ep7_native_ui_owner_bulk_bridge;
    ep7_stock_ui_display_vtable_unresolved[0]=(uint32_t)(uintptr_t)ep7_native_ui_owner_destructor_bridge;
    begin_case();
    ep7b_native n={NULL,sem_create,sem_delete,{NULL,sem_tid,sem_poll,sem_signal}};
    assert(ep7b_prepare(&shared_boot,&shared_core,n));
    ep7r_environment e={NULL,installed_fixture,env_task,env_queue,env_delay,env_fatal};
    assert(ep7r_prepare(&shared_runtime,&shared_boot,e));
    if (publish_runtime) assert(ep7r_publish(&ep7_native_runtime_slot,&shared_runtime));
}
static void owner_complete(void)
{
    struct ep7u_screen_call call={ui_service,278,1,0};ep7u_screen_enter(&call);
    put32(display_owner,0x61032f10);put16(display_owner+4,0x6111);put16(display_owner+6,0x0112);
    pointer(display_owner+20,ui_service);display_owner[28]=6;put32(display_owner+92,0x60f94aa0);
    ui_service[1378]=1;pointer(ui_service+416,display_owner);ep7u_screen_leave(&call);
    assert(ui_service[28]==0x81&&ui_service[29]==0xfe);
}
static void native_draw(void)
{
    unsigned held=ep7v_draw_begin(viewer);
    /* Full original draw and property/queue delivery are boundary fixtures. */
    pointer(viewer+388,selector);pointer(viewer+392,getpointer(parent+80));
    put16(viewer+396,selector[86]);put32(viewer+400,public_mode);
    ep7v_draw_end(viewer,held);
}
static void enter_hl(unsigned category)
{ enable_fixture_hl();select_category(category);ep7c_rebuild(parent);native_draw(); }
static void expect_text(const char *text)
{ unsigned i;for (i=0;text[i];i++) assert(rendered[i]==(unsigned char)text[i]);assert(!rendered[i]); }
#ifndef EP7_VIEWER_TEST_MAIN
#define EP7_VIEWER_TEST_MAIN main
#endif
int EP7_VIEWER_TEST_MAIN(void)
{
    assert(!content_regressions()); /* Six MVC + six content groups, now joined to actual renderer C. */
    /*1 Both asynchronous ordering cases converge without a guessed ready flag. */
    render_case(1);enter_hl(4);assert(!ep7_native_ui_receipt.ready&&!text_allocs);
    owner_complete();assert(ep7_native_ui_receipt.ready&&text_allocs==1);expect_text("H 01 +0");
    render_case(1);owner_complete();enter_hl(4);assert(ep7_native_ui_receipt.ready);expect_text("H 01 +0");
    uint32_t prior_owner_generation=ep7_native_ui_receipt.owner_generation;
    struct ep7u_screen_call failed_switch={ui_service,278,0,0};ep7u_screen_enter(&failed_switch);
    assert(!ep7_native_ui_receipt.ready);ep7u_screen_leave(&failed_switch);
    assert(ep7_native_ui_receipt.ready&&ep7_native_ui_receipt.owner_generation>prior_owner_generation);
    assert(ep7_native_ui_model.runtime==&shared_runtime&&ep7_native_ui_model.ui.core==shared_boot.core);
    /*2 Normalized fixture edits use the same core captured by image snapshots. */
    struct ep7cm_model *model=&ep7_native_ui_model;
    assert(ep7p_ui_ops.event(&model->ui,model->session,EP7_UI_VALUE_INCREASE,3)==EP7_UI_CHANGED);
    native_draw();expect_text("H 01 +3");
    ep7p_snapshot frozen;assert(ep7p_capture(&shared_core,11,1,&frozen));assert(frozen.hl[0]==3);
    uint32_t serial=model->session.generation;
    assert(ep7p_ui_ops.event(&model->ui,model->session,EP7_UI_TOGGLE_ALL,1)==EP7_UI_CHANGED);
    select_category(5);ep7c_rebuild(parent);native_draw();expect_text("L ALL +0");assert(model->session.generation==serial);
    assert(ep7p_ui_ops.event(&model->ui,model->session,EP7_UI_VALUE_DECREASE,2)==EP7_UI_CHANGED);
    native_draw();expect_text("L ALL -2");assert(frozen.hl[12]==0&&frozen.hl[0]==3);
    public_mode=55;native_draw();expect_text("L ALL +0"); /* Different COLOR profile, same selection. */
    /*3 Reentry within one MVC generation consumes a new independent UI serial. */
    struct ep7_ui_session old=model->session;uint32_t mvc_gen=ep7_native_mvc.generation;
    select_category(2);ep7c_rebuild(parent);native_draw();expect_text("");assert(!model->session.generation);
    select_category(4);ep7c_rebuild(parent);native_draw();expect_text("H 01 +0");
    assert(ep7_native_mvc.generation==mvc_gen&&model->session.generation>old.generation);
    assert(ep7p_ui_ops.event(&model->ui,old,EP7_UI_VALUE_INCREASE,1)==EP7_UI_REJECTED);
    ep7m_before_viewer_destroy(viewer);expect_text("");assert(!model->session.generation&&!ep7_native_ui_receipt.ready);
    /*4 Unpublished/unsupported/stopped runtime cannot make a ready frame. */
    render_case(0);owner_complete();enter_hl(4);assert(!model->runtime&&!ep7_native_ui_receipt.ready);
    assert(ep7r_publish(&ep7_native_runtime_slot,&shared_runtime));native_draw();assert(ep7_native_ui_receipt.ready);
    public_mode=0x10036;native_draw();expect_text("");assert(!model->session.generation); /* No uint16 truncation to54. */
    public_mode=54;native_draw();assert(ep7_native_ui_receipt.ready);
    poll_fail=1;native_draw();assert(!ep7_native_ui_receipt.ready&&model->session.generation);poll_fail=0;
    native_draw();assert(ep7_native_ui_receipt.ready);
    ep7r_stop(&shared_runtime);native_draw();expect_text("");assert(!model->session.generation);
    /*5 Owner mismatch/failure latches display unavailable; no duplicate factory. */
    render_case(1);owner_complete();enter_hl(4);unsigned sets=text_sets;
    pointer(ui_service+416,(void *)1);native_draw();assert(!ep7_native_ui_receipt.ready&&text_sets==sets);
    pointer(ui_service+416,display_owner);native_draw();assert(!ep7_native_ui_receipt.ready&&text_allocs==1);
    render_case(1);owner_complete();enter_hl(4);reject_text=1;native_draw();
    assert(!ep7_native_ui_receipt.ready&&!ep7_native_ui_owner.display_ready);reject_text=0;
    native_draw();assert(!ep7_native_ui_receipt.ready&&text_allocs==1);
    render_case(1);owner_complete();enter_hl(4);text_member=0;sets=text_sets;native_draw();
    assert(!ep7_native_ui_receipt.ready&&text_sets==sets);
    /*6 Text update holds both native lifetimes across recursive callbacks. */
    for (volatile unsigned i=1;i<=3;i++) {
        render_case(1);owner_complete();enter_hl(4);reenter_text=i;
        if (!setjmp(fatal)) { native_draw();assert(!"text callback escaped guards"); }
        assert(quarantines==1&&ep7_native_mvc.busy&&ep7_native_ui_owner.text.busy&&!private_frees);
    }
    /*7 Token exhaustion and replacement of the permanently published core stop. */
    render_case(1);owner_complete();model->serial=UINT32_MAX;enter_hl(4);
    assert(!model->session.generation&&!ep7_native_ui_receipt.ready&&model->serial==UINT32_MAX);
    render_case(1);owner_complete();enter_hl(4);atomic_store(&ep7_native_runtime_slot.published,NULL);
    if (!setjmp(fatal)) { native_draw();assert(!"runtime unpublication accepted"); }
    assert(quarantines==1);
    render_case(1);owner_complete();enter_hl(4);pointer(viewer+384,(void *)1);
    if (!setjmp(fatal)) { native_draw();assert(!"invalid owned draw delegated"); }
    assert(quarantines==1);
    return 0;
}
