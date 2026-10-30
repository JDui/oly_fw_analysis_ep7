#include "ep7p_direct.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef struct { bool held,fail; unsigned queries; } host;
static bool lock(void *v) { host *h=v; if(h->held || h->fail)return false; h->held=true;return true; }
static void unlock(void *v) { host *h=v; assert(h->held);h->held=false; }
static int no_task(void *v,ep7p_task *t) { host *h=v;(void)t;++h->queries;return -25; }
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

int main(void) {
 host h={0}; ep7p core; ep7p_snapshot s={0,{0}}; uint64_t token,old;
 unsigned char *b=calloc(1,EP7P_EXTENT),out[EP7P_OUTPUT],before[EP7P_OUTPUT];
 uint32_t wire=(uint32_t)(uintptr_t)b; uintptr_t request=(uintptr_t)b+11364;
 unsigned slot,k;
 assert(b && wire && wire<=UINT32_MAX-EP7P_EXTENT);
 assert(ep7p_init(&core,(ep7p_ops){&h,lock,unlock,no_task}));
 s.hl[0]=1;assert(ep7p_register_job(&core,b,EP7P_EXTENT,&s,&token));
 for(slot=0;slot<16;slot++) {
  fixture(b,wire,slot);memset(out,0x5a,sizeof(out));
  assert(ep7p_direct_apply(&core,request,out,sizeof(out)));
  assert(out[706]==0x18 && out[707]==0xfc);
  for(k=0;k<sizeof(out);k++)if(k!=706 && k!=707)assert(out[k]==0x5a);
 }
 memset(out,0x5a,sizeof(out));memcpy(before,out,sizeof(out));
 assert(!ep7p_direct_apply(&core,1,out,sizeof(out))); /* unmapped integer */
 assert(!ep7p_direct_apply(&core,request+4,out,sizeof(out)));
 assert(!ep7p_direct_apply(&core,request,out,sizeof(out)-1));
 assert(!ep7p_direct_apply(&core,request,b,EP7P_OUTPUT));
 assert(!ep7p_direct_apply(&core,request,(unsigned char *)&core,EP7P_OUTPUT));
 assert(!ep7p_direct_apply(&core,request,(unsigned char *)(UINTPTR_MAX-10),EP7P_OUTPUT));
 h.fail=true;assert(!ep7p_direct_apply(&core,request,out,sizeof(out)));h.fail=false;
#define BAD32(offset,value) do { fixture(b,wire,0);put32(b+(offset),(value));assert(!ep7p_direct_apply(&core,request,out,sizeof(out))); } while(0)
 BAD32(11364,0);BAD32(11368,wire+14576+52);BAD32(11368,wire+14576+16*56);
 BAD32(14576,wire+4);BAD32(14584,wire+11368);BAD32(10984+24,0);BAD32(10984+28,1);BAD32(11364+1524,1);
#define BAD16(offset,value) do { fixture(b,wire,0);put16(b+(offset),(value));assert(!ep7p_direct_apply(&core,request,out,sizeof(out))); } while(0)
 BAD16(11312,1);BAD16(11314,2);BAD16(11314,17);BAD16(11364+12,0xf00d);BAD16(11364+10,12);
 fixture(b,wire,0);b[11364+16]=3;assert(!ep7p_direct_apply(&core,request,out,sizeof(out)));
 fixture(b,wire,0);b[11364+29]=0;assert(!ep7p_direct_apply(&core,request,out,sizeof(out)));
 fixture(b,wire,0);b[EP7P_STOCK]=8;assert(!ep7p_direct_apply(&core,request,out,sizeof(out)));
 assert(!memcmp(out,before,sizeof(out)));
 old=token;assert(ep7p_release_job(&core,token));
 assert(!ep7p_direct_apply(&core,request,out,sizeof(out)));
 /* Address reuse: stale TOKEN is rejected, but a naked old REQUEST cannot be
    distinguished from the newly live invocation. This is the explicit ABA
    exclusion precondition, not a hidden claim of generation detection. */
 s.hl[0]=0;assert(ep7p_register_job(&core,b,EP7P_EXTENT,&s,&token));fixture(b,wire,0);
 assert(token!=old && !ep7p_release_job(&core,old));
 assert(ep7p_direct_apply(&core,request,out,sizeof(out)));assert(!memcmp(out,before,sizeof(out)));
 assert(ep7p_release_job(&core,token));free(b);
 assert(!ep7p_direct_apply(&core,request,out,sizeof(out))); /* no dereference after free */
 assert(h.queries==0 && !h.held);
 puts("direct observer: 16 slots, negative gates, neutral/reuse/ABA boundaries passed; zero task queries");return 0;
}
