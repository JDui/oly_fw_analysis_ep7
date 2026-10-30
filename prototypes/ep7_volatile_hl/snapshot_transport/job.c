#include "job.h"
#include <string.h>
void ep7j_begin(ep7j_scope *scope,ep7t *transport,unsigned char *descriptor,size_t extent)
{
    if(!scope)return;
    memset(scope,0,sizeof *scope);
    if(ep7q_claim_owned(transport,descriptor,extent,&scope->snapshot))scope->state=EP7J_FROZEN;
}
void *ep7j_allocate(ep7j_scope *scope,unsigned requested,ep7j_allocator allocate,void *ctx)
{
    void *result;bool eligible;
    if(!allocate)return NULL;
    eligible=scope && scope->state==EP7J_FROZEN && requested==EP7P_STOCK;
    if(eligible){scope->state=EP7J_FINISHED;requested=EP7P_EXTENT;}
    result=allocate(ctx,requested);
    if(eligible && result){
        scope->allocation=result;scope->extent=requested;
        memset((unsigned char *)result+EP7P_STOCK,0,EP7P_EXTENT-EP7P_STOCK);
        scope->state=EP7J_ALLOCATED;
    }
    return result;
}
bool ep7j_register(ep7j_scope *scope,ep7p *core,void *observed_job)
{
    if(!scope || scope->state!=EP7J_ALLOCATED)return false;
    scope->state=EP7J_FINISHED;
    if(observed_job!=scope->allocation || scope->extent!=EP7P_EXTENT ||
       !ep7p_register_job(core,observed_job,scope->extent,&scope->snapshot,&scope->job))return false;
    scope->state=EP7J_REGISTERED;return true;
}
bool ep7j_revoke(ep7j_scope *scope,ep7p *core)
{
    if(!scope)return false;
    scope->state=EP7J_FINISHED;
    if(scope->job && !ep7p_release_job(core,scope->job))return false;
    scope->job=0;return true;
}
