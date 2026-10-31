#include "sidecar.h"
#include <assert.h>
#include <string.h>
ep7c ep7_controller_sidecar_unresolved;
static bool fail_lock;
static bool lock(void *p){(void)p;return !fail_lock;}
static void unlock(void *p){(void)p;}
static int current(void *p,ep7p_task *t){(void)p;t->tid=1;t->epoch=1;return 0;}
static void fresh(ep7c *p){memset(p,0,sizeof *p);assert(ep7c_init(p,33));}
static void test_live_join(ep7p *settings)
{
 ep7c p={0};ep7c_prefix v={2,3,1,11,4};
 ep7p_snapshot frozen,out;int8_t hl[24]={0};
 uint64_t old,current,resolved=999;unsigned i;
 assert(!ep7c_resolve_live(&p,33,1,&resolved) && resolved==999);
 assert(!ep7c_resolve_live(NULL,33,1,&resolved) && resolved==999);
 fresh(&p);
 assert(!ep7c_resolve_live(&p,33,0,&resolved) && resolved==999);
 assert(!ep7c_resolve_live(&p,33,1,&resolved) && resolved==999);
 assert(ep7c_register_fresh(&p,33,1,2,&old));
 assert(!ep7c_resolve_live(&p,33,1,NULL));
 assert(ep7c_resolve_live(&p,33,1,&resolved) && resolved==old);
 assert(ep7c_authorize(&p,33,1,resolved)); /* before native prefix access */
 hl[0]=6;hl[23]=-7;assert(ep7p_edit(settings,3,hl));
 assert(ep7c_seal(&p,33,1,resolved,&v,true,settings));
 assert(ep7c_copyout(&p,33,1,resolved,&v,&frozen));
 hl[0]=-2;hl[23]=3;assert(ep7p_edit(settings,3,hl));
 assert(ep7c_resolve_live(&p,33,1,&resolved));
 assert(ep7c_authorize(&p,33,1,resolved));
 assert(ep7c_copyout(&p,33,1,resolved,&v,&out));
 assert(out.profile==3 && out.hl[0]==6 && out.hl[23]==-7);
 assert(ep7c_forget(&p,33,1,resolved)); /* before original free */
 resolved=999;assert(!ep7c_resolve_live(&p,33,1,&resolved) && resolved==999);
 assert(ep7c_register_fresh(&p,33,1,2,&current) && current!=old);
 assert(!ep7c_authorize(&p,33,1,old));assert(!ep7c_forget(&p,33,1,old));
 /* Naked stale address would resolve the NEW token. The caller's live-object
    proof is essential: this interface intentionally cannot detect that ABA. */
 assert(ep7c_resolve_live(&p,33,1,&resolved) && resolved==current);
 ep7c_transition(&p,33,255);assert(ep7c_resolve_live(&p,33,1,&resolved));
 ep7c_transition(&p,33,33);resolved=999;
 assert(!ep7c_resolve_live(&p,33,1,&resolved) && resolved==999);
 assert(frozen.profile==3 && frozen.hl[0]==6 && frozen.hl[23]==-7);
 for(i=0;i<EP7C_CAP;i++) {
  assert(ep7c_register_fresh(&p,33,100+i,2,&current));
  assert(ep7c_resolve_live(&p,33,100+i,&resolved) && resolved==current);
 }
 assert(!ep7c_resolve_live(&p,33,999,&resolved));
 ep7c_transition(&p,33,7);resolved=999;
 assert(!ep7c_resolve_live(&p,7,100,&resolved) && resolved==999 && !p.poison);
 ep7c_transition(&p,7,33);assert(!ep7c_resolve_live(&p,33,100,&resolved));
 assert(ep7c_register_fresh(&p,33,1,2,&current));
 assert(!ep7c_resolve_live(&p,7,1,&resolved) && p.poison && resolved==999);
 assert(!ep7c_resolve_live(&p,33,1,&resolved));
}
static void test_split_population(ep7p *settings)
{
 ep7c p={0};ep7c_prefix v={2,3,1,11,4},changed;
 ep7p_snapshot out,sentinel;int8_t hl[24]={0};uint64_t token,reused;unsigned i;
 memset(&sentinel,0x55,sizeof sentinel);
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&token));
 hl[0]=5;hl[23]=-6;assert(ep7p_edit(settings,3,hl));
 assert(ep7c_sample_population(&p,33,1,token,&v,true,settings));
 hl[0]=-7;hl[23]=7;assert(ep7p_edit(settings,3,hl));
 fail_lock=true; /* Completion needs only the already frozen value. */
 assert(ep7c_finish_population(&p,33,1,token,&v,true));fail_lock=false;
 assert(!ep7c_finish_population(&p,33,1,token,&v,true));
 assert(ep7c_copyout(&p,33,1,token,&v,&out));
 assert(out.profile==3 && out.hl[0]==5 && out.hl[23]==-6);
 /* Early queued selection burns the pending snapshot, even with a NULL output. */
 for(i=0;i<2;i++){
  fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&token));
  assert(ep7c_sample_population(&p,33,1,token,&v,true,settings));out=sentinel;
  assert(!ep7c_copyout(&p,33,1,token,&v,i?NULL:&out));
  assert(!ep7c_finish_population(&p,33,1,token,&v,true));
  assert(!ep7c_sample_population(&p,33,1,token,&v,true,settings));
  assert(memcmp(&out,&sentinel,sizeof out)==0);
 }
 for(i=0;i<5;i++){
  fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&token));
  assert(ep7c_sample_population(&p,33,1,token,&v,true,settings));changed=v;
  if(i==0)changed.associated++;else if(i==1)changed.capture++;else if(i==2)changed.capture_id++;
  else if(i==3)changed.raw_mode=10;else changed.selector=3;
  assert(!ep7c_finish_population(&p,33,1,token,&changed,true));
  assert(!ep7c_finish_population(&p,33,1,token,&v,true));
  assert(!ep7c_copyout(&p,33,1,token,&v,&out));
 }
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&token));
 assert(ep7c_sample_population(&p,33,1,token,&v,true,settings));
 assert(!ep7c_finish_population(&p,33,1,token,&v,false));
 assert(!ep7c_finish_population(&p,33,1,token,&v,true));
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&token));
 assert(ep7c_sample_population(&p,33,1,token,&v,true,settings));
 assert(ep7c_forget(&p,33,1,token));assert(ep7c_register_fresh(&p,33,1,2,&reused));
 assert(reused!=token && !ep7c_finish_population(&p,33,1,token,&v,true));
 assert(!ep7c_finish_population(&p,33,1,reused,&v,true));
 assert(ep7c_sample_population(&p,33,1,reused,&v,true,settings));
 ep7c_transition(&p,33,33);assert(!ep7c_finish_population(&p,33,1,reused,&v,true));
}
static void test_capture_retirement(ep7p *settings)
{
 ep7c p={0};ep7c_prefix v={2,30,3,11,4},wrong;ep7p_snapshot frozen,out;
 uint64_t unsampled,sampled,sealed,reused;
 fresh(&p);
 assert(!ep7c_register_fresh_capture(&p,33,1,2,0,10,&unsampled));
 assert(!ep7c_register_fresh_capture(&p,33,1,2,1,0,&unsampled));
 assert(ep7c_register_fresh_capture(&p,33,1,2,1,10,&unsampled));
 assert(ep7c_register_fresh_capture(&p,33,2,2,2,20,&sampled));
 assert(ep7c_register_fresh_capture(&p,33,3,2,3,30,&sealed));
 assert(ep7c_seal(&p,33,3,sealed,&v,true,settings));
 assert(ep7c_copyout(&p,33,3,sealed,&v,&frozen));
 v.capture=20;v.capture_id=2;assert(ep7c_sample_population(&p,33,2,sampled,&v,true,settings));
 ep7c_retire_capture(&p,33,20);ep7c_retire_capture(&p,33,20);
 assert(!ep7c_authorize(&p,33,2,sampled) && !ep7c_finish_population(&p,33,2,sampled,&v,true));
 assert(ep7c_authorize(&p,33,1,unsampled) && ep7c_authorize(&p,33,3,sealed));
 ep7c_retire_capture(&p,33,10);assert(!ep7c_authorize(&p,33,1,unsampled));
 ep7c_retire_capture(&p,33,30);assert(!ep7c_authorize(&p,33,3,sealed));
 assert(ep7c_register_fresh_capture(&p,33,3,2,3,30,&reused) && reused!=sealed);
 v.capture=30;v.capture_id=3;assert(!ep7c_copyout(&p,33,3,sealed,&v,&out));
 /* A changed capture must fail before it can overwrite the reservation. */
 wrong=v;wrong.capture=31;assert(!ep7c_sample_population(&p,33,3,reused,&wrong,true,settings));
 assert(!ep7c_sample_population(&p,33,3,reused,&v,true,settings));
 assert(frozen.profile==3); /* Independently copied value survives pool release. */
}
int main(void)
{
 ep7c p={0};ep7p settings={0};ep7p_ops ops={NULL,lock,unlock,current};
 ep7c_prefix v={2,3,1,11,1},bad;ep7p_snapshot out,sentinel;uint64_t t,u;unsigned i;int8_t hl[24]={0};
 assert(ep7p_init(&settings,ops));hl[0]=4;assert(ep7p_edit(&settings,0,hl));
 test_live_join(&settings);
 test_split_population(&settings);
 test_capture_retirement(&settings);
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&t));assert(ep7c_authorize(&p,33,1,t));
 assert(!ep7c_authorize(&p,33,1,t+1));assert(!ep7c_authorize(&p,33,9,t));
 assert(ep7c_seal(&p,33,1,t,&v,true,&settings));
 hl[0]=-3;assert(ep7p_edit(&settings,0,hl));assert(ep7c_copyout(&p,33,1,t,&v,&out));assert(out.hl[0]==4);
 assert(!ep7c_seal(&p,33,1,t,&v,true,&settings));
 memset(&sentinel,0x55,sizeof sentinel);out=sentinel;bad=v;bad.capture_id=2;
 assert(!ep7c_copyout(&p,33,1,t,&bad,&out));assert(memcmp(&out,&sentinel,sizeof out)==0);
 assert(!ep7c_copyout(&p,33,1,t,&v,&out)); /* observed mismatch stays neutral */
 assert(ep7c_forget(&p,33,1,t));assert(!ep7c_forget(&p,33,1,t));
 assert(ep7c_register_fresh(&p,33,1,2,&u));assert(u!=t);assert(!ep7c_authorize(&p,33,1,t));
 ep7c_transition(&p,33,33);assert(p.generation==2);assert(!ep7c_authorize(&p,33,1,u));
 assert(ep7c_register_fresh(&p,33,1,2,&t));ep7c_transition(&p,33,255);assert(ep7c_authorize(&p,33,1,t));
 ep7c_transition(&p,33,7);assert(!ep7c_authorize(&p,7,1,t));ep7c_transition(&p,7,33);assert(!ep7c_authorize(&p,33,1,t));
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&t));assert(!ep7c_register_fresh(&p,33,1,2,&u));assert(p.poison);assert(!ep7c_init(&p,33));
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&t));fail_lock=true;assert(!ep7c_seal(&p,33,1,t,&v,true,&settings));fail_lock=false;assert(!ep7c_seal(&p,33,1,t,&v,true,&settings));
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&t));assert(!ep7c_seal(&p,33,1,t,&v,false,&settings));assert(!ep7c_seal(&p,33,1,t,&v,true,&settings));
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&t));assert(!ep7c_copyout(&p,33,1,t,&v,&out));assert(!ep7c_seal(&p,33,1,t,&v,true,&settings));
 fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&t));assert(!ep7c_copyout(&p,33,1,t,&v,NULL));assert(!ep7c_seal(&p,33,1,t,&v,true,&settings));
 for(i=0;i<6;i++){
  fresh(&p);assert(ep7c_register_fresh(&p,33,1,2,&t));bad=v;
  switch(i){case 0:bad.associated=8;break;case 1:bad.capture=0;break;case 2:bad.capture_id=0;break;case 3:bad.capture_id=26;break;case 4:bad.raw_mode=10;break;default:bad.selector=5;}
  assert(!ep7c_seal(&p,33,1,t,&bad,true,&settings));assert(!ep7c_seal(&p,33,1,t,&v,true,&settings));
 }
 fresh(&p);for(i=0;i<EP7C_CAP;i++)assert(ep7c_register_fresh(&p,33,100+i,2,&t));u=999;assert(!ep7c_register_fresh(&p,33,999,2,&u));assert(u==999);assert(!p.poison);
 fresh(&p);p.serial=UINT64_MAX;assert(!ep7c_register_fresh(&p,33,1,2,&t));assert(p.poison);
 fresh(&p);p.generation=UINT64_MAX;ep7c_transition(&p,33,33);assert(p.poison);
 fresh(&p);assert(!ep7c_authorize(&p,7,1,1));assert(p.poison);
 fresh(&p);ep7c_transition(&p,7,33);assert(p.poison);
 fresh(&p);assert(!ep7c_init(&p,33));assert(p.poison);
 fresh(&ep7_controller_sidecar_unresolved);assert(ep7c_register_fresh(&ep7_controller_sidecar_unresolved,33,1,2,&t));ep7_sidecar_transition_unresolved(33,33);assert(!ep7c_authorize(&ep7_controller_sidecar_unresolved,33,1,t));
 return 0;
}
