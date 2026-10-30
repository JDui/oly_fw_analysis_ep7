#ifndef EP7_DESCRIPTOR_SEND_H
#define EP7_DESCRIPTOR_SEND_H
#include "stack.h"
#include "../forward.h"
/* Saved exact send603dfaa1 inputs. Nominal d1 is statically300 at this seam. */
typedef struct {uint32_t handle,descriptor,trace_label;} ep7q_send_input;
enum {EP7Q_NORMAL_SENDER=1,EP7Q_DUAL_SENDER=2,EP7Q_KIND19_SENDER=3};
typedef struct {uint32_t descriptor;int timeout;unsigned origin;} ep7q_send_args;
typedef struct {ep7q_stack stack;ep7q_forward_ops forward;} ep7q_send_context;
bool ep7q_descriptor_send_layout(const ep7q_stack *,uint32_t,const ep7q_send_input *,ep7q_send_args *);
/* Same stable frame/queue publication and current-task stack obligations as
 * receivers, plus a concrete retirement owner that accepts failed cleanup. */
bool ep7q_descriptor_send_context_unresolved(unsigned,uint32_t,ep7q_send_context *);
int ep7q_descriptor_send_entry(const ep7q_send_input *,uint32_t);
#endif
