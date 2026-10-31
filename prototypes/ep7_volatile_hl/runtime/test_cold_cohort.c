#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include "cold_cohort.c"
const unsigned char cold_clear[]={0},receive_gate[]={0},send_gate[]={0},delete_gate[]={0},capture_init[]={0},bootstrap[]={0};
static void page(uint32_t address)
{
    void *p=(void *)(uintptr_t)(address&~4095u);
    assert(mmap(p,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==p);
}
static void put32(uint32_t address,uint32_t value){memcpy((void *)(uintptr_t)address,&value,4);}
int main(void)
{
    unsigned negatives=0;
    /* Flags first: unmapped instruction sites must not be touched yet. */
    page(0xa272e000);assert(!ep7r_native_early_cohort_present());negatives++;
    put32(0xa272e420,15);assert(!ep7r_native_early_cohort_present());negatives++;
    put32(0xa272e41c,15);
    const uint32_t pages[]={0x60020000,0x60022000,0x60036000,0x60031000,0x60289000,0x60191000,0x62234000};
    for(unsigned i=0;i<sizeof pages/sizeof pages[0];i++)page(pages[i]);
    for(unsigned i=0;i<sizeof sites/sizeof sites[0];i++){
        const struct inline_site *s=&sites[i];unsigned char *p=(void *)(uintptr_t)s->address;
        assert((uintptr_t)s->target<=UINT32_MAX);
        p[0]=0xdc;put32(s->address+1,(uint32_t)(uintptr_t)s->target-s->address);
        memset(p+5,0xcb,s->bytes-5);
    }
    unsigned char *call=(void *)(uintptr_t)0x60191371;
    call[0]=0xdd;put32(0x60191372,(uint32_t)(uintptr_t)bootstrap-0x60191371u);call[5]=0;call[6]=4;
    unsigned char *alloc=(void *)(uintptr_t)0x600229b9,*free_bound=(void *)(uintptr_t)0x60022c28;
    alloc[0]=0x80;alloc[1]=31;free_bound[0]=0x8f;free_bound[1]=31;
    assert(ep7r_native_early_cohort_present());
    put32(0x62234fc0,33);assert(!ep7r_native_early_cohort_present());put32(0x62234fc0,0);negatives++;
    for(unsigned i=0;i<sizeof sites/sizeof sites[0];i++){
        unsigned char *p=(void *)(uintptr_t)sites[i].address;
        /* Every displaced byte, including every NOP, is installation evidence. */
        for(unsigned j=0;j<sites[i].bytes;j++){
            p[j]^=1;assert(!ep7r_native_early_cohort_present());p[j]^=1;negatives++;
        }
    }
    for(unsigned i=0;i<7;i++){call[i]^=1;assert(!ep7r_native_early_cohort_present());call[i]^=1;negatives++;}
    for(unsigned i=0;i<2;i++){
        alloc[i]^=1;assert(!ep7r_native_early_cohort_present());alloc[i]^=1;negatives++;
        free_bound[i]^=1;assert(!ep7r_native_early_cohort_present());free_bound[i]^=1;negatives++;
    }
    assert(ep7r_native_early_cohort_present());
    printf("{\"negative_checks\":%u,\"later_ui_pages_mapped\":false,\"synthetic_pages_executable\":false}\n",negatives);
    return 0;
}
