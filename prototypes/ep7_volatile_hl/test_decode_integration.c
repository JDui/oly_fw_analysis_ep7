#include "ep7p_decode.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef struct { bool held; } host;
static bool lock(void *v) { host *h=v; if(h->held) return false; h->held=true; return true; }
static void unlock(void *v) { host *h=v; assert(h->held); h->held=false; }
static int task(void *v,ep7p_task *t) { (void)v; *t=(ep7p_task){3,1}; return 0; }
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
    const uint32_t wire=0x62000000; unsigned slot; host h={false}; ep7p core;
    unsigned char *b=calloc(1,EP7P_EXTENT),out[EP7P_OUTPUT],before[EP7P_OUTPUT];
    ep7p_snapshot snapshot; ep7p_observation observation; uint64_t job,scope; int8_t values[24]={0};
    assert(b && ep7p_init(&core,(ep7p_ops){&h,lock,unlock,task}));
    values[0]=1; assert(ep7p_edit(&core,0,values)); assert(ep7p_capture(&core,11,1,&snapshot));
    fixture(b,wire,0);
    assert(!ep7p_decode(NULL,EP7P_STOCK,wire,wire+11364,1,&observation));
    assert(!ep7p_decode(b,EP7P_STOCK-1,wire,wire+11364,1,&observation));
    assert(!ep7p_decode(b,EP7P_STOCK,wire,wire+11368,1,&observation));
    assert(!ep7p_decode(b,EP7P_STOCK,UINT32_MAX-12,0,1,&observation));
    assert(!ep7p_decode(b,EP7P_STOCK,wire,wire+11364,0,&observation));
    /* A stock-size buffer can have matching SHAPE, but cannot be registered. */
    assert(ep7p_decode(b,EP7P_STOCK,wire,wire+11364,1,&observation));
    assert(!ep7p_register_job(&core,b,EP7P_STOCK,&snapshot,&job));
    { /* Real allocation has no trailer: slot 15 must remain in bounds. */
        unsigned char *stock=calloc(1,EP7P_STOCK);
        assert(stock); fixture(stock,wire,15);
        assert(ep7p_decode(stock,EP7P_STOCK,wire,wire+11364,1,&observation));
        stock[11364+29]=2;
        assert(ep7p_decode(stock,EP7P_STOCK,wire,wire+11364,1,&observation));
        assert(!ep7p_register_job(&core,stock,EP7P_STOCK,&snapshot,&job));
        free(stock);
    }
    assert(ep7p_register_job(&core,b,EP7P_EXTENT,&snapshot,&job));
    assert(ep7p_register_task(&core,(ep7p_task){3,1}));
    for(slot=0;slot<16;slot++) {
        fixture(b,wire,slot);
        assert(ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
        assert(ep7p_enter(&core,job,&observation,&scope));
        memset(out,0x71,sizeof out); memcpy(before,out,sizeof out);
        assert(ep7p_apply(&core,scope,job,&observation,out,sizeof out));
        before[706]=0x18; before[707]=0xfc; /* experimental -1000 */
        assert(memcmp(out,before,sizeof out)==0);
        assert(ep7p_unwind(&core,scope));
    }
#define REJECT_U32(offset,value) do { fixture(b,wire,0); put32(b+(offset),(value)); assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation)); } while(0)
    REJECT_U32(11364,0); REJECT_U32(11368,wire+14576+52);
    REJECT_U32(11368,wire+14572); REJECT_U32(11368,wire+14576+16*56); REJECT_U32(14576,wire+4);
    REJECT_U32(14584,wire+11368); REJECT_U32(10984+24,0); REJECT_U32(10984+28,1);
    REJECT_U32(11364+1524,1);
#undef REJECT_U32
    fixture(b,wire,0); b[11364+16]=3; assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); b[11364+29]=0; assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); put16(b+11364+12,0xf00d); assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); put16(b+11314,2); assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); put16(b+11312,16); assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); put16(b+11314,17); assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); b[11364+8]=1; assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); b[11364+9]=1; assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&observation));
    fixture(b,wire,0); put16(b+11364+10,12);
    { ep7p_observation sentinel,unchanged;
      memset(&sentinel,0x5a,sizeof sentinel); memcpy(&unchanged,&sentinel,sizeof sentinel);
      assert(!ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,1,&sentinel));
      assert(memcmp(&sentinel,&unchanged,sizeof sentinel)==0);
    }
    fixture(b,wire,0); assert(ep7p_decode(b,EP7P_EXTENT,wire,wire+11364,2,&observation));
    assert(!ep7p_enter(&core,job,&observation,&scope)); /* Captured selector binding differs. */
    assert(ep7p_release_job(&core,job)); assert(ep7p_release_task(&core,(ep7p_task){3,1})); free(b);
    puts("bounded native-layout bytes -> checked observation -> scoped CPU lanes: PASS (host only)");
    return 0;
}
