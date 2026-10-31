/* Actual reviewed CALL bytes, not an installer-provided enable flag.
 * All sites are fixed E-P7 build1100 code addresses; G6 must still establish cold
 * installation, code visibility, init ordering and complete native alias closure. */
#include "native.h"
extern const unsigned char fresh[] __asm__("ep7_native_capture_fresh");
extern const unsigned char sample[] __asm__("ep7_native_capture_sample");
extern const unsigned char finish[] __asm__("ep7_native_capture_finish");
extern const unsigned char release_node[] __asm__("ep7_native_capture_node_free");
extern const unsigned char release_capture[] __asm__("ep7_native_capture_pool_release");
extern const unsigned char transition[] __asm__("ep7_native_state_service_bridge");
extern const unsigned char prewrite[] __asm__("ep7_native_capture_prewrite");
extern const unsigned char postwrite[] __asm__("ep7_native_capture_postwrite");
extern const unsigned char associated_recycle[] __asm__("ep7_native_associated_recycle");
extern const unsigned char associated_reset[] __asm__("ep7_native_associated_reset");
struct site { uint32_t address;const unsigned char *target;uint8_t width,mask,frame; };
static const struct site sites[]={
    {0x602973bc,associated_recycle,4,0,8},{0x6029c692,associated_reset,2,0xf0,28},
    {0x602a7ea0,prewrite,4,0,24},{0x602a8dca,postwrite,4,0,24},
    {0x602a31c7,fresh,2,0xa0,28},{0x602a440a,fresh,2,0xa0,28},{0x602a4480,fresh,2,0xa0,28},
    {0x602a31ea,sample,2,0xf0,20},{0x602a442c,sample,2,0xf0,20},{0x602a44a3,sample,2,0xf0,20},
    {0x602a31f7,finish,2,0xf0,48},{0x602a443e,finish,2,0xf0,48},{0x602a44b5,finish,2,0xf0,48},
    {0x60289c5e,transition,2,0xf0,32},{0x60289d02,transition,2,0xf0,32},
    {0x6029be5d,release_capture,4,0,4},
    {0x602a31b1,release_node,4,0,4},{0x602a4461,release_node,4,0,4},
    {0x6029f1c2,release_node,4,0,4},{0x602a4220,release_node,4,0,4},
    {0x6029f6ba,release_node,4,0,4},{0x602a29ab,release_node,4,0,4},
    {0x602a2a00,release_node,4,0,4},{0x602a2a48,release_node,4,0,4},
    {0x602a2ab5,release_node,4,0,4},{0x602a427d,release_node,4,0,4},
    {0x602a44d8,release_node,4,0,4},{0x602a2cb9,release_node,4,0,4},
    {0x602a2d0d,release_node,4,0,4}};
bool ep7cn_native_cohort_present(void)
{
    for (unsigned i=0;i<sizeof sites/sizeof sites[0];i++) {
        const struct site *s=&sites[i];
        const volatile uint8_t *p=(const volatile uint8_t *)(uintptr_t)s->address;
        uint32_t displacement=0;
        if (p[0]!=(s->width==2?0xcd:0xdd)||p[1+s->width]!=s->mask||p[2+s->width]!=s->frame) return false;
        for (unsigned j=0;j<s->width;j++) displacement|=(uint32_t)p[1+j]<<(8*j);
        if (s->width==2&&(displacement&0x8000u)) displacement|=UINT32_C(0xffff0000);
        if (s->address+displacement!=(uint32_t)(uintptr_t)s->target) return false;
    }
    return true;
}
