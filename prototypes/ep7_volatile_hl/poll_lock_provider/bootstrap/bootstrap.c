#include "bootstrap.h"
#include <stddef.h>
_Static_assert(sizeof(ep7b_sem_spec)==12,"kernel create input size");
_Static_assert(offsetof(ep7b_sem_spec,initial)==4,"initial offset");
_Static_assert(offsetof(ep7b_sem_spec,maximum)==8,"maximum offset");
static bool id_shape(unsigned x){return x<=0x7fffu && !(x&0x8000u) && (x&0xfffu) && (x&0x7000u)<=0x2000u;}
static bool current(ep7b *b,uint16_t *id){return b->native.raw.get_tid(b->native.raw.ctx,id)==0 && id_shape(*id);}
static bool same_domain(ep7b *b){uint16_t id=0;return id_shape((unsigned)b->owned_handle)&&current(b,&id)&&((id&0x7000u)==((unsigned)b->owned_handle&0x7000u));}
bool ep7b_abort_unpublished(ep7b *b){
 int status;
 if(!b || (b->state!=EP7B_RETAINED && b->state!=EP7B_PREPARED))return false;
 b->core->ready=false; /* still caller-private; never race a live user */
 b->state=EP7B_RETAINED;
 if(!id_shape((unsigned)b->owned_handle)){b->state=EP7B_QUARANTINED;return false;}
 if(!same_domain(b))return false; /* no delete attempted; ownership retained */
 status=b->native.delete_unpublished(b->native.ctx,(unsigned)b->owned_handle);
 b->last_native_status=status;
 if(status==0){b->owned_handle=0;b->state=EP7B_CLOSED;return true;}
 if(status!=-25)b->state=EP7B_QUARANTINED; /* no retry on missing/stale/unknown ID */
 return false;
}
bool ep7b_prepare(ep7b *b,ep7p *core,ep7b_native n){
 const ep7b_sem_spec spec={0,1,1};uint16_t id=0;int result;
 if(!b||!core||b->state!=EP7B_COLD||!n.create||!n.delete_unpublished||!n.raw.get_tid||!n.raw.wait_poll||!n.raw.signal)return false;
 b->native=n;b->core=core;core->ready=false;b->state=EP7B_CREATING;
 if(!current(b,&id)){b->state=EP7B_FAILED;return false;}
 result=n.create(n.ctx,&spec);b->last_native_status=result;
 if(result<=0){b->state=EP7B_FAILED;return false;}
 b->owned_handle=result;b->state=EP7B_RETAINED; /* ownership before validation */
 if(!same_domain(b)||!ep7s_init(&b->provider,n.raw,(uint16_t)result)||!ep7p_init(core,ep7s_ops(&b->provider))){
  (void)ep7b_abort_unpublished(b);return false;
 }
 b->state=EP7B_PREPARED;return true;
}
bool ep7b_mark_published(ep7b *b){
 if(!b||b->state!=EP7B_PREPARED)return false;
 b->state=EP7B_PUBLISHED;return true;
}
