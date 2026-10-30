#include "rollback.h"
#include <assert.h>
#include <string.h>
static struct {int qualify,enter,restore,destroy,allow,enter_ok;unsigned current;} f;
static uint8_t bytes[180];
static int qualify(void *ctx,const void *p,size_t n){assert(ctx==&f&&p==bytes&&n==180);f.qualify++;return f.allow;}
static int enter(void *ctx,uint8_t x,uint8_t y,uintptr_t *prior){assert(ctx==&f&&x==3&&y==4);f.enter++;if(!f.enter_ok)return 0;*prior=f.current;f.current=0x304;return 1;}
static void restore(void *ctx,uintptr_t prior){assert(ctx==&f&&f.destroy==1&&f.current==0x304);f.current=(unsigned)prior;f.restore++;}
void ep7_gcc_text_cleanup_destroy_unresolved(void *p){assert(p==bytes&&f.current==0x304);f.destroy++;memset(bytes,0xa5,sizeof bytes);}
int main(void){
 const struct ep7_text_rollback_ops ops={&f,qualify,enter,restore};
 for(int mode=0;mode<9;mode++){
  memset(&f,0,sizeof f);memset(bytes,0,sizeof bytes);f.allow=f.enter_ok=1;f.current=0x102;
  bytes[0]=0x7c;bytes[1]=0xec;bytes[2]=0xfa;bytes[3]=0x60;bytes[4]=0x10;bytes[5]=0x80;bytes[28]=3;bytes[29]=4;
  if(mode==1)f.allow=0;
  if(mode==2)bytes[0]++;
  if(mode==3)bytes[4]++;
  if(mode==4)bytes[20]=1;
  if(mode==5)bytes[68]=1;
  if(mode==6)bytes[88]=1;
  if(mode==7)f.enter_ok=0;
  if(mode==8)bytes[23]=1;
  int ok=ep7_text_rollback(bytes,&ops);
  assert(ok==(mode==0));assert(f.current==0x102);
  assert(f.destroy==(mode==0)&&f.restore==(mode==0));
  if(mode==1)assert(!f.enter);
 }
 assert(!ep7_text_rollback(NULL,&ops));assert(!ep7_text_rollback(bytes,NULL));
 return 0;
}
