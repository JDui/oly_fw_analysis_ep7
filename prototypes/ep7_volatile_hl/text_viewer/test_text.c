#include "text.h"
#include <assert.h>
#include <string.h>
static uint16_t copied[EP7_TEXT_UNITS];static int calls,result=1;
int ep7_gcc_set_text_unresolved_binding(void *widget,const uint16_t *s) {
    assert(widget==(void*)copied);++calls;unsigned i=0;do {copied[i]=s[i];}while(s[i++]);return result;
}
static void equal(const uint16_t *s,const char *a) {unsigned i=0;while(a[i]){assert(s[i]==(unsigned char)a[i]);i++;}assert(s[i]==0);}
static void rejected_unchanged(const struct ep7_ui_frame *f,uint16_t *out) {
    uint16_t before[12];memcpy(before,out,sizeof(before));
    assert(!ep7_text_format(f,out,12));assert(!memcmp(before,out,sizeof(before)));
}
int main(void) {
 struct ep7_ui_frame f={54,4,0,{0}};uint16_t out[12];
 for(unsigned i=0;i<12;i++)out[i]=0xabcd;
 assert(ep7_text_format(&f,out,12)==7);equal(out,"H 01 +0");assert(out[8]==0xabcd);
 f.selected_sector=11;f.category=5;f.logical_steps[11]=-7;assert(ep7_text_format(&f,out,12));equal(out,"L 12 -7");
 for(int value=-7;value<=7;value++) for(unsigned sector=0;sector<12;sector++) {
  f.selected_sector=(uint8_t)sector;f.logical_steps[sector]=(int16_t)value;
  assert(ep7_text_format(&f,out,12)==7);assert(out[5]==(value<0?'-':'+'));assert(out[6]=='0'+(value<0?-value:value));
 }
 for(unsigned i=0;i<12;i++){f.logical_steps[i]=7;} f.selected_sector=255;
 assert(ep7_text_format(&f,out,12)==8);equal(out,"L ALL +7");
 f.logical_steps[4]=6;assert(ep7_text_format(&f,out,12)==9);equal(out,"L ALL MIX");
 for(unsigned cap=0;cap<10;cap++) {uint16_t saved[12];memcpy(saved,out,sizeof(out));assert(!ep7_text_format(&f,out,cap));assert(!memcmp(saved,out,sizeof(out)));}
 f.logical_steps[4]=8;rejected_unchanged(&f,out);assert(!ep7_text_present(copied,&f));assert(!calls);
 f.logical_steps[4]=0;f.category=3;rejected_unchanged(&f,out);f.category=4;
 f.selected_sector=12;rejected_unchanged(&f,out);f.selected_sector=0;
 f.public_mode=57;rejected_unchanged(&f,out);
 const uint16_t modes[]={54,55,56,64};for(unsigned i=0;i<4;i++){f.public_mode=modes[i];assert(ep7_text_format(&f,out,12));}
 rejected_unchanged(0,out);assert(!ep7_text_format(&f,0,12));assert(!ep7_text_present(0,&f));
 assert(ep7_text_present(copied,&f)==1);equal(copied,"H 01 +7");
 result=0;assert(!ep7_text_present(copied,&f));result=-1;assert(!ep7_text_present(copied,&f));
 return 0;
}
