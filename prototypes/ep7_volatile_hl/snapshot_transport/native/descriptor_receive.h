#ifndef EP7_DESCRIPTOR_RECEIVE_H
#define EP7_DESCRIPTOR_RECEIVE_H
#include "materializer.h"
/* Four words saved by the exact44-byte receive bridge at W+12..27. */
typedef struct {uint32_t handle,nominal_bytes,descriptor,trace_label;} ep7q_receive_input;
enum {EP7Q_DUAL_RECEIVER=1,EP7Q_KIND19_RELAY=2,EP7Q_KIND19_WORKER=3,EP7Q_DELEGATE_RECEIVE=256};
typedef struct {uint32_t descriptor;int timeout;unsigned origin;} ep7q_receive_args;
bool ep7q_descriptor_receive_layout(const ep7q_stack *,uint32_t,const ep7q_receive_input *,ep7q_receive_args *);
/* Unknown nonexpanded queues may retain their original300-byte wrapper. An
 * unqualified4c/ab/4f must never use that fallback with a possibly short object. */
int ep7q_receive_rejection(unsigned handle);
/* Same trusted stack/installation/queue contract as materializer context;
 * domains differ: dual relay, kind19 relay and kind19 worker must be admitted. */
bool ep7q_descriptor_receive_context_unresolved(unsigned,uint32_t,ep7q_materializer_context *);
int ep7q_descriptor_receive_entry(const ep7q_receive_input *,uint32_t);
#endif
