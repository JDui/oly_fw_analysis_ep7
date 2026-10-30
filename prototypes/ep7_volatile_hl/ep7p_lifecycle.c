#include "ep7p_lifecycle.h"
/* Prototype reader budget, not native stage/operation count. */
#define READER_BUDGET 16u

typedef struct {
    ep7p *core;
    uintptr_t expected_request;
    bool enabled;
    ep7l_result *result;
} invocation;

/* Called only AFTER native output construction and request initialization.
   Neither request nor output pointer survives this synchronous call. */
static bool read_output(void *opaque,uintptr_t request,unsigned char *output,size_t length)
{
    invocation *i=opaque;
    bool applied;
    if(i->result->readers==READER_BUDGET) { i->enabled=false; return false; }
    ++i->result->readers;
    if(!i->enabled || request!=i->expected_request) return false;
    applied=ep7p_direct_apply(i->core,request,output,length);
    if(applied) ++i->result->applied;
    return applied;
}

static bool valid(const ep7l_ops *o)
{
    return o && o->construct && o->convert && o->process && o->cleanup;
}

bool ep7l_retry_cleanup(ep7p *core,const ep7l_ops *o,void *descriptor,ep7l_result *r)
{
    if(!core || !valid(o) || !r || !r->invoked || r->cleaned) return false;
    if(r->pending_job && !ep7p_release_job(core,r->pending_job)) {
        r->quarantined=true;
        return false;
    }
    r->pending_job=0;
    o->cleanup(o->ctx,descriptor);
    r->cleaned=true;
    r->quarantined=false;
    return true;
}

ep7l_result ep7l_run(ep7p *core,const ep7l_ops *o,void *descriptor,
                    const ep7p_snapshot *earlier_snapshot)
{
    ep7l_result r={0};
    ep7l_allocation a={0};
    ep7p_snapshot frozen;
    invocation i={core,0,false,&r};
    bool have_snapshot=earlier_snapshot!=NULL;
    if(!core || !valid(o)) return r; /* native_status not meaningful unless invoked */
    if(have_snapshot) frozen=*earlier_snapshot;
    r.invoked=true;
    r.native_status=o->construct(o->ctx,descriptor,&a);
    if(!r.native_status) r.native_status=o->convert(o->ctx,descriptor);
    if(!r.native_status) {
        if(have_snapshot && a.fresh_extent_proven && a.extent>=EP7P_EXTENT &&
           ep7p_register_job(core,a.base,a.extent,&frozen,&r.pending_job)) {
            r.registered=true; i.expected_request=(uintptr_t)a.base+11364u; i.enabled=true;
        }
        /* No outer reader scope/task lookup; actual request decoded at reader. */
        r.native_status=o->process(o->ctx,descriptor,read_output,&i);
        i.enabled=false;
    }
    (void)ep7l_retry_cleanup(core,o,descriptor,&r);
    return r;
}
