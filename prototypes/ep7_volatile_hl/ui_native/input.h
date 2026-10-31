#ifndef EP7_NATIVE_UI_INPUT_H
#define EP7_NATIVE_UI_INPUT_H
#include "bridge.h"
#include "../runtime/task_context.h"
#include <stdatomic.h>
struct ep7i_sample {
    uint32_t packet,delta,return_pc,native_d2,native_a2;
};
struct ep7i_dispatch {
    uint32_t event,parameter,extra,machine,packet;
};
/* Permanent GUI-task storage. A sample is copied inside a particular complete
 * preprocessor call, consumed by the immediately matching engine call, and
 * usable at most once inside that call. No global wheel-delta reread. */
struct ep7i_scope {
    atomic_bool started;
    ep7n_task task;
    const uint8_t *packet;
    uint32_t original_event,event,parameter,extra,machine;
    int32_t delta;
    unsigned phase,samples,valid,consumed;
};
extern struct ep7i_scope ep7_native_ui_input_scope;
int ep7i_native_cohort_present(void);
void ep7i_prepare_begin(const void *packet);
void ep7i_sample_wheel(const struct ep7i_sample *);
void ep7i_prepare_end(const void *packet,uint32_t result);
unsigned ep7i_dispatch_begin(const struct ep7i_dispatch *);
void ep7i_dispatch_end(unsigned held);
uint32_t ep7i_route(const struct ep7_native_ui_input *);
#endif
