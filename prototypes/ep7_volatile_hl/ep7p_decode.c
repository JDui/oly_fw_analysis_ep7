/* Exact E-P7 1100 schema from the audited request/stage/CPU-builder paths.
 * No pointer reconstructed from firmware bytes is ever dereferenced. */
#include "ep7p_decode.h"
static uint16_t u16(const unsigned char *p) { return (uint16_t)((uint16_t)p[0] | (uint16_t)p[1]<<8); }
static uint32_t u32(const unsigned char *p) { return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24; }
bool ep7p_decode(const unsigned char *b,size_t length,uint32_t base,uint32_t request_address,
                 unsigned selector,ep7p_observation *out) {
    const unsigned char *r,*op,*stage; uint32_t operation,offset,mode; unsigned index,count;
    ep7p_observation result={0}; uintptr_t host=(uintptr_t)b;
    if(!b || !out || length<EP7P_STOCK || host%4 || host>UINTPTR_MAX-EP7P_EXTENT ||
       !base || base%4 || base>UINT32_MAX-EP7P_EXTENT ||
       request_address!=base+11364u || selector<1 || selector>4) return false;
    r=b+11364; /* fixed embedded range [11364,13248), never an external address */
    if(u32(r)!=0x60355fd4u) return false;
    operation=u32(r+4);
    if(operation<base+14576u) return false;
    offset=operation-base-14576u;
    if(offset%56 || offset/56>=16) return false;
    op=b+14576+offset; /* membership checked before reading backlink bytes */
    if(u32(op)!=base || u32(op+8)!=request_address) return false;
    index=u16(b+11312); count=u16(b+11314);
    if(index!=2 || count<=index || count>16) return false;
    stage=b+10984+12*index;
    if(u32(stage)!=0x6036884du || u32(stage+4)!=0) return false;
    mode=(uint32_t)r[8]<<24 | (uint32_t)r[9]<<16 | u16(r+10);
    /* Conservative initial subset of the proven CPU-builder predicates. */
    if(r[16]!=0 || mode!=11 || u32(r+1524)!=0 || u16(r+12)==0xf00d ||
       (r[29]!=1 && r[29]!=2)) return false;
    result.job=host; result.request=host+11364; result.operation=host+14576+offset;
    result.request_operation=result.operation; result.operation_job=host;
    result.operation_request=result.request; result.callback=u32(r);
    result.stage_callback=u32(stage); result.stage=index; result.type=r[16];
    result.raw_mode=mode; result.raw_selector=selector; result.owner=u32(r+1524);
    result.mutation_callback=u32(stage+4); *out=result; return true;
}
