#define _POSIX_C_SOURCE 200809L
#include "ep7p_direct.h"
#include <assert.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define JOBS_PER_WORKER 2000u
#define EDITS 12000u
/* Host-only synchronization adapter, NOT a native semaphore binding. */
typedef struct {
    pthread_mutex_t mutex;
    pthread_barrier_t start;
    atomic_uint queries, applications, edits;
    ep7p core;
} state;
typedef struct { state *s; unsigned index; } worker;
static bool lock(void *v) { return pthread_mutex_lock(&((state *)v)->mutex)==0; }
static void unlock(void *v) { assert(pthread_mutex_unlock(&((state *)v)->mutex)==0); }
static int no_task(void *v,ep7p_task *t) {
    (void)t; atomic_fetch_add(&((state *)v)->queries,1); return -25;
}
static void barrier(state *s) {
    int r=pthread_barrier_wait(&s->start);assert(r==0 || r==PTHREAD_BARRIER_SERIAL_THREAD);
}
static void p16(unsigned char *p,unsigned v) {p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);}
static void p32(unsigned char *p,uint32_t v) {unsigned k;for(k=0;k<4;k++)p[k]=(unsigned char)(v>>(8*k));}
static void fixture(unsigned char *b,unsigned slot) {
    uint32_t wire=(uint32_t)(uintptr_t)b;
    unsigned char *r=b+11364,*op=b+14576+56*slot;
    assert(wire && wire<=UINT32_MAX-EP7P_EXTENT);
    memset(b,0,EP7P_EXTENT);
    p16(b+11312,2);p16(b+11314,3);p32(b+10984+24,0x6036884d);
    p32(r,0x60355fd4);p32(r+4,wire+14576+56*slot);
    p16(r+10,11);r[29]=1;p32(op,wire);p32(op+8,wire+11364);
}
static void expected_output(unsigned char *out,const ep7p_snapshot *snapshot) {
    /* Comparative numerical fixtures, not E-P7 image calibration.
       LUT attribution: fishcu/oly_fw_analysis PEN-F image_parameters.s:101-104;
       see the parent prototype README rights/provenance notice. */
    static const int lum[15]={-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300};
    unsigned j;
    memset(out,0x5a,EP7P_OUTPUT);
    for(j=0;j<12;j++) {
        unsigned bin=2*(j%6)+j/6;
        int h=snapshot->hl[bin],l=snapshot->hl[12+bin];
        if(h)p16(out+706+24*j,(uint16_t)(-1000*h));
        if(l)p16(out+710+24*j,(uint16_t)lum[l+7]);
    }
}
static void *writer(void *v) {
    state *s=v; unsigned n,k;int8_t values[24];barrier(s);
    for(n=0;n<EDITS;n++) {
        for(k=0;k<24;k++)values[k]=(int8_t)((int)((n+k)%15)-7);
        assert(ep7p_edit(&s->core,n%4,values));atomic_fetch_add(&s->edits,1);
        if(n%8==0)sched_yield();
    }
    return NULL;
}
static void *reader(void *v) {
    worker *w=v;state *s=w->s;unsigned n,k;barrier(s);
    for(n=0;n<JOBS_PER_WORKER;n++) {
        ep7p_snapshot captured;uint64_t token;unsigned profile=(n+w->index)%4;
        unsigned char *allocation=malloc(EP7P_EXTENT+64u),*b,out[EP7P_OUTPUT],expected[EP7P_OUTPUT];
        assert(allocation);b=allocation+64; /* TSan allocator may give low32==0. */
        fixture(b,n%16);
        assert(ep7p_capture(&s->core,11,profile+1,&captured));assert(captured.profile==profile);
        /* Each snapshot is either boot-neutral or a whole atomic settings edit,
           never a torn combination of two writes. */
        { bool neutral=true;
          for(k=0;k<24;k++)if(captured.hl[k])neutral=false;
          if(!neutral)for(k=0;k<24;k++)assert(captured.hl[k]==(int8_t)((captured.hl[0]+7+(int)k)%15-7)); }
        assert(ep7p_register_job(&s->core,b,EP7P_EXTENT,&captured,&token));
        sched_yield(); /* Encourage an intervening settings edit/other job. */
        expected_output(expected,&captured);memset(out,0x5a,sizeof(out));
        assert(ep7p_direct_apply(&s->core,(uintptr_t)b+11364,out,sizeof(out)));
        assert(memcmp(out,expected,sizeof(out))==0); /* Includes all S/canary bytes. */
        assert(ep7p_release_job(&s->core,token));free(allocation);
        atomic_fetch_add(&s->applications,1);
    }
    return NULL;
}
int main(void) {
    state s;pthread_t threads[3];worker workers[2];unsigned k;
    memset(&s,0,sizeof(s));atomic_init(&s.queries,0);atomic_init(&s.applications,0);atomic_init(&s.edits,0);
    assert(pthread_mutex_init(&s.mutex,NULL)==0);assert(pthread_barrier_init(&s.start,NULL,3)==0);
    assert(ep7p_init(&s.core,(ep7p_ops){&s,lock,unlock,no_task}));
    assert(pthread_create(&threads[0],NULL,writer,&s)==0);
    for(k=0;k<2;k++){workers[k]=(worker){&s,k};assert(pthread_create(&threads[k+1],NULL,reader,&workers[k])==0);}
    for(k=0;k<3;k++)assert(pthread_join(threads[k],NULL)==0);
    assert(atomic_load(&s.queries)==0);assert(atomic_load(&s.applications)==2*JOBS_PER_WORKER);assert(atomic_load(&s.edits)==EDITS);
    for(k=0;k<EP7P_CAP;k++)assert(!s.core.jobs[k].token);
    assert(pthread_barrier_destroy(&s.start)==0);assert(pthread_mutex_destroy(&s.mutex)==0);
    puts("pthread integration: 12000 settings edits, 4000 capture/job/direct-read/revoke/free cycles, 2 job workers, zero task queries");
    return 0;
}
