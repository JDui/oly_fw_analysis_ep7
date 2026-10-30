#include "ep7p.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { bool held, fail_lock; int status; ep7p_task who; } mock;
static bool lock(void *v) { mock *m=v; assert(!m->held); if(m->fail_lock) return false; m->held=true; return true; }
static void unlock(void *v) { mock *m=v; assert(m->held); m->held=false; }
static int current(void *v,ep7p_task *t) { mock *m=v; assert(m->held); if(!m->status) *t=m->who; return m->status; }
static ep7p_observation observe(void *base,unsigned slot,unsigned selector) {
    uintptr_t b=(uintptr_t)base; ep7p_observation o={0};
    o.job=b; o.request=b+11364; o.operation=b+14576+56*slot;
    o.request_operation=o.operation; o.operation_job=b; o.operation_request=o.request;
    o.callback=0x60355fd4u; o.stage=2; o.stage_callback=0x6036884du;
    o.raw_mode=11; o.raw_selector=selector; return o;
}
static unsigned read16(const unsigned char *p) { return p[0]+256u*p[1]; }
static void lifetime_edges(void) {
 ep7p p; mock m={false,false,0,{7,1}}; ep7p_ops ops={&m,lock,unlock,current};
 unsigned char *a=calloc(1,EP7P_EXTENT),*b=calloc(1,EP7P_EXTENT),out[EP7P_OUTPUT];
 ep7p_snapshot s; uint64_t ja,jb,ha,hb,hc,untouched=42; ep7p_observation oa,ob;
 assert(a&&b); assert(ep7p_init(&p,ops)); assert(ep7p_capture(&p,11,1,&s));
 assert(ep7p_register_job(&p,a,EP7P_EXTENT,&s,&ja)); assert(ep7p_register_job(&p,b,EP7P_EXTENT,&s,&jb));
 assert(ep7p_register_task(&p,m.who)); oa=observe(a,0,1); ob=observe(b,0,1);
 assert(ep7p_enter(&p,ja,&oa,&ha)); assert(ep7p_enter(&p,jb,&ob,&hb)); assert(ep7p_enter(&p,ja,&oa,&hc));
 assert(ep7p_release_job(&p,jb)); /* removes middle frame + descendants, leaves earlier A */
 assert(!ep7p_apply(&p,hc,ja,&oa,out,sizeof(out))); assert(ep7p_apply(&p,ha,ja,&oa,out,sizeof(out)));
 p.serial=UINT64_MAX; /* explicit test injection only */
 assert(!ep7p_enter(&p,ja,&oa,&untouched)); assert(untouched==42);
 assert(!ep7p_register_job(&p,b,EP7P_EXTENT,&s,&untouched)); assert(untouched==42);
 assert(ep7p_apply(&p,ha,ja,&oa,out,sizeof(out))); assert(ep7p_release_job(&p,ja));
 assert(!ep7p_apply(&p,ha,ja,&oa,out,sizeof(out))); assert(!m.held);
 free(a);free(b);puts("independent exhaustion and cross-job unwind checks passed");
}

int main(void) {
    ep7p p; mock m={false,false,0,{7,1}}; ep7p_ops ops={&m,lock,unlock,current};
    unsigned char *b=malloc(EP7P_EXTENT), output[EP7P_OUTPUT], before[EP7P_OUTPUT];
    ep7p_snapshot s, neutral; ep7p_observation o,bad; int8_t hl[24]={0};
    uint64_t j,h,inner,old,frames[EP7P_DEPTH], jobs[EP7P_CAP]; unsigned i,k;
    void *blocks[EP7P_CAP];
    lifetime_edges();
    assert(b); memset(b,0x5a,EP7P_EXTENT);
    assert(!ep7p_init(&p,(ep7p_ops){0})); assert(ep7p_init(&p,ops));
    assert(ep7p_capture(&p,11,1,&neutral));
    for(i=0;i<24;i++) assert(neutral.hl[i]==0);
    assert(!ep7p_capture(&p,11,0,&s)); assert(!ep7p_capture(&p,12,1,&s));
    hl[0]=1; hl[2]=-7; hl[12]=7;
    assert(ep7p_edit(&p,3,hl)); assert(ep7p_capture(&p,11,4,&s));
    hl[0]=7; assert(ep7p_edit(&p,3,hl)); assert(s.hl[0]==1); /* immutable capture copy */
    hl[0]=8; assert(!ep7p_edit(&p,3,hl)); assert(!ep7p_edit(&p,4,hl));
    assert(!ep7p_register_job(&p,NULL,EP7P_EXTENT,&s,&j));
    assert(!ep7p_register_job(&p,b,EP7P_STOCK,&s,&j));
    assert(!ep7p_register_job(&p,&p,EP7P_EXTENT,&s,&j));
    for(i=0;i<EP7P_EXTENT;i++) assert(b[i]==0x5a);
    assert(ep7p_register_job(&p,b,EP7P_EXTENT,&s,&j));
    for(i=0;i<EP7P_STOCK;i++) assert(b[i]==0x5a);
    assert(!ep7p_register_job(&p,b,EP7P_EXTENT,&s,&old));
    assert(!ep7p_register_task(&p,(ep7p_task){7,0}));
    assert(ep7p_register_task(&p,m.who)); assert(!ep7p_register_task(&p,m.who));
    o=observe(b,0,4); assert(ep7p_enter(&p,j,&o,&h));
    assert(sizeof(p)>=EP7P_OUTPUT);
    assert(!ep7p_apply(&p,h,j,&o,(unsigned char *)&p,sizeof(p)));
    memset(output,0x6c,sizeof(output)); memcpy(before,output,sizeof(output));
    assert(ep7p_apply(&p,h,j,&o,output,sizeof(output)));
    assert(read16(output+706)==(uint16_t)-1000); assert(read16(output+710)==300);
    assert(read16(output+730)==7000);
    for(i=0;i<sizeof(output);i++) {
        bool changed=(i==706 || i==707 || i==710 || i==711 || i==730 || i==731);
        if(!changed) assert(output[i]==before[i]);
    }
    /* Native S and every unrelated byte survive; output owns scalars, not pointers. */
    assert(!ep7p_apply(&p,h,j,&o,b,EP7P_OUTPUT));
    assert(!ep7p_apply(&p,h,j,&o,output,EP7P_OUTPUT-1));
    assert(ep7p_enter(&p,j,&o,&inner)); assert(!ep7p_apply(&p,h,j,&o,output,sizeof(output)));
    assert(ep7p_unwind(&p,h)); assert(!ep7p_apply(&p,inner,j,&o,output,sizeof(output)));
    for(i=0;i<16;i++) { o=observe(b,i,4); assert(ep7p_enter(&p,j,&o,&h)); assert(ep7p_apply(&p,h,j,&o,output,sizeof(output))); assert(ep7p_unwind(&p,h)); }
    o=observe(b,0,4); assert(ep7p_enter(&p,j,&o,&h));
    assert(sizeof(p)>=EP7P_OUTPUT);
    assert(!ep7p_apply(&p,h,j,&o,(unsigned char *)&p,sizeof(p)));
#define BAD(field,value) do { bad=o; bad.field=(value); assert(!ep7p_apply(&p,h,j,&bad,output,sizeof(output))); assert(!ep7p_enter(&p,j,&bad,&inner)); } while(0)
    BAD(stage,1); BAD(stage_callback,0); BAD(type,3); BAD(raw_mode,12); BAD(raw_selector,3);
    BAD(owner,1); BAD(mutation_callback,1); BAD(callback,0); BAD(request,o.request+4);
    BAD(operation,o.job+14576+16*56); BAD(request_operation,0); BAD(operation_job,0); BAD(operation_request,0);
#undef BAD
    m.status=-25; assert(!ep7p_apply(&p,h,j,&o,output,sizeof(output))); m.status=0;
    m.who.epoch=2; assert(!ep7p_apply(&p,h,j,&o,output,sizeof(output))); m.who.epoch=1;
    assert(ep7p_release_task(&p,m.who)); m.who.epoch=2; assert(ep7p_register_task(&p,m.who));
    assert(!ep7p_apply(&p,h,j,&o,output,sizeof(output)));
    for(i=0;i<EP7P_DEPTH;i++) assert(ep7p_enter(&p,j,&o,&frames[i]));
    assert(!ep7p_enter(&p,j,&o,&h)); assert(ep7p_unwind(&p,frames[0]));
    assert(ep7p_enter(&p,j,&o,&h)); old=j; assert(ep7p_release_job(&p,j));
    assert(!ep7p_apply(&p,h,old,&o,output,sizeof(output)));
    assert(ep7p_register_job(&p,b,EP7P_EXTENT,&neutral,&j)); assert(j!=old);
    o=observe(b,0,1); assert(!ep7p_apply(&p,h,j,&o,output,sizeof(output)));
    assert(ep7p_enter(&p,j,&o,&h)); memcpy(before,output,sizeof(output));
    assert(ep7p_apply(&p,h,j,&o,output,sizeof(output))); assert(!memcmp(before,output,sizeof(output)));
    assert(ep7p_release_job(&p,j)); free(b); /* output remains valid after release */
    assert(!memcmp(before,output,sizeof(output)));
    for(i=0;i<EP7P_CAP;i++) { blocks[i]=malloc(EP7P_EXTENT); assert(blocks[i]); assert(ep7p_register_job(&p,blocks[i],EP7P_EXTENT,&neutral,&jobs[i])); }
    b=malloc(EP7P_EXTENT); assert(b); assert(!ep7p_register_job(&p,b,EP7P_EXTENT,&neutral,&j)); free(b);
    for(i=0;i<EP7P_CAP;i++) { assert(ep7p_release_job(&p,jobs[i])); free(blocks[i]); }
    for(i=0;i<EP7P_CAP-1;i++) { m.who.tid=(uint16_t)(20+i); m.who.epoch=1; assert(ep7p_register_task(&p,m.who)); }
    m.who.tid=100; assert(!ep7p_register_task(&p,m.who));
    m.fail_lock=true; assert(!ep7p_edit(&p,0,hl)); m.fail_lock=false;
    for(k=0;k<4;k++) { assert(ep7p_capture(&p,11,k+1,&s)); assert(s.profile==k); }
    assert(ep7p_axis_adjust(&p,1,0,255,INT_MAX,false));
    { int8_t axis[12]; assert(ep7p_axis_read(&p,1,0,axis)); for(i=0;i<12;i++) assert(axis[i]==7); }
    assert(ep7p_axis_adjust(&p,1,0,0,INT_MIN,false));
    assert(ep7p_axis_adjust(&p,1,1,255,2,false));
    assert(ep7p_axis_adjust(&p,1,0,255,0,true));
    { int8_t axis[12]; assert(ep7p_axis_read(&p,1,0,axis)); for(i=0;i<12;i++) assert(axis[i]==0); }
    assert(!ep7p_axis_adjust(&p,1,0,12,1,false));
    /* Exhaustion cannot wrap a stale token back into validity. */
    p.serial=UINT64_MAX; b=malloc(EP7P_EXTENT); assert(b);
    assert(!ep7p_register_job(&p,b,EP7P_EXTENT,&neutral,&j)); free(b);
    assert(!m.held); puts("portable integration: all assertions passed (host only)"); return 0;
}
