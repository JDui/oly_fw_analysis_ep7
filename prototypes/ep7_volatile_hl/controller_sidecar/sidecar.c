#include "sidecar.h"
#include <string.h>
static void clear(ep7c *p) { memset(p->entries,0,sizeof p->entries); }
static bool die(ep7c *p) { p->poison=true;clear(p);return false; }
static bool state_ok(ep7c *p,unsigned state)
{
 if(!p || !p->initialized || p->poison)return false;
 if(state!=p->state || state>65535u)return die(p);
 return state==33u;
}
bool ep7c_init(ep7c *p,unsigned state)
{
 if(!p)return false;
 if(p->initialized || p->poison)return die(p);
 if(state>65535u)return die(p);
 p->initialized=true;p->state=state;p->generation=(state==33u);p->serial=0;clear(p);return true;
}
void ep7c_transition(ep7c *p,unsigned old,unsigned pending)
{
 if(!p)return;
 if(!p->initialized) { (void)die(p);return; }
 if(p->poison)return;
 if(old!=p->state || old>65535u || pending>65535u) {(void)die(p);return;}
 if(pending==255u)return;
 /* Bounded and infallible under exclusive controller ownership. */
 if(old==33u)clear(p);
 if(pending==33u) {
  if(p->generation==UINT64_MAX){(void)die(p);return;}
  ++p->generation;clear(p);
 }
 p->state=pending;
}
static ep7c_entry *lookup(ep7c *p,uintptr_t node,uint64_t token)
{
 unsigned i;
 if(!node || !token)return NULL;
 for(i=0;i<EP7C_CAP;i++)if(p->entries[i].token==token && p->entries[i].node==node && p->entries[i].generation==p->generation)return &p->entries[i];
 return NULL;
}
bool ep7c_register_fresh(ep7c *p,unsigned state,uintptr_t node,uintptr_t associated,uint64_t *token)
{
 unsigned i;ep7c_entry *slot=NULL;
 if(!state_ok(p,state))return false;
 if(!node || !associated || !token)return false;
 for(i=0;i<EP7C_CAP;i++) {
  if(p->entries[i].token && p->entries[i].node==node)return die(p);
  if(!p->entries[i].token && !slot)slot=&p->entries[i];
 }
 if(p->serial==UINT64_MAX)return die(p);
 if(!slot)return false;
 memset(slot,0,sizeof *slot);slot->node=node;slot->associated=associated;
 slot->generation=p->generation;slot->token=++p->serial;*token=slot->token;return true;
}
bool ep7c_authorize(ep7c *p,unsigned state,uintptr_t node,uint64_t token)
{ return state_ok(p,state) && lookup(p,node,token)!=NULL; }
static bool prefix_ok(const ep7c_entry *e,const ep7c_prefix *v)
{ return v && v->associated==e->associated && v->capture && v->capture_id>=1u && v->capture_id<=25u && v->raw_mode==11u && v->selector>=1u && v->selector<=4u; }
bool ep7c_seal(ep7c *p,unsigned state,uintptr_t node,uint64_t token,const ep7c_prefix *v,bool complete,ep7p *settings)
{
 ep7c_entry *e;ep7p_snapshot s;
 if(!state_ok(p,state) || !(e=lookup(p,node,token)))return false;
 if(e->attempted)return false;
 e->attempted=true; /* BEFORE any fallible capture; never retry current settings */
 if(!complete || !prefix_ok(e,v) || !settings)return false;
 if(!ep7p_capture(settings,v->raw_mode,v->selector,&s))return false;
 if(s.profile!=v->selector-1u)return false;
 e->prefix=*v;e->snapshot=s;e->sealed=true;return true;
}
bool ep7c_copyout(ep7c *p,unsigned state,uintptr_t node,uint64_t token,const ep7c_prefix *v,ep7p_snapshot *out)
{
 ep7c_entry *e;
 if(!state_ok(p,state) || !(e=lookup(p,node,token)))return false;
 if(!e->sealed) {e->attempted=true;return false;}
 if(!out)return false;
 if(!prefix_ok(e,v)){e->sealed=false;return false;}
 if(v->associated!=e->prefix.associated || v->capture!=e->prefix.capture || v->capture_id!=e->prefix.capture_id || v->raw_mode!=e->prefix.raw_mode || v->selector!=e->prefix.selector){e->sealed=false;return false;}
 *out=e->snapshot;return true;
}
bool ep7c_forget(ep7c *p,unsigned state,uintptr_t node,uint64_t token)
{
 ep7c_entry *e;
 if(!state_ok(p,state) || !(e=lookup(p,node,token)))return false;
 memset(e,0,sizeof *e);return true;
}
