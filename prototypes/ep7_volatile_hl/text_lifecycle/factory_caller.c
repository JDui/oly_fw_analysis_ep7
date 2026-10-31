/* Compiler ABI probe, not an installed UI flow. */
#include "native_create.h"
#include <stddef.h>
_Static_assert(sizeof(struct ep7_text_factory_result)==8,"target pointer/int layout");
_Static_assert(offsetof(struct ep7_text_factory_result,initialized)==4,"native result offset");
void *ep7_text_factory_probe(void *owner,const void *descriptor,int *initialized)
{
    struct ep7_text_factory_result result;
    ep7_gcc_text_factory(owner,descriptor,&result);
    *initialized=result.child?result.initialized:0;
    return result.child;
}
