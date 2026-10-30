#include "ep7_sem_provider.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {uint16_t tid;int tid_status,wait_status,signal_status;unsigned waits,signals;ep7p_ops *reenter;bool nested;} mock;
static int tid(void *v,uint16_t *out){mock*m=v;if(!m->tid_status)*out=m->tid;return m->tid_status;}
static int waitpoll(void*v,uint16_t h){mock*m=v;assert(h==0x1001);m->waits++;return m->wait_status;}
static int signal(void*v,uint16_t h){mock*m=v;assert(h==0x1001);m->signals++;if(m->reenter)m->nested=m->reenter->lock(m->reenter->ctx);return m->signal_status;}
static void setup(ep7s_provider*p,mock*m,ep7p_ops*o){ep7s_native n={m,tid,waitpoll,signal};memset(m,0,sizeof *m);m->tid=0x1002;assert(ep7s_init(p,n,0x1001));*o=ep7s_ops(p);}
int main(void){ep7s_provider p;mock m;ep7p_ops o;ep7p runtime;int8_t values[24]={0};bool changed=false;
 setup(&p,&m,&o);assert(ep7p_init(&runtime,o));values[0]=2;assert(ep7p_edit(&runtime,0,values));assert(m.waits==1&&m.signals==1&&!ep7s_poisoned(&p));
 m.tid=0x2002;assert(!ep7p_edit(&runtime,0,values));assert(m.waits==1);m.tid=0x1002;m.tid_status=-25;assert(!o.lock(o.ctx));assert(m.waits==1);
 setup(&p,&m,&o);m.wait_status=-50;assert(!o.lock(o.ctx));assert(!ep7s_poisoned(&p));m.wait_status=0;assert(o.lock(o.ctx));assert(!o.lock(o.ctx));o.unlock(o.ctx);
 setup(&p,&m,&o);m.wait_status=255;assert(!o.lock(o.ctx));assert(ep7s_poisoned(&p));m.wait_status=0;assert(!o.lock(o.ctx));assert(m.waits==1);
 setup(&p,&m,&o);assert(o.lock(o.ctx));m.signal_status=-43;m.reenter=&o;o.unlock(o.ctx);assert(!m.nested&&ep7s_poisoned(&p));assert(!o.lock(o.ctx));assert(m.waits==1&&m.signals==1);
 setup(&p,&m,&o);assert(o.lock(o.ctx));m.tid=0x1003;o.unlock(o.ctx);assert(ep7s_poisoned(&p)&&m.signals==0);
 setup(&p,&m,&o);assert(o.lock(o.ctx));m.reenter=&o;o.unlock(o.ctx);assert(!m.nested&&!ep7s_poisoned(&p));assert(o.lock(o.ctx));o.unlock(o.ctx);
 setup(&p,&m,&o);assert(ep7p_init(&runtime,o));m.signal_status=-43;
 /* Existing void-unlock core reports commit despite release failure. This is
    intentionally an exposed limitation, NOT a passing safe-completion claim. */
 assert(ep7p_axis_adjust_result(&runtime,0,0,0,1,false,&changed));assert(changed&&ep7s_poisoned(&p));assert(!ep7p_axis_adjust(&runtime,0,0,0,1,false));
 puts("provider: actual core callbacks, domain decline, contention, poison, reentry and void-unlock limitation passed");return 0;}
