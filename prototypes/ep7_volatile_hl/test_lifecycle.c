#include "ep7p_lifecycle.h"
#include "ep7p_ui_raw.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {
 ep7p core; ep7p_ui ui; struct ep7_ui_session session; unsigned queries; unsigned char *allocation; unsigned char output[EP7P_OUTPUT];
 unsigned locks,fail_after,ctors,converts,processes,cleanups;
 int ctor_status,convert_status,process_status;
 bool proven,small,bad_shape,mutate_ui,fail_release,noalloc,extra_reads,wrong_request;
} host;
static bool lock(void *v) { host *h=v; ++h->locks; return !h->fail_after || h->locks<h->fail_after; }
static void unlock(void *v) { (void)v; }
static int current(void *v,ep7p_task *t) { host *h=v;(void)t;++h->queries;return -25; }
static void put16(unsigned char *p,unsigned v) { p[0]=(unsigned char)v; p[1]=(unsigned char)(v>>8); }
static void put32(unsigned char *p,uint32_t v) { unsigned i; for(i=0;i<4;i++) p[i]=(unsigned char)(v>>(8*i)); }
static void fixture(unsigned char *b,uint32_t base,unsigned slot) {
    unsigned char *r=b+11364,*op=b+14576+56*slot;
    put16(b+11312,2); put16(b+11314,3);
    put32(b+10984+24,0x6036884d); put32(b+10984+28,0);
    put32(r,0x60355fd4); put32(r+4,base+14576+56*slot);
    r[8]=0; r[9]=0; put16(r+10,11); put16(r+12,0); r[16]=0; put16(r+28,0x100);
    put32(r+1524,0); put32(op,base); put32(op+8,base+11364);
}
static int construct(void *v,void *descriptor,ep7l_allocation *a) {
 host *h=v; assert(descriptor==h); ++h->ctors;
 if(h->noalloc)return -90;
 h->allocation=malloc(h->small?EP7P_STOCK:EP7P_EXTENT); assert(h->allocation);
 memset(h->allocation,0xa5,h->small?EP7P_STOCK:EP7P_EXTENT);
 a->base=h->allocation; a->extent=h->small?EP7P_STOCK:EP7P_EXTENT; a->fresh_extent_proven=h->proven;
 return h->ctor_status;
}
static int convert(void *v,void *descriptor) {
 host *h=v; assert(descriptor==h); ++h->converts; fixture(h->allocation,(uint32_t)(uintptr_t)h->allocation,0); return h->convert_status;
}
static int process(void *v,void *descriptor,ep7l_reader reader,void *ctx) {
 host *h=v; uintptr_t request=(uintptr_t)h->allocation+11364;
 unsigned j; assert(descriptor==h); ++h->processes;
 /* Converter initialized native-layout bytes; reader sees actual buffer. */
 if(h->bad_shape)h->allocation[11364+16]=3;
 if(h->mutate_ui) {
  const struct ep7p_ui_raw_event event={0x9032,-8};
  assert(ep7p_ui_raw_dispatch(&h->ui,h->session,&event)==EP7_UI_CHANGED);
 }
 memset(h->output,0x5a,sizeof(h->output));
 (void)reader(ctx,request+(h->wrong_request?4u:0u),h->output,sizeof(h->output));
 if(h->extra_reads)for(j=0;j<16;j++)(void)reader(ctx,request,h->output,sizeof(h->output));
 if(h->fail_release)h->fail_after=h->locks+1;
 return h->process_status;
}
static void cleanup(void *v,void *descriptor) {
 host *h=v; unsigned j; assert(descriptor==h);
 for(j=0;j<EP7P_CAP;j++)assert(!h->core.jobs[j].token);
 assert(h->queries==0);++h->cleanups;free(h->allocation);h->allocation=NULL;
}
static void init(host *h) {
 ep7p_ops o; memset(h,0,sizeof(*h));h->proven=true;
 o.ctx=h;o.lock=lock;o.unlock=unlock;o.current=current;
 assert(ep7p_init(&h->core,o));
 ep7p_ui_init(&h->ui,&h->core);h->session=(struct ep7_ui_session){1,0};
 assert(ep7p_ui_ops.open(&h->ui,h->session,54,4)==EP7_UI_CHANGED);
}
static ep7l_result run(host *h,const ep7p_snapshot *s) {
 ep7l_ops o={h,construct,convert,process,cleanup}; return ep7l_run(&h->core,&o,h,s);
}
int main(void) {
 host h; ep7l_result r; ep7p_snapshot snapshot={0,{0}}; unsigned k;
 init(&h);
 { const struct ep7p_ui_raw_event event={0x9032,1};
 assert(ep7p_ui_raw_dispatch(&h.ui,h.session,&event)==EP7_UI_CHANGED);
 assert(ep7p_capture(&h.core,11,1,&snapshot)); }
 h.mutate_ui=true;h.process_status=-123;r=run(&h,&snapshot);
 assert(r.native_status==-123 && r.applied==1 && r.cleaned && h.cleanups==1);
 /* +1 experimental H is -1000 = 0xfc18, captured BEFORE replacement UI -7. */
 assert(h.output[706]==0x18 && h.output[707]==0xfc);
 for(k=0;k<sizeof(h.output);k++)if(k!=706 && k!=707)assert(h.output[k]==0x5a);
 init(&h);h.ctor_status=31;r=run(&h,&snapshot);assert(r.native_status==31 && !h.converts && !h.processes && r.cleaned);
 init(&h);h.convert_status=-32;r=run(&h,&snapshot);assert(r.native_status==-32 && h.converts==1 && !h.processes && r.cleaned);
 init(&h);h.small=true;r=run(&h,&snapshot);assert(!r.registered && !r.applied && h.processes==1 && r.cleaned);
 init(&h);h.proven=false;r=run(&h,&snapshot);assert(!r.registered && !r.applied && r.cleaned);
 init(&h);r=run(&h,NULL);assert(!r.registered && !r.applied && r.cleaned);
 init(&h);h.bad_shape=true;r=run(&h,&snapshot);assert(r.registered && !r.applied && r.cleaned);
 for(k=0;k<sizeof(h.output);k++)assert(h.output[k]==0x5a);
 init(&h);h.fail_release=true;h.process_status=77;r=run(&h,&snapshot);
 assert(r.native_status==77 && r.applied==1 && r.quarantined && !r.cleaned && !h.cleanups && h.allocation);
 { ep7l_ops o={&h,construct,convert,process,cleanup};
   assert(!ep7l_retry_cleanup(&h.core,&o,&h,&r));
   assert(r.native_status==77 && r.quarantined && !r.cleaned && !h.cleanups);h.fail_after=0;
   assert(ep7l_retry_cleanup(&h.core,&o,&h,&r));assert(r.cleaned && !r.quarantined && !r.pending_job);
   assert(!ep7l_retry_cleanup(&h.core,&o,&h,&r)); }
 init(&h);h.core.serial=UINT64_MAX;r=run(&h,&snapshot);assert(!r.registered && !r.applied && r.cleaned);
 init(&h);h.noalloc=true;r=run(&h,&snapshot);assert(r.native_status==-90 && r.cleaned && !r.registered);
 init(&h);h.fail_after=1;r=run(&h,&snapshot);assert(!r.registered && !r.applied && r.cleaned);
 init(&h);h.wrong_request=true;r=run(&h,&snapshot);assert(r.registered && !r.applied && r.cleaned);
 for(k=0;k<sizeof(h.output);k++)assert(h.output[k]==0x5a);
 init(&h);h.extra_reads=true;r=run(&h,&snapshot);assert(r.readers==16 && r.applied==16 && r.cleaned);
 puts("raw UI -> immutable capture -> direct lifecycle: 13 scenarios passed; zero task queries");return 0;
}
