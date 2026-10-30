#include "ep7_sem_provider.h"
static bool id_shape(uint16_t x) {
 return !(x & 0x8000u) && (x & 0x0fffu) && ((x & 0x7000u) <= 0x2000u);
}
static bool domain(ep7s_provider *p, uint16_t *id) {
 return p->native.get_tid(p->native.ctx,id)==0 && id_shape(*id) &&
        ((*id & 0x7000u)==(p->handle & 0x7000u));
}
static bool take(void *ctx) {
 ep7s_provider *p=ctx; uint16_t id=0; unsigned expected=EP7S_READY; int status;
 if (!domain(p,&id)) return false;
 /* Held throughout the core call, including the native release callback. This
    closes wake/preemption-before-poison publication, and rejects reentry. */
 if (!atomic_compare_exchange_strong_explicit(&p->state,&expected,EP7S_BUSY,
         memory_order_acquire,memory_order_relaxed)) return false;
 status=p->native.wait_poll(p->native.ctx,p->handle);
 if (status!=0) {
  /* -50 is proven non-acquisition on raw poll. Unknown positive/errors must not
     reopen admission; no automatic retry or signal after ambiguous acquire. */
  atomic_store_explicit(&p->state,status==-50?EP7S_READY:EP7S_POISON,memory_order_release);
  return false;
 }
 p->owner=id;
 return true;
}
static void give(void *ctx) {
 ep7s_provider *p=ctx; uint16_t id=0; int status;
 if (atomic_load_explicit(&p->state,memory_order_acquire)!=EP7S_BUSY ||
     !domain(p,&id) || id!=p->owner) {
  atomic_store_explicit(&p->state,EP7S_POISON,memory_order_release);return;
 }
 status=p->native.signal(p->native.ctx,p->handle);
 atomic_store_explicit(&p->state,status==0?EP7S_READY:EP7S_POISON,memory_order_release);
}
/* Direct-reader/UI APIs don't require task epochs. Scoped APIs remain unavailable. */
static int no_lease(void *ctx,ep7p_task *out) {(void)ctx;(void)out;return -1;}
bool ep7s_init(ep7s_provider *p,ep7s_native n,uint16_t handle) {
 if(!p || !n.get_tid || !n.wait_poll || !n.signal || !id_shape(handle))return false;
 p->native=n;p->handle=handle;p->owner=0;atomic_init(&p->state,EP7S_READY);return true;
}
ep7p_ops ep7s_ops(ep7s_provider *p) {ep7p_ops o={p,take,give,no_lease};return o;}
bool ep7s_poisoned(const ep7s_provider *p) {
 return atomic_load_explicit(&p->state,memory_order_acquire)==EP7S_POISON;
}
