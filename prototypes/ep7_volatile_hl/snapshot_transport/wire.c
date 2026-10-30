#include "wire.h"
#include <string.h>
#define MARKER UINT32_C(0x31543745) /* E7T1, wire protocol marker, not provenance */
static uint32_t get32(const unsigned char *p)
{ return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
static void put32(unsigned char *p,uint32_t v)
{ unsigned i;for(i=0;i<4;i++){p[i]=(unsigned char)v;v>>=8;} }
static bool prefix_ok(unsigned n)
{ return n==EP7W_COMMAND || n==EP7W_DESCRIPTOR; }
static uintptr_t metadata(unsigned n,const unsigned char *p)
{ return (uintptr_t)get32(p+(n==EP7W_COMMAND?12u:48u)); }
static bool route_ok(unsigned n,const unsigned char *p)
{
    if(n==EP7W_COMMAND)return get32(p+8)==19u;
    return get32(p+52)==19u && p[194]==1u && p[195]==0x20u;
}
bool ep7w_write_trailer(unsigned char *p,ep7t_ticket t)
{
    if(!p)return false;
    memset(p,0,EP7W_TRAILER);
    if(!t.metadata || t.metadata>UINT32_MAX || !t.serial)return false;
    put32(p,MARKER);put32(p+4,(uint32_t)t.serial);put32(p+8,(uint32_t)(t.serial>>32));
    return true;
}
bool ep7w_encode(unsigned n,const unsigned char *native,ep7t_ticket t,
                 unsigned char *wire,size_t capacity,size_t *written)
{
    size_t size;bool tagged=t.serial!=0;
    if(!prefix_ok(n) || !native || !wire || !written)return false;
    if(tagged){
        if(!t.metadata || t.metadata!=metadata(n,native) || !route_ok(n,native))return false;
    }else if(t.metadata)return false;
    size=n+(tagged?EP7W_TRAILER:0u);
    if(capacity<size)return false;
    memcpy(wire,native,n);
    if(tagged){
        (void)ep7w_write_trailer(wire+n,t);
    }
    *written=size;return true;
}
int ep7w_ticket(unsigned n,const unsigned char *wire,size_t actual,ep7t_ticket *out)
{
    ep7t_ticket t;
    if(!out)return EP7W_REJECT;
    *out=(ep7t_ticket){0,0};
    if(!prefix_ok(n) || !wire ||
       (actual!=n && actual!=n+EP7W_TRAILER))return EP7W_REJECT;
    if(actual==n || get32(wire+n)!=MARKER || !route_ok(n,wire))return EP7W_LEGACY;
    t.metadata=metadata(n,wire);
    t.serial=(uint64_t)get32(wire+n+4)|((uint64_t)get32(wire+n+8)<<32);
    if(!t.metadata || !t.serial)return EP7W_LEGACY;
    *out=t;return EP7W_TAGGED;
}
int ep7w_decode(unsigned n,const unsigned char *wire,size_t actual,
                unsigned char *native,size_t capacity,ep7t_ticket *out)
{
    int status;
    if(!out)return EP7W_REJECT;
    *out=(ep7t_ticket){0,0};
    if(!native || capacity<n)return EP7W_REJECT;
    status=ep7w_ticket(n,wire,actual,out);
    if(status!=EP7W_REJECT)memcpy(native,wire,n);
    return status;
}
bool ep7w_retirement_ticket(const unsigned char *p,ep7t_ticket *out)
{
    ep7t_ticket t;
    if(!out)return false;
    *out=(ep7t_ticket){0,0};
    if(!p || get32(p+EP7W_DESCRIPTOR)!=MARKER)return false;
    t.metadata=metadata(EP7W_DESCRIPTOR,p);
    t.serial=(uint64_t)get32(p+EP7W_DESCRIPTOR+4)|((uint64_t)get32(p+EP7W_DESCRIPTOR+8)<<32);
    if(!t.metadata || !t.serial)return false;
    *out=t;return true;
}
