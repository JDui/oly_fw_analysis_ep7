#include "ep7p.h"
#include <string.h>

static bool begin(ep7p *p) { return p && p->ready && p->ops.lock(p->ops.ctx); }
static bool end(ep7p *p, bool result) { p->ops.unlock(p->ops.ctx); return result; }
static bool runtime_overlap(ep7p *p, uintptr_t b, size_t len) {
    uintptr_t a=(uintptr_t)p;
    return b<a+sizeof(*p) && a<b+len;
}
static bool same(ep7p_task a, ep7p_task b) { return a.tid==b.tid && a.epoch==b.epoch; }
static bool values(const int8_t *v) {
    unsigned i; if (!v) return false;
    for (i=0;i<24;i++) if (v[i]<-7 || v[i]>7) return false;
    return true;
}
static uint64_t issue(ep7p *p) { return p->serial==UINT64_MAX ? 0 : ++p->serial; }
static ep7p_job *job(ep7p *p,uint64_t token) {
    unsigned i; if (!token) return NULL;
    for(i=0;i<EP7P_CAP;i++) if(p->jobs[i].token==token) return &p->jobs[i];
    return NULL;
}
static ep7p_task_slot *current(ep7p *p) {
    unsigned i; ep7p_task t={0,0};
    if(p->ops.current(p->ops.ctx,&t)!=0 || !t.epoch) return NULL;
    for(i=0;i<EP7P_CAP;i++) if(p->tasks[i].live && same(t,p->tasks[i].who)) return &p->tasks[i];
    return NULL;
}
static bool shape(ep7p_job *j,const ep7p_observation *o) {
    uintptr_t b=(uintptr_t)j->base, offset;
    if(!o || b%4 || b>UINTPTR_MAX-EP7P_EXTENT || o->job!=b ||
       o->request!=b+11364 || o->operation<b+14576) return false;
    offset=o->operation-b-14576;
    return offset%56==0 && offset/56<16 && o->callback==0x60355fd4u &&
        o->request_operation==o->operation && o->operation_job==b &&
        o->operation_request==o->request && o->stage==2 &&
        o->stage_callback==0x6036884du && o->type==0 && o->raw_mode==11 &&
        o->raw_selector==(unsigned)j->profile+1 && o->owner==0 && o->mutation_callback==0;
}
bool ep7p_init(ep7p *p,ep7p_ops ops) {
    if(!p || !ops.lock || !ops.unlock || !ops.current) return false;
    memset(p,0,sizeof(*p)); p->ops=ops; p->ready=true; return true;
}
bool ep7p_edit(ep7p *p,unsigned profile,const int8_t hl[24]) {
    if(!begin(p)) return false;
    if(profile>=4 || !values(hl)) return end(p,false);
    memcpy(p->profiles[profile],hl,24); return end(p,true);
}
bool ep7p_axis_read(ep7p *p,unsigned profile,unsigned axis,int8_t out[12]) {
    if(!begin(p)) return false;
    if(profile>=4 || axis>=2 || !out) return end(p,false);
    memcpy(out,p->profiles[profile]+12*axis,12); return end(p,true);
}
bool ep7p_axis_adjust_result(ep7p *p,unsigned profile,unsigned axis,unsigned sector,int delta,bool reset,bool *changed) {
    unsigned i; int lower=-14,upper=14,step; bool any=false;
    if(!changed || !begin(p)) return false;
    if(profile>=4 || axis>=2 || (sector>=12 && sector!=255)) return end(p,false);
    /* ALL preserves inter-sector differences: one common delta stops when the
       first selected value reaches a limit, rather than clipping each band. */
    for(i=0;i<12;i++) if(sector==255 || sector==i) {
        int v=p->profiles[profile][12*axis+i];
        if(-7-v>lower) lower=-7-v;
        if(7-v<upper) upper=7-v;
    }
    step=delta>upper ? upper : delta<lower ? lower : delta;
    for(i=0;i<12;i++) if(sector==255 || sector==i) {
        int v=p->profiles[profile][12*axis+i];
        v=reset ? 0 : v+step;
        if(v!=p->profiles[profile][12*axis+i]) any=true;
        p->profiles[profile][12*axis+i]=(int8_t)v;
    }
    *changed=any; return end(p,true);
}
bool ep7p_axis_adjust(ep7p *p,unsigned profile,unsigned axis,unsigned sector,int delta,bool reset) {
    bool changed;
    return ep7p_axis_adjust_result(p,profile,axis,sector,delta,reset,&changed);
}
bool ep7p_capture(ep7p *p,unsigned mode,unsigned selector,ep7p_snapshot *s) {
    if(!begin(p)) return false;
    if(!s || mode!=11 || selector<1 || selector>4) return end(p,false);
    s->profile=(uint8_t)(selector-1); memcpy(s->hl,p->profiles[s->profile],24);
    return end(p,true);
}
bool ep7p_register_job(ep7p *p,void *base,size_t extent,const ep7p_snapshot *s,uint64_t *out) {
    unsigned i; ep7p_job *free_slot=NULL; uintptr_t b=(uintptr_t)base;
    if(!begin(p)) return false;
    if(!base || b%4 || extent<EP7P_EXTENT || extent>UINTPTR_MAX-b || runtime_overlap(p,b,extent) ||
       !s || s->profile>=4 || !values(s->hl) || !out) return end(p,false);
    for(i=0;i<EP7P_CAP;i++) {
        ep7p_job *j=&p->jobs[i]; uintptr_t a=(uintptr_t)j->base;
        if(!j->token) { if(!free_slot) free_slot=j; }
        else if(b<a+j->extent && a<b+extent) return end(p,false);
    }
    if(!free_slot || p->serial==UINT64_MAX) return end(p,false);
    /* First actual job access is after independently supplied extent checks. */
    memcpy((unsigned char *)base+EP7P_STOCK,s->hl,24);
    free_slot->base=base; free_slot->extent=extent; free_slot->profile=s->profile; free_slot->token=issue(p);
    *out=free_slot->token; return end(p,true);
}
bool ep7p_release_job(ep7p *p,uint64_t token) {
    unsigned i,k; ep7p_job *j;
    if(!begin(p)) return false;
    j=job(p,token); if(!j) return end(p,false);
    for(i=0;i<EP7P_CAP;i++) for(k=0;k<p->tasks[i].depth;k++)
        if(p->tasks[i].frames[k].job==token) { p->tasks[i].depth=k; break; }
    memset(j,0,sizeof(*j)); return end(p,true);
}
bool ep7p_register_task(ep7p *p,ep7p_task who) {
    unsigned i; ep7p_task actual={0,0}; ep7p_task_slot *slot=NULL;
    if(!begin(p)) return false;
    if(!who.epoch || p->ops.current(p->ops.ctx,&actual)!=0 || !same(actual,who)) return end(p,false);
    for(i=0;i<EP7P_CAP;i++) {
        if(p->tasks[i].live && p->tasks[i].who.tid==who.tid) return end(p,false);
        if(!p->tasks[i].live && !slot) slot=&p->tasks[i];
    }
    if(!slot) return end(p,false);
    memset(slot,0,sizeof(*slot)); slot->live=true; slot->who=who; return end(p,true);
}
bool ep7p_release_task(ep7p *p,ep7p_task who) {
    unsigned i; if(!begin(p)) return false;
    for(i=0;i<EP7P_CAP;i++) if(p->tasks[i].live && same(who,p->tasks[i].who)) {
        memset(&p->tasks[i],0,sizeof(p->tasks[i])); return end(p,true);
    }
    return end(p,false);
}
bool ep7p_enter(ep7p *p,uint64_t token,const ep7p_observation *o,uint64_t *out) {
    ep7p_job *j; ep7p_task_slot *t; ep7p_frame *f;
    if(!begin(p)) return false;
    j=job(p,token); t=current(p);
    if(!j || !t || !out || !shape(j,o) || t->depth>=EP7P_DEPTH || p->serial==UINT64_MAX) return end(p,false);
    f=&t->frames[t->depth++]; f->token=issue(p); f->job=token; f->shape=*o;
    *out=f->token; return end(p,true);
}
bool ep7p_unwind(ep7p *p,uint64_t token) {
    unsigned i; ep7p_task_slot *t;
    if(!begin(p)) return false;
    t=current(p); if(!t || !token) return end(p,false);
    for(i=0;i<t->depth;i++) if(t->frames[i].token==token) { t->depth=i; return end(p,true); }
    return end(p,false);
}
static void put16(unsigned char *p,int value) {
    uint16_t u=(uint16_t)value; p[0]=(unsigned char)u; p[1]=(unsigned char)(u>>8);
}
bool ep7p_apply(ep7p *p,uint64_t scope,uint64_t token,const ep7p_observation *o,unsigned char *out,size_t len) {
    /* Comparative LUTs: fishcu/oly_fw_analysis, patches/hsl/pen-f/src/
       image_parameters/image_parameters.s:101-104 (upstream attribution retained).
       NOT E-P7 pixel calibration. See README attribution/rights boundaries. */
    static const int hue[15]={7000,6000,5000,4000,3000,2000,1000,0,-1000,-2000,-3000,-4000,-5000,-6000,-7000};
    static const int lum[15]={-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300};
    static const unsigned bins[12]={0,2,4,6,8,10,1,3,5,7,9,11};
    ep7p_task_slot *t; ep7p_job *j; ep7p_frame *f; int8_t hl[24]; unsigned k;
    if(!begin(p)) return false;
    t=current(p); j=job(p,token);
    if(!t || !t->depth || !j || !out || len<EP7P_OUTPUT || !shape(j,o)) return end(p,false);
    f=&t->frames[t->depth-1];
    if(f->token!=scope || f->job!=token || f->shape.operation!=o->operation) return end(p,false);
    if(len>UINTPTR_MAX-(uintptr_t)out || runtime_overlap(p,(uintptr_t)out,len)) return end(p,false);
    for(k=0;k<EP7P_CAP;k++) {
        ep7p_job *other=&p->jobs[k]; uintptr_t a=(uintptr_t)other->base, b=(uintptr_t)out;
        if(other->token && b<a+other->extent && a<b+len) return end(p,false);
    }
    /* Synchronous copy only; no extension pointer is returned or retained by output. */
    memcpy(hl,j->base+EP7P_STOCK,24);
    if(!values(hl)) return end(p,false);
    for(k=0;k<12;k++) {
        int h=hl[bins[k]], l=hl[12+bins[k]];
        if(h) put16(out+706+24*k,hue[h+7]);
        if(l) put16(out+710+24*k,lum[l+7]);
    }
    return end(p,true);
}
