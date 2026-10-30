#include "ep7_sem_provider.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct{uint16_t tid;int tid_status,wait_status,signal_status;unsigned waits,signals;bool held,nested;ep7p_ops *on_release;ep7s_provider *poison_during_wait;}mock;
static int tid(void*v,uint16_t*out){mock*m=v;if(!m->tid_status)*out=m->tid;return m->tid_status;}
static int poll(void*v,uint16_t h){mock*m=v;assert(h==0x1001);m->waits++;if(m->wait_status)return m->wait_status;if(m->held)return -50;m->held=true;if(m->poison_during_wait)atomic_store(&m->poison_during_wait->poison,true);return 0;}
static int signal(void*v,uint16_t h){mock*m=v;ep7p_ops*o=m->on_release;assert(h==0x1001);m->signals++;if(m->signal_status)return m->signal_status;assert(m->held);m->held=false;if(o){m->on_release=NULL;m->tid=0x1003;m->nested=o->lock(o->ctx);}return 0;}
static void setup(ep7s_provider*p,mock*m,ep7p_ops*o){ep7s_native n={m,tid,poll,signal};memset(m,0,sizeof *m);m->tid=0x1002;assert(ep7s_init(p,n,0x1001));*o=ep7s_ops(p);}
int main(void){ep7s_provider p;mock m;ep7p_ops o;ep7p runtime;int8_t values[24]={0};bool changed=false;
 setup(&p,&m,&o);assert(ep7p_init(&runtime,o));values[0]=2;assert(ep7p_edit(&runtime,0,values));assert(m.waits==1&&m.signals==1&&!m.held);
 m.tid=0x2002;assert(!ep7p_edit(&runtime,0,values));assert(m.waits==1);m.tid=0x1002;m.tid_status=-25;assert(!o.lock(o.ctx));assert(m.waits==1);
 setup(&p,&m,&o);assert(o.lock(o.ctx));assert(!o.lock(o.ctx));assert(!ep7s_poisoned(&p));o.unlock(o.ctx);assert(o.lock(o.ctx));o.unlock(o.ctx);
 setup(&p,&m,&o);m.wait_status=255;assert(!o.lock(o.ctx));assert(ep7s_poisoned(&p));m.wait_status=0;assert(!o.lock(o.ctx));assert(m.waits==1);
 setup(&p,&m,&o);assert(o.lock(o.ctx));m.signal_status=-25;o.unlock(o.ctx);assert(m.held&&ep7s_poisoned(&p));assert(!o.lock(o.ctx));assert(m.waits==1);
 setup(&p,&m,&o);assert(o.lock(o.ctx));m.tid=0x1003;o.unlock(o.ctx);assert(m.held&&ep7s_poisoned(&p)&&m.signals==0);
 setup(&p,&m,&o);assert(o.lock(o.ctx));m.on_release=&o;o.unlock(o.ctx);assert(m.nested&&m.held&&!ep7s_poisoned(&p));assert(atomic_load(&p.owner)==0x1003);o.unlock(o.ctx);assert(!m.held);
 setup(&p,&m,&o);m.poison_during_wait=&p;assert(!o.lock(o.ctx));assert(ep7s_poisoned(&p)&&!m.held&&m.signals==1);
 setup(&p,&m,&o);assert(ep7p_init(&runtime,o));m.signal_status=-25;assert(ep7p_axis_adjust_result(&runtime,0,0,0,1,false,&changed));assert(changed&&ep7s_poisoned(&p));assert(!ep7p_axis_adjust(&runtime,0,0,0,1,false));
 puts("poll provider: core integration, decline, contention, poison, preemption-before-return, poison recheck and void-unlock boundary passed");return 0;}
