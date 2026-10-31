#include "native_lifecycle.h"
#include "../text_rollback/native_context.h"
#include "../text_viewer/text.h"
#include "../runtime/task_context.h"
#include <assert.h>
#include <string.h>

static uint8_t owner[1360],service[2880],child[180],resource[94];
static uint16_t text[EP7_TEXT_UNITS];
static struct {int mode,queries,qualifies,creates,attaches,binds,sets,destroys,member;} f;
static void put32(uint8_t *p,uint32_t n)
{ for (unsigned i=0;i<4;i++) p[i]=(uint8_t)(n>>(8*i)); }
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *t)
{
    (void)anchor;f.queries++;
    *t=(ep7n_task){0x101,0,0x1000,0x60dd5067,0x2000,16384};
    if (f.mode==7) t->domain=1;
    return !(f.mode==10&&f.queries==2);
}
void *ep7_gcc_ui_service(void) { return service; }
uint16_t ep7_gcc_ui_context_exchange(void *p,uint16_t value)
{
    assert(p==service);uint16_t prior=(uint16_t)(service[28]|((uint16_t)service[29]<<8));
    service[28]=(uint8_t)value;service[29]=(uint8_t)(value>>8);return prior;
}
void ep7_gcc_ui_context_select(void *p,uint16_t value)
{ (void)ep7_gcc_ui_context_exchange(p,value); }
static int qualify(void *ctx,const void *o,size_t on,const void *r,size_t rn)
{
    assert(ctx==&f&&on==1360&&rn==94);f.qualifies++;
    if (f.mode==6) return 0; /* o/r deliberately invalid; never inspect them. */
    assert(o==owner&&r==resource);return 1;
}
void ep7_gcc_text_factory(void *o,const void *r,struct ep7_text_factory_result *out)
{
    assert(o==owner&&r==resource&&service[28]==3&&service[29]==4);f.creates++;
    *out=(struct ep7_text_factory_result){f.mode==1?NULL:child,f.mode==2||f.mode==10?0:1};
}
void ep7_gcc_text_cleanup_destroy_unresolved(void *p)
{
    assert(p==child&&!f.member&&service[28]==3&&service[29]==4);f.destroys++;
    memset(child,0xa5,sizeof child);
}
int ep7_gcc_ui_attach(void *o,void *p)
{
    assert(o==owner&&p==child&&!f.member);f.attaches++;
    if (f.mode==3) return 0;
    f.member=1;return 1;
}
int ep7_gcc_text_bind(void *p,void *o)
{
    assert(p==child&&o==owner&&f.member);f.binds++;
    put32(child+20,f.mode==12?0:(uint32_t)(uintptr_t)o);
    return f.mode==4?0:-1;
}
int ep7_gcc_set_text_unresolved_binding(void *p,const uint16_t *t)
{
    assert(p==child&&f.member&&t==text&&t[0]=='H');f.sets++;
    return f.mode==5?0:1;
}
int main(void)
{
    for (int mode=0;mode<15;mode++) {
        memset(&f,0,sizeof f);memset(owner,0,sizeof owner);memset(service,0,sizeof service);
        memset(child,0,sizeof child);memset(resource,0,sizeof resource);memset(text,0,sizeof text);
        struct ep7_text_native state={0};f.mode=mode;text[0]='H';
        put32(owner,0x61032f10);put32(service,0x60faaab4);put32(child,0x60faec7c);
        service[4]=service[5]=1;service[80]=2;service[28]=0x81;service[29]=0xfe;
        owner[28]=child[28]=3;owner[29]=child[29]=4;resource[0]=child[4]=0x10;resource[1]=child[5]=0x80;
        if (mode==8) service[82]=2;
        if (mode==9) owner[0]++;
        if (mode==11) for (unsigned i=0;i<EP7_TEXT_UNITS;i++) text[i]='X';
        if (mode==13) resource[84]=1;
        if (mode==14) service[0]++;
        void *o=mode==6?(void *)(uintptr_t)1:owner;
        const void *r=mode==6?(void *)(uintptr_t)1:resource;
        int result=ep7_text_native_open(&state,o,r,text,qualify,&f);
        assert(service[28]==0x81&&service[29]==0xfe);
        if (mode==0) assert(result==1&&state.attached.bound&&f.sets==1);
        else if (mode==4||mode==5||mode==12) {
            assert(result==0&&state.attached.child==child&&!f.destroys);
            assert(state.attached.bound==(mode==5));
        } else if (mode==10) {
            assert(result==EP7_TEXT_NATIVE_RETAINED&&state.fresh.child==child&&!f.destroys&&!f.member);
            assert(!ep7_text_native_revoke(&state));
            assert(ep7_text_native_open(&state,owner,resource,text,qualify,&f)==-1);
            assert(f.creates==1&&ep7_text_native_retry_rollback(&state)==1&&f.destroys==1);
            assert(!state.fresh.child&&!state.owner&&service[28]==0x81&&service[29]==0xfe);
        } else assert(result==-1&&!state.attached.child&&!state.fresh.child);
        if (mode==2||mode==3) assert(f.destroys==1&&!f.member);
        if (mode==6||mode==7||mode==8||mode==9||mode==11||mode==13||mode==14) assert(!f.creates);
        if (mode==7) assert(!f.qualifies);
        if (state.attached.child) {
            assert(!ep7_text_native_retry_rollback(&state));
            assert(ep7_text_native_open(&state,owner,resource,text,qualify,&f)==-1&&f.creates==1);
        }
        int destroyed=f.destroys;
        assert(ep7_text_native_revoke(&state)==1&&!state.attached.child&&!state.owner&&f.destroys==destroyed);
    }
    return 0;
}
