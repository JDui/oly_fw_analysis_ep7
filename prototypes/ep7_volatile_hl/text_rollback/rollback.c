#include "rollback.h"
static uint32_t read32(const uint8_t *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
int ep7_text_rollback(void *object,const struct ep7_text_rollback_ops *ops)
{
 const uint8_t *p=object;
 uintptr_t prior=0;
 if (!object||!ops||!ops->qualify||!ops->enter_context||!ops->restore_context)
  return 0;
 if (ops->qualify(ops->context,object,180)!=1) return 0;
 if (read32(p)!=UINT32_C(0x60faec7c)||p[4]!=0x10||p[5]!=0x80||
     read32(p+20)!=0||p[68]!=0||p[88]!=0) return 0;
 if (ops->enter_context(ops->context,p[28],p[29],&prior)!=1) return 0;
 ep7_gcc_text_cleanup_destroy_unresolved(object);
 /* No object reads after native destruction. */
 ops->restore_context(ops->context,prior);
 return 1;
}
