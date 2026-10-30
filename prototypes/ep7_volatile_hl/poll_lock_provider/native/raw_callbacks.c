/* Self-authored target-only normalized callback binding, not initialization.
 * Native targets remain unresolved. Private handle/domain/lifetime, raw poll
 * contract and task context must be separately qualified. No API is invoked
 * by compilation, and no existing semaphore is borrowed. */
#include "ep7_sem_provider.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only 32-bit pointer callback adapter");
_Static_assert(sizeof(uint16_t)==sizeof(unsigned short),"native output halfword");
extern int ep7_gcc_get_tid(unsigned short *);
extern int ep7_gcc_raw_sem_poll(unsigned int handle);
extern int ep7_gcc_raw_sem_signal(unsigned int handle);
static int current(void *ctx,uint16_t *out){(void)ctx;return ep7_gcc_get_tid(out);}
static int poll(void *ctx,uint16_t handle){(void)ctx;return ep7_gcc_raw_sem_poll(handle);}
static int signal(void *ctx,uint16_t handle){(void)ctx;return ep7_gcc_raw_sem_signal(handle);}
ep7s_native ep7s_unresolved_raw_callbacks(void){ep7s_native n={0,current,poll,signal};return n;}
