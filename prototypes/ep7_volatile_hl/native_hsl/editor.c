/* Reuses patches/hsl/pen-f/src/editor_storage/{editor,settings}.s.
 * H1 words live in the native ACTIVE part-1 cells; the original settings
 * registry/bank implementation owns persistence, reset and recall. No private
 * flash writer, spare record bytes, extra MVC category or retained UI pointer.
 */
#include "editor.h"
#include <stdint.h>

unsigned ep7h_axis;
extern uint32_t ep7h_active_get(unsigned property);
extern void ep7h_active_set(unsigned property,uint32_t value);
extern int ep7h_stock_value(unsigned property);
extern void ep7h_redraw(void *viewer);
extern void ep7h_refresh(unsigned profile);

static const unsigned bases[4]={927,939,951,1655};
static unsigned word(uintptr_t p) { return *(const volatile uint32_t *)p; }
static unsigned half(uintptr_t p) { return *(const volatile uint16_t *)p; }
static bool ready(void)
{
    return (word(0xa272e420u)&4u) && word(0x62253594u);
}
int ep7h_property(unsigned property)
{
    if(property>=927 && property<963)return (int)(property-927);
    if(property>=1655 && property<1667)return (int)(property-1655+36);
    return -1;
}
static unsigned decode(uint32_t cell)
{
    unsigned pair=cell&255u;
    if((cell>>16)!=0x4831u || (((cell>>8)^pair)&255u)!=255u ||
       (pair&15u)==8u || (pair>>4)==8u)return 0;
    return pair;
}
int ep7h_value(unsigned property,unsigned axis)
{
    if(ep7h_property(property)<0 || axis<1 || axis>2 || !ready())return 0;
    unsigned n=(decode(ep7h_active_get(property))>>(axis==2?4:0))&15u;
    return n<8?(int)n:(int)n-16;
}
int ep7h_set(unsigned property,int value)
{
    unsigned axis=ep7h_axis;
    if(ep7h_property(property)<0 || axis<1 || axis>2 || value < -5 || value > 5 || !ready())return 0;
    unsigned pair=decode(ep7h_active_get(property));
    if(axis==1)pair=(pair&240u)|((unsigned)value&15u);
    else pair=(pair&15u)|(((unsigned)value&15u)<<4);
    uint32_t cell=0x48310000u|((pair^255u)<<8)|pair;
    ep7h_active_set(property,cell);
    if(ep7h_active_get(property)!=cell)return 0;
    ep7h_refresh((unsigned)ep7h_property(property)/12u);
    return 1;
}
int ep7h_visible(void)
{
    uintptr_t container=word(0x61fc436cu),parent,selector;
    if(!container || !(parent=word(container)) || word(parent)!=0x6118957cu)return 0;
    selector=word(parent+76);
    return selector && half(selector+86)==1 && ready();
}
bool ep7h_snapshot(unsigned selector,int8_t out[24])
{
    if(!out)return false;
    for(unsigned i=0;i<24;i++)out[i]=0;
    if(selector<1 || selector>4 || !ready())return false;
    for(unsigned i=0;i<12;i++) {
        unsigned pair=decode(ep7h_active_get(bases[selector-1]+i));
        unsigned h=pair&15u,l=pair>>4;
        out[i]=(int8_t)(h<8?(int)h:(int)h-16);
        out[i+12]=(int8_t)(l<8?(int)l:(int)l-16);
    }
    return true;
}
int ep7h_cycle(const unsigned char *machine)
{
    uintptr_t parent,content,selector,viewer,container;
    uint16_t indices[12];
    unsigned key,profile,axis=ep7h_axis;
    if(!machine || machine[0]!=4 || machine[1]!=29 || axis>2 || !ready() ||
       word(0x61fc1ba8u) || word(0x61fc1bacu))return 0;
    container=word(0x61fc436cu);
    if(!container)return 0;
    parent=word(container);viewer=word(container+4);
    if(!parent || !viewer || word(parent)!=0x6118957cu || word(viewer)!=0x61189ba8u ||
       word(viewer+384)!=parent)return 0;
    selector=word(parent+76);content=word(parent+80);
    if(!selector || !content || half(selector+86)!=1 || word(content)!=0x61187534u ||
       half(content+120)!=13 || word(parent+16) || word(parent+44) ||
       word(content+16) || word(content+44))return 0;
    key=half(content+100);
    if(key>=0x13b3 && key<=0x13b5)profile=key-0x13b3;
    else if(key==0x140c)profile=3;
    else return 0;
    uintptr_t cursor=word(content+124);
    if(!cursor || half(cursor+90)>=13)return 0;
    axis=axis?axis-1:2;
    for(unsigned i=0;i<12;i++) {
        uintptr_t child=word(content+128+4*i);
        if(!child || half(child+84)!=bases[profile]+i || half(child+88)!=11)return 0;
        uintptr_t eligible=word(child+96),values=word(child+100);
        if(!eligible || !values)return 0;
        int value=axis?ep7h_value(bases[profile]+i,axis):ep7h_stock_value(bases[profile]+i);
        unsigned found=11,seen=0;
        for(unsigned j=0;j<11;j++) {
            int v=(int32_t)word(values+4*j);
            if(half(eligible+2*j) || v < -5 || v > 5 || (seen&(1u<<(v+5))))return 0;
            seen|=1u<<(v+5);
            if(v==value)found=j;
        }
        if(found==11)return 0;
        indices[i]=(uint16_t)found;
    }
    /* Stage every child first. Keep the actual cursor and native ALL flags. */
    *(volatile uint32_t *)0x61fc3804u=0;
    ep7h_axis=axis;
    for(unsigned i=0;i<12;i++) {
        uintptr_t child=word(content+128+4*i);
        *(volatile uint16_t *)(child+90)=indices[i];
    }
    ep7h_redraw((void *)viewer);
    return 1;
}
