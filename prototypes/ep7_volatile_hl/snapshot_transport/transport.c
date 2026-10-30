#include "transport.h"
#include <string.h>
enum { PREPARED=1, PUBLISHED, CONSUMED };
static bool enter(ep7t *p)
{ return p && p->initialized && p->ops.lock(p->ops.ctx); }
static ep7t_entry *find(ep7t *p,ep7t_ticket t)
{
    unsigned i;
    if(!t.metadata || !t.serial)return NULL;
    for(i=0;i<EP7T_CAP;i++)
        if(p->entries[i].ticket.serial==t.serial &&
           p->entries[i].ticket.metadata==t.metadata)return &p->entries[i];
    return NULL;
}
bool ep7t_init(ep7t *p,ep7p_ops ops)
{
    if(!p || p->initialized || !ops.lock || !ops.unlock)return false;
    p->ops=ops;p->serial=0;memset(p->entries,0,sizeof p->entries);
    p->initialized=true;return true;
}
bool ep7t_prepare(ep7t *p,uintptr_t metadata,const ep7p_snapshot *s,ep7t_ticket *out)
{
    unsigned i;ep7t_entry *slot=NULL;bool ok=false;
    if(!metadata || !s || !out || s->profile>=4u)return false;
    for(i=0;i<24u;i++)if(s->hl[i]<-7 || s->hl[i]>7)return false;
    if(!enter(p))return false;
    for(i=0;i<EP7T_CAP;i++){
        if(p->entries[i].ticket.metadata==metadata)goto done;
        if(!p->entries[i].ticket.serial && !slot)slot=&p->entries[i];
    }
    if(!slot || p->serial==UINT64_MAX)goto done;
    slot->ticket=(ep7t_ticket){metadata,++p->serial};slot->state=PREPARED;
    slot->snapshot=*s;*out=slot->ticket;ok=true;
done:
    p->ops.unlock(p->ops.ctx);return ok;
}
bool ep7t_publish(ep7t *p,ep7t_ticket t)
{
    ep7t_entry *e;bool ok=false;
    if(!enter(p))return false;
    e=find(p,t);
    if(e && e->state==PREPARED){e->state=PUBLISHED;ok=true;}
    p->ops.unlock(p->ops.ctx);return ok;
}
bool ep7t_claim(ep7t *p,ep7t_ticket t,ep7p_snapshot *out)
{
    ep7t_entry *e;bool ok=false;
    if(!out || !enter(p))return false;
    e=find(p,t);
    if(e && e->state!=CONSUMED){
        ok=e->state==PUBLISHED;e->state=CONSUMED;
        if(ok)*out=e->snapshot;
    }
    p->ops.unlock(p->ops.ctx);return ok;
}
bool ep7t_retire(ep7t *p,ep7t_ticket t)
{
    ep7t_entry *e;bool ok=false;
    if(!enter(p))return false;
    e=find(p,t);
    if(e){memset(e,0,sizeof *e);ok=true;}
    p->ops.unlock(p->ops.ctx);return ok;
}
