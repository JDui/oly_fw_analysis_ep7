#include "native_context.h"
#include "../runtime/task_context.h"
#include <assert.h>
#include <string.h>

static uint8_t child[180],service[32],other[32];
static struct {int scenario,queries,gets,admissions,exchanges,selects,destroys;} f;
bool ep7n_native_current_task(uint32_t anchor,ep7n_task *t)
{
    (void)anchor;f.queries++;
    *t=(ep7n_task){0x101,0,0x1000,0x60dd5067,0x2000,16384};
    if (f.scenario==1) return false;
    if (f.scenario==2) t->domain=1;
    if (f.scenario==3) t->entry++;
    if (f.scenario==9&&f.queries==2) t->tcb++;
    return true;
}
void *ep7_gcc_ui_service(void)
{
    f.gets++;
    if (f.scenario==5) return NULL;
    if (f.scenario==8&&f.gets==2) return other;
    return service;
}
uint16_t ep7_gcc_ui_context_exchange(void *p,uint16_t packed)
{
    uint8_t *s=p;uint16_t prior=(uint16_t)(s[28]|((uint16_t)s[29]<<8));
    assert(p==service&&packed==0x0403);f.exchanges++;
    s[28]=(uint8_t)packed;s[29]=(uint8_t)(packed>>8);return prior;
}
void ep7_gcc_ui_context_select(void *p,uint16_t packed)
{
    assert(p==service&&packed==0xfe81&&f.destroys==1);f.selects++;
    service[28]=(uint8_t)packed;service[29]=(uint8_t)(packed>>8);
}
static int admit(void *ctx,const void *p,size_t bytes)
{
    assert(ctx==&f&&bytes==180);f.admissions++;
    if (f.scenario==4) return 0; /* Deliberately invalid p cannot be read. */
    assert(p==child);return 1;
}
void ep7_gcc_text_cleanup_destroy_unresolved(void *p)
{
    assert(p==child&&service[28]==3&&service[29]==4);f.destroys++;
    memset(child,0xa5,sizeof child); /* C must restore without reading child. */
}
int main(void)
{
    for (int scenario=0;scenario<12;scenario++) {
        memset(&f,0,sizeof f);memset(child,0,sizeof child);memset(service,0,sizeof service);
        f.scenario=scenario;
        child[0]=0x7c;child[1]=0xec;child[2]=0xfa;child[3]=0x60;
        child[4]=0x10;child[5]=0x80;child[28]=3;child[29]=4;
        service[0]=0xb4;service[1]=0xaa;service[2]=0xfa;service[3]=0x60;
        service[4]=service[5]=1;service[28]=0x81;service[29]=0xfe;
        if (scenario==6) service[0]++;
        if (scenario==7) service[5]++;
        if (scenario==10) child[20]=1;
        if (scenario==11) child[88]=1;
        void *p=scenario==4?(void *)(uintptr_t)1:child;
        assert(ep7_text_rollback_native(p,admit,&f)==(scenario==0));
        assert(service[28]==0x81&&service[29]==0xfe);
        assert(f.exchanges==(scenario==0)&&f.selects==(scenario==0)&&f.destroys==(scenario==0));
        if (scenario>=1&&scenario<=3) assert(!f.admissions&&!f.gets);
        if (scenario==4) assert(!f.gets);
    }
    assert(!ep7_text_rollback_native(child,NULL,&f));
    assert(!ep7_text_rollback_native(NULL,admit,&f));
    return 0;
}
