/* Reuse existing fixture initialization without running its lifetime suites. */
#define _GNU_SOURCE
#define EP7_INPUT_TEST_MAIN input_lifetime_regressions
#include "../ui_native/test_input.c"
#include "postbuilder/cohort.h"
#include <sys/mman.h>
unsigned char ep7_postbuilder_far_calls[EP7_FAR_CALL_BYTES];
__asm__(".globl ep7_postbuilder_far_calls_end\n.set ep7_postbuilder_far_calls_end,ep7_postbuilder_far_calls+30");
const unsigned char ep7_native_postbuilder_bridge[1]={31};
static void reject_rows(volatile unsigned char **sites,unsigned char *veneers,
                        unsigned count,int (*cohort)(void))
{
    assert(cohort());
    for(unsigned i=0;i<count;i++) {
        sites[i][1]^=1;assert(!cohort());sites[i][1]^=1;assert(cohort());
        veneers[i*EP7_FAR_CALL_BYTES+12]^=1;
        assert(!cohort());veneers[i*EP7_FAR_CALL_BYTES+12]^=1;assert(cohort());
    }
    /* A valid different veneer is not interchangeable with the expected one. */
    uint32_t original=get32((const uint8_t *)(const void *)(sites[0]+1));
    ep7_far_fixture_word(sites[0]+1,(uint32_t)(uintptr_t)(veneers+30)-(uint32_t)(uintptr_t)sites[0]);
    assert(!cohort());ep7_far_fixture_word(sites[0]+1,original);assert(cohort());
}
int main(void)
{
    reset();input_install_fixture();
    volatile unsigned char *mvc[]={ep7_stock_mvc_rebuild_initial_call_unresolved,
        ep7_stock_mvc_rebuild_previous_call_unresolved,ep7_stock_mvc_rebuild_next_call_unresolved,
        ep7_stock_mvc_rebuild_touch_call_unresolved};
    volatile unsigned char *input[]={ep7_stock_ui_wheel_1_call_unresolved,ep7_stock_ui_wheel_0_call_unresolved,
        ep7_stock_ui_wheel_2_call_unresolved,ep7_stock_ui_wheel_4_call_unresolved,ep7_stock_ui_wheel_3_call_unresolved};
    reject_rows(mvc,ep7_mvc_far_calls,4,ep7m_native_cohort_present);
    reject_rows(input,ep7_input_far_calls,5,ep7i_native_cohort_present);
    void *page=mmap((void *)(uintptr_t)0x603b0000,4096,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(page==(void *)(uintptr_t)0x603b0000);
    uint8_t *site=(uint8_t *)(uintptr_t)0x603b02d9;
    assert(!ep7n_postbuilder_cohort_present());
    ep7_far_fixture(site,ep7_postbuilder_far_calls,ep7_native_postbuilder_bridge,0xf0,96);
    assert(ep7n_postbuilder_cohort_present());
    const unsigned corrupt[]={12,18,26};
    for(unsigned i=0;i<sizeof corrupt/sizeof corrupt[0];i++) {
        ep7_postbuilder_far_calls[corrupt[i]]^=1;
        assert(!ep7n_postbuilder_cohort_present());ep7_postbuilder_far_calls[corrupt[i]]^=1;
        assert(ep7n_postbuilder_cohort_present());
    }
    assert(munmap(page,4096)==0);
    return 0;
}
