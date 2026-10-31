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
bool ep7c_resolve_live(ep7c *p,unsigned state,uintptr_t node,uint64_t *token)
{
 unsigned i;
 if(!state_ok(p,state) || !node || !token)return false;
 for(i=0;i<EP7C_CAP;i++) {
  const ep7c_entry *e=&p->entries[i];
  if(e->token && e->node==node && e->generation==p->generation) {
   *token=e->token;return true;
  }
 }
 return false;
}
static bool prefix_ok(const ep7c_entry *e,const ep7c_prefix *v)
{ return v && v->associated==e->associated && v->capture && v->capture_id>=1u && v->capture_id<=25u && v->raw_mode==11u && v->selector>=1u && v->selector<=4u; }
static bool prefix_same(const ep7c_prefix *a,const ep7c_prefix *b)
{
 return a && b && a->associated==b->associated && a->capture==b->capture &&
  a->capture_id==b->capture_id && a->raw_mode==b->raw_mode && a->selector==b->selector;
}
bool ep7c_sample_population(ep7c *p,unsigned state,uintptr_t node,uint64_t token,const ep7c_prefix *v,bool complete,ep7p *settings)
{
 ep7c_entry *e;ep7p_snapshot s;
 if(!state_ok(p,state) || !(e=lookup(p,node,token)))return false;
 if(e->attempted)return false;
 e->attempted=true; /* BEFORE any fallible capture; never retry current settings */
 if(!complete || !prefix_ok(e,v) || !settings)return false;
 if(!ep7p_capture(settings,v->raw_mode,v->selector,&s))return false;
 if(s.profile!=v->selector-1u)return false;
 e->prefix=*v;e->snapshot=s;e->sampled=true;return true;
}
bool ep7c_finish_population(ep7c *p,unsigned state,uintptr_t node,uint64_t token,const ep7c_prefix *v,bool complete)
{
 ep7c_entry *e;
 if(!state_ok(p,state) || !(e=lookup(p,node,token)) || !e->sampled)return false;
 e->sampled=false; /* This matched completion opportunity is consumed. */
 if(!complete || !prefix_ok(e,v) || !prefix_same(v,&e->prefix))return false;
 e->sealed=true;return true;
}
bool ep7c_seal(ep7c *p,unsigned state,uintptr_t node,uint64_t token,const ep7c_prefix *v,bool complete,ep7p *settings)
{
 return ep7c_sample_population(p,state,node,token,v,complete,settings) &&
  ep7c_finish_population(p,state,node,token,v,complete);
}
bool ep7c_copyout(ep7c *p,unsigned state,uintptr_t node,uint64_t token,const ep7c_prefix *v,ep7p_snapshot *out)
{
 ep7c_entry *e;
 if(!state_ok(p,state) || !(e=lookup(p,node,token)))return false;
 if(!e->sealed) {e->attempted=true;e->sampled=false;return false;}
 if(!out)return false;
 if(!prefix_ok(e,v)){e->sealed=false;return false;}
 if(!prefix_same(v,&e->prefix)){e->sealed=false;return false;}
 *out=e->snapshot;return true;
}
bool ep7c_forget(ep7c *p,unsigned state,uintptr_t node,uint64_t token)
{
 ep7c_entry *e;
 if(!state_ok(p,state) || !(e=lookup(p,node,token)))return false;
 memset(e,0,sizeof *e);return true;
}
