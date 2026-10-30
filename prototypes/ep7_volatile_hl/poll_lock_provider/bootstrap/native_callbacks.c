/* Compile-only factory, not native initialization or hook publication. */
#include "bootstrap.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only bootstrap callback binding");
extern int ep7_gcc_raw_sem_create(const ep7b_sem_spec *);
extern int ep7_gcc_raw_sem_delete_unpublished(unsigned int);
extern ep7s_native ep7s_unresolved_raw_callbacks(void);
static int create(void *ctx,const ep7b_sem_spec *p){(void)ctx;return ep7_gcc_raw_sem_create(p);}
static int drop(void *ctx,unsigned int h){(void)ctx;return ep7_gcc_raw_sem_delete_unpublished(h);}
ep7b_native ep7b_unresolved_native(void){ep7b_native n;n.ctx=0;n.create=create;n.delete_unpublished=drop;n.raw=ep7s_unresolved_raw_callbacks();return n;}
