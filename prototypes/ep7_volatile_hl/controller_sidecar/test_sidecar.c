#include "sidecar.h"
#include <assert.h>
#include <string.h>
ep7c ep7_controller_sidecar_unresolved;
static bool fail_lock;
static bool lock(void *p){(void)p;return !fail_lock;}
static void unlock(void *p){(void)p;}
static int current(void *p,ep7p_task *t){(void)p;t->tid=1;t->epoch=1;return 0;}
static void fresh(ep7c *p){memset(p,0,sizeof *p);assert(ep7c_init(p,33));}
int main(void)
{
 ep7c p={0};ep7p settings={0};ep7p_ops ops={NULL,lock,unlock,current};
 ep7c_prefix v={2,3,1,11,1},bad;ep7p_snapshot out,sentinel;uint64_t t,u;unsigned i;int8_t hl[24]={0};
 assert(ep7p_init(&settings,ops));hl[0]=4;assert(ep7p_edit(&settings,0,hl));
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
