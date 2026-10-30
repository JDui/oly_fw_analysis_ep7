#include "ep7_sem_provider.h"
static bool id_shape(uint16_t x) {
 return !(x & 0x8000u) && (x & 0x0fffu) && ((x & 0x7000u) <= 0x2000u);
}
static bool domain(ep7s_provider *p, uint16_t *id) {
 return p->native.get_tid(p->native.ctx,id)==0 && id_shape(*id) &&
        ((*id & 0x7000u)==(p->handle & 0x7000u));
}
static void poison(ep7s_provider *p) {
 atomic_store_explicit(&p->poison,true,memory_order_release);
}
static bool take(void *ctx) {
 ep7s_provider *p=ctx;uint16_t id=0;int status;
 if(!domain(p,&id)||atomic_load_explicit(&p->poison,memory_order_acquire))return false;
 status=p->native.wait_poll(p->native.ctx,p->handle);
 if(status!=0){if(status!=-50)poison(p);return false;}
 /* A failed acquire in another admitted task could poison while we were in
    native code. Never enter the core with such a failure already published. */
 if(atomic_load_explicit(&p->poison,memory_order_acquire)){
  (void)p->native.signal(p->native.ctx,p->handle); /* poison is already permanent */
  return false;
 }
 atomic_store_explicit(&p->owner,id,memory_order_relaxed);
 return true;
}
static void give(void *ctx) {
 ep7s_provider *p=ctx;uint16_t id=0;int status;
 if(!domain(p,&id)||id!=atomic_load_explicit(&p->owner,memory_order_relaxed)){
  poison(p);return;
 }
 /* Native success may schedule the next owner before returning to C. */
 atomic_store_explicit(&p->owner,0,memory_order_relaxed);
 status=p->native.signal(p->native.ctx,p->handle);
 if(status!=0)poison(p);
 /* Absolutely no shared provider writes after successful release. */
}
static int no_lease(void *ctx,ep7p_task *out){(void)ctx;(void)out;return -1;}
bool ep7s_init(ep7s_provider *p,ep7s_native n,uint16_t handle){
 if(!p||!n.get_tid||!n.wait_poll||!n.signal||!id_shape(handle))return false;
 p->native=n;p->handle=handle;atomic_init(&p->owner,0);atomic_init(&p->poison,false);return true;
}
ep7p_ops ep7s_ops(ep7s_provider*p){ep7p_ops o={p,take,give,no_lease};return o;}
bool ep7s_poisoned(const ep7s_provider*p){return atomic_load_explicit(&p->poison,memory_order_acquire);}
