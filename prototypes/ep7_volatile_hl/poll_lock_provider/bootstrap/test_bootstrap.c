#include "bootstrap.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
typedef struct{int tid_status,created,deleted,create_status,delete_status,tid_calls;uint16_t tid;bool switch_after_create,fail_context_after_create;}mock;
static int tid(void*v,uint16_t*out){mock*m=v;m->tid_calls++;if(m->tid_status)return m->tid_status;*out=m->tid;return 0;}
static int create(void*v,const ep7b_sem_spec*s){mock*m=v;assert(s->attributes==0&&s->initial==1&&s->maximum==1);m->created++;if(m->switch_after_create)m->tid=0x2002;if(m->fail_context_after_create)m->tid_status=-25;return m->create_status;}
static int drop(void*v,unsigned int h){mock*m=v;assert(h==0x1001);m->deleted++;return m->delete_status;}
static int poll(void*v,uint16_t h){(void)v;assert(h==0x1001);return 0;}
static int signal(void*v,uint16_t h){(void)v;assert(h==0x1001);return 0;}
static ep7b_native setup(ep7b*b,ep7p*p,mock*m){ep7b_native n;memset(b,0,sizeof *b);memset(p,0,sizeof *p);memset(m,0,sizeof *m);m->tid=0x1002;m->create_status=0x1001;n=(ep7b_native){m,create,drop,{m,tid,poll,signal}};return n;}
int main(void){ep7b b;ep7p p;mock m;ep7b_native n;int8_t hl[24]={1};
 n=setup(&b,&p,&m);assert(ep7b_prepare(&b,&p,n));assert(b.state==EP7B_PREPARED&&p.ready&&b.owned_handle==0x1001);int calls=m.tid_calls;assert(!ep7b_prepare(&b,&p,n));assert(m.created==1&&m.tid_calls==calls);assert(ep7b_mark_published(&b));assert(ep7p_edit(&p,0,hl));calls=m.tid_calls;assert(!ep7b_abort_unpublished(&b)&&m.deleted==0&&p.ready);assert(!ep7b_prepare(&b,&p,n)&&m.created==1&&m.tid_calls==calls);assert(!ep7b_mark_published(&b));
 n=setup(&b,&p,&m);assert(ep7b_prepare(&b,&p,n));assert(ep7b_abort_unpublished(&b));assert(b.state==EP7B_CLOSED&&!p.ready&&b.owned_handle==0&&m.deleted==1);assert(!ep7b_prepare(&b,&p,n));
 n=setup(&b,&p,&m);m.tid_status=-25;assert(!ep7b_prepare(&b,&p,n));assert(b.state==EP7B_FAILED&&!m.created&&!p.ready);
 n=setup(&b,&p,&m);m.create_status=-34;assert(!ep7b_prepare(&b,&p,n));assert(b.state==EP7B_FAILED&&!b.owned_handle&&!m.deleted);
 n=setup(&b,&p,&m);m.switch_after_create=true;assert(!ep7b_prepare(&b,&p,n));assert(b.state==EP7B_RETAINED&&b.owned_handle==0x1001&&!m.deleted);m.tid=0x1002;m.delete_status=-25;assert(!ep7b_abort_unpublished(&b));assert(b.state==EP7B_RETAINED&&b.owned_handle==0x1001);m.delete_status=0;assert(ep7b_abort_unpublished(&b));assert(m.deleted==2&&!b.owned_handle);
 n=setup(&b,&p,&m);assert(ep7b_prepare(&b,&p,n));m.delete_status=-42;assert(!ep7b_abort_unpublished(&b));assert(b.state==EP7B_QUARANTINED&&b.owned_handle==0x1001);m.delete_status=0;assert(!ep7b_abort_unpublished(&b)&&m.deleted==1);
 n=setup(&b,&p,&m);m.create_status=0x11001;assert(!ep7b_prepare(&b,&p,n));assert(b.state==EP7B_QUARANTINED&&b.owned_handle==0x11001&&!m.deleted);
 n=setup(&b,&p,&m);m.create_status=0;assert(!ep7b_prepare(&b,&p,n));assert(b.state==EP7B_FAILED&&!b.owned_handle&&!m.deleted&&!p.ready);
 n=setup(&b,&p,&m);m.create_status=0x10001;assert(!ep7b_prepare(&b,&p,n));assert(b.state==EP7B_QUARANTINED&&b.owned_handle==0x10001&&!m.deleted);
 for(int bad=0;bad<2;bad++){n=setup(&b,&p,&m);assert(ep7b_prepare(&b,&p,n));m.delete_status=bad?255:-18;assert(!ep7b_abort_unpublished(&b));assert(b.state==EP7B_QUARANTINED&&b.owned_handle==0x1001&&!p.ready);m.delete_status=0;assert(!ep7b_abort_unpublished(&b)&&m.deleted==1);}
 n=setup(&b,&p,&m);m.fail_context_after_create=true;assert(!ep7b_prepare(&b,&p,n));assert(b.state==EP7B_RETAINED&&b.owned_handle==0x1001&&!m.deleted&&!p.ready);m.tid_status=0;assert(ep7b_abort_unpublished(&b)&&m.deleted==1);
 n=setup(&b,&p,&m);n.raw.signal=0;assert(!ep7b_prepare(&b,&p,n)&&m.created==0);
 puts("bootstrap: actual core prepared/published, repeat guards, startup abort/context retry, retained unknown handles and quarantine passed");return 0;}
