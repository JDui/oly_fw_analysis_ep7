/* Self-authored minimal H/L label/value payload, not native widget creation. */
#include "text.h"
size_t ep7_text_format(const struct ep7_ui_frame *f,uint16_t *out,size_t cap)
{
    uint16_t text[EP7_TEXT_UNITS];size_t n=0;int value;unsigned i;int mixed=0;
    if(!f || !out || (f->category!=4 && f->category!=5) ||
       (f->public_mode!=54 && f->public_mode!=55 && f->public_mode!=56 && f->public_mode!=64) ||
       (f->selected_sector>11 && f->selected_sector!=255)) return 0;
    for(i=0;i<12;i++) if(f->logical_steps[i]<-7 || f->logical_steps[i]>7) return 0;
    text[n++]=(uint16_t)(f->category==4?'H':'L');text[n++]=' ';
    if(f->selected_sector==255) {
        text[n++]='A';text[n++]='L';text[n++]='L';
        value=f->logical_steps[0];
        for(i=1;i<12;i++) if(f->logical_steps[i]!=value) mixed=1;
    } else {
        unsigned sector=(unsigned)f->selected_sector+1u;
        text[n++]=(uint16_t)('0'+sector/10u);text[n++]=(uint16_t)('0'+sector%10u);
        value=f->logical_steps[f->selected_sector];
    }
    text[n++]=' ';
    if(mixed) {text[n++]='M';text[n++]='I';text[n++]='X';}
    else {text[n++]=(uint16_t)(value<0?'-':'+');text[n++]=(uint16_t)('0'+(value<0?-value:value));}
    text[n]=0;
    if(cap<n+1u) return 0;
    for(i=0;i<=n;i++) out[i]=text[i];
    return n;
}
int ep7_text_present(void *widget,const struct ep7_ui_frame *f)
{
    uint16_t text[EP7_TEXT_UNITS];
    if(!widget || !ep7_text_format(f,text,EP7_TEXT_UNITS)) return 0;
    return ep7_gcc_set_text_unresolved_binding(widget,text)==1 ? 1 : 0;
}
