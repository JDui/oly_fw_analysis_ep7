/* PEN-F image_transport.s ownership pattern, rebound to E-P7 build1100.
 * Native capture owners freeze settings when their stock S snapshot completes.
 * The existing native converter carries that snapshot into each job's tail.
 * The constructor explicitly allocates 15512 bytes and zeros this 24-byte tail.
 * No locks, queue changes, task registries, waits or error/AF traps are added.
 */
#include "transport.h"
#include <stdbool.h>
#include <stddef.h>

extern bool ep7h_snapshot(unsigned selector,int8_t out[24]);
static int8_t capture_rows[25][24];
static uintptr_t clone_owner;
static int8_t clone_row[24];

static uintptr_t uncached(uintptr_t p)
{
    uintptr_t region=p&0xe0000000u;
    return region==0x60000000u || region==0xa0000000u ?
        (p&0x1fffffffu)|0xa0000000u : 0;
}
static int8_t *row(uintptr_t owner)
{
    uintptr_t p=uncached(owner);
    if(p>=0xaf6037c0u && p-0xaf6037c0u<25u*41984u &&
       (p-0xaf6037c0u)%41984u==0)
        return capture_rows[(p-0xaf6037c0u)/41984u];
    return p && p==clone_owner ? clone_row : NULL;
}
static void copy24(int8_t *to,const int8_t *from)
{
    for(unsigned i=0;i<24;i++)to[i]=from?from[i]:0;
}
void ep7h_capture_sample(uintptr_t capture)
{
    int8_t values[24]={0};
    int8_t *destination=row(capture);
    if(!destination)return;
    const volatile unsigned char *p=(const volatile unsigned char *)capture;
    if(p[24053]==11 && p[24083]>=1 && p[24083]<=4)
        (void)ep7h_snapshot(p[24083],values);
    copy24(destination,values);
}
void ep7h_capture_clone(uintptr_t destination,uintptr_t source)
{
    int8_t local[24];
    /* Read the prior clone row before changing its identity. Stock has exactly
     * one temporary clone at622933dc; its existing lifetime owns this row. */
    copy24(local,row(source));
    clone_owner=uncached(destination);
    copy24(clone_row,local);
}
void ep7h_capture_to_job(uintptr_t capture,uintptr_t parameters)
{
    /* Invoked only by the two native capture converters after their mode11 S
     * loops. parameters is the constructor's job+36, not an arbitrary request. */
    if(!parameters)return;
    copy24((int8_t *)(parameters+15488u-36u),row(capture));
}
static uint32_t u32(const unsigned char *p)
{ return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static void put16(unsigned char *p,int value)
{ unsigned v=(unsigned)value;p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8); }
void ep7h_transport_apply(const unsigned char *setup)
{
    if(!setup)return;
    const unsigned char *request=(const unsigned char *)(uintptr_t)u32(setup+4);
    unsigned char *out=(unsigned char *)(uintptr_t)u32(setup+12);
    if(!request || !out || u32(request)!=0x60355fd4u)return;
    /* The borrowed-table path also serves non-COLOR modes. The ordinary
     * COLOR hook supplied this guard implicitly; both paths now check it. */
    uint32_t mode=(uint32_t)request[8]<<24 | (uint32_t)request[9]<<16 |
                  (uint32_t)request[10] | (uint32_t)request[11]<<8;
    if(mode!=11)return;
    uintptr_t job=(uintptr_t)request-11364u,operation=u32(request+4);
    if(operation<job+14576u || operation-job-14576u>=16u*56u ||
       (operation-job-14576u)%56u)return;
    const unsigned char *op=(const unsigned char *)operation;
    if(u32(op)!=(uint32_t)job || u32(op+8)!=(uint32_t)(uintptr_t)request)return;
    /* Both native COLOR paths (ordinary and borrowed table) reach this reader.
     * Constructor and converters own the tail; no stage/task guessing is needed.
     * Preserve S and all other output fields, including control and calibration.
     */
    static const int16_t hue[11]={5000,4000,3000,2000,1000,0,-1000,-2000,-3000,-4000,-5000};
    static const int16_t lum[11]={-200,-150,-100,-50,-25,0,25,50,100,150,200};
    static const unsigned char bins[12]={0,2,4,6,8,10,1,3,5,7,9,11};
    const int8_t *hl=(const int8_t *)(job+15488u);
    for(unsigned k=0;k<12;k++) {
        int h=hl[bins[k]],l=hl[12u+bins[k]];
        if(h>=-5 && h<=5 && h)put16(out+706u+24u*k,hue[h+5]);
        if(l>=-5 && l<=5 && l)put16(out+710u+24u*k,lum[l+5]);
    }
}
