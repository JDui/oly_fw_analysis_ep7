/* Historical isolated router fixture. check_input.py uses the actual provider. */
#include "input.h"
#include <assert.h>
static uint32_t native_result;
static unsigned routes;
uint32_t ep7i_route(const struct ep7_native_ui_input *in)
{ assert(in->parent==0x12340000u);routes++;return native_result; }
int main(void)
{
    struct ep7_native_ui_input in={0x9032,1,0x12340000,0x60e4d101,0x12341000};
    assert(ep7_gcc_ui_route(0)==0);
    const uint32_t results[]={0,1,256};
    for (unsigned i=0;i<3;i++) { native_result=results[i];assert(ep7_gcc_ui_route(&in)==results[i]); }
    in.event=0x9031;assert(ep7_gcc_ui_route(&in)==256);
    in.event=0x9014;native_result=1;assert(ep7_gcc_ui_route(&in)==1);
    unsigned old=routes;in.event=0x900c;assert(ep7_gcc_ui_route(&in)==256&&routes==old);
    in.event=0x9016;assert(ep7_gcc_ui_route(&in)==256&&routes==old);
    return 0;
}
