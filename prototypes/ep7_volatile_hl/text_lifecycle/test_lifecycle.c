#include "lifecycle.h"
#include <assert.h>
struct fixture { int creates, destroys, attaches, binds, sets; int init,attach,bind,set,null_create; int child; };
static void *create(void *v,void *owner,const void *desc) {struct fixture *f=v;assert(owner&&desc);f->creates++;return f->null_create?NULL:&f->child;}
static int initialized(void *v,void *p) {struct fixture *f=v;assert(p==&f->child);return f->init;}
static void destroy(void *v,void *p) {struct fixture *f=v;assert(p==&f->child);assert(!f->attaches||f->attach!=1);f->destroys++;}
static int attach(void *v,void *owner,void *p) {struct fixture *f=v;assert(owner&&p==&f->child);f->attaches++;return f->attach;}
static int bind(void *v,void *p,void *owner) {struct fixture *f=v;assert(owner&&p==&f->child);f->binds++;return f->bind;}
static int set(void *v,void *p,const uint16_t *t) {struct fixture *f=v;assert(p==&f->child&&t[0]=='H');f->sets++;return f->set;}
int main(void) {
 int owner=0,desc=0;
 const uint16_t text[]={'H',0};
 for(int mode=0;mode<7;mode++) {
  struct fixture f={0}; f.init=f.attach=f.bind=f.set=1;
  struct ep7_text_lifecycle s={0};
  struct ep7_text_lifecycle_ops o={&f,create,initialized,destroy,attach,bind,set};
  if(mode==1)f.null_create=1;
  if(mode==2)f.init=0;
  if(mode==3)f.attach=0;
  if(mode==4)f.bind=0;
  if(mode==5)f.set=0;
  int r=ep7_text_create_attach(&s,&o,&owner,&desc,text,mode!=6);
  if(mode==0)assert(r==1&&s.bound&&f.sets==1&&f.destroys==0);
  if(mode==1||mode==6)assert(r==-1&&!s.child&&f.destroys==0);
  if(mode==2||mode==3)assert(r==-1&&!s.child&&f.destroys==1);
  if(mode==4||mode==5)assert(r==0&&s.child&&f.destroys==0);
  if(s.child) {
   int n=f.creates;assert(ep7_text_create_attach(&s,&o,&owner,&desc,text,1)==-1);assert(n==f.creates);
   ep7_text_revoke(&s);assert(!s.child&&!s.owner&&!s.bound&&f.destroys==0);
  }
 }
 ep7_text_revoke(NULL);
 assert(ep7_text_create_attach(NULL,NULL,NULL,NULL,NULL,0)==-1);
 return 0;
}
