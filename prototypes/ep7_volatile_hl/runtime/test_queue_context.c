#include "queue_context.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
enum { ROOT=0x1000,LIMITS=0x2000,TABLE=0x3000,OBJECT=0x4000,BACKING=0x8000,HANDLE=0x4c };
typedef struct {
    uint16_t tid,count,id;
    uint32_t cpu,maximum,ring,backing;
    unsigned reads,queries,backing_reads;
    bool change_maximum;
} fixture;
static int get_tid(void *opaque,uint16_t *out)
{ fixture *f=opaque;f->queries++;*out=f->tid;return 0; }
static bool word(void *opaque,uint32_t address,uint32_t *out)
{
    fixture *f=opaque;f->reads++;
    switch(address){
    case 0x8050:*out=f->cpu;break;
    case 0x8ff00004:*out=ROOT;break;
    case ROOT+60:*out=LIMITS;break;
    case ROOT+232:*out=TABLE;break;
    case TABLE+4*(HANDLE-1):*out=OBJECT;break;
    case OBJECT+20:*out=128;break;
    case OBJECT+24:*out=f->maximum;break;
    case OBJECT+28:*out=f->ring;break;
    case OBJECT+32:
        *out=f->backing;f->backing_reads++;
        if(f->change_maximum)f->maximum=300;
        break;
    default:assert(!"out-of-range kernel read");return false;
    }
    return true;
}
static bool half(void *opaque,uint32_t address,uint16_t *out)
{
    fixture *f=opaque;f->reads++;
    if(address==LIMITS+26)*out=f->count;
    else if(address==OBJECT)*out=f->id;
    else {assert(!"out-of-range kernel halfword read");return false;}
    return true;
}
static fixture fresh(void)
{ fixture f={0};f.tid=0x6c;f.count=0xab;f.id=HANDLE;f.maximum=312;f.ring=10112;f.backing=BACKING;return f; }
static void rejected(fixture *f,unsigned handle)
{
    ep7n_task_ops ops={f,get_tid,word,half};ep7n_queue out;
    memset(&out,0xa5,sizeof out);
    assert(!ep7n_query_queue(&ops,handle,&out));
    assert(!out.handle && !out.object && !out.maximum && !out.backing);
}
int main(void)
{
    fixture f=fresh();ep7n_task_ops ops={&f,get_tid,word,half};ep7n_queue out,copy;
    assert(ep7n_query_queue(&ops,HANDLE,&out));
    assert(out.object==OBJECT && out.maximum==312 && out.ring_bytes==10112 && out.backing==BACKING);
    assert(out.attributes==128 && f.queries==2 && f.backing_reads==2);
    copy=out;assert(ep7n_same_queue(&out,&copy));copy.backing+=4;assert(!ep7n_same_queue(&out,&copy));
    f=fresh();f.count=HANDLE-1;rejected(&f,HANDLE);assert(f.backing_reads==0);
    f=fresh();rejected(&f,HANDLE|0x1000);assert(f.reads==0);
    f=fresh();f.cpu=1;rejected(&f,HANDLE);assert(f.reads==1);
    f=fresh();f.id=0;rejected(&f,HANDLE);assert(f.backing_reads==0);
    f=fresh();f.backing=UINT32_C(0xfffff000);rejected(&f,HANDLE);
    f=fresh();f.change_maximum=true;rejected(&f,HANDLE);assert(f.backing_reads==2);
    puts("actual queue view: bounds/domain/deletion/overflow/changing-config cases passed; kernel reads mocked");
    return 0;
}
