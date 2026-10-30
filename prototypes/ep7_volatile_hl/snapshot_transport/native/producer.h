#ifndef EP7_NATIVE_PRODUCER_H
#define EP7_NATIVE_PRODUCER_H
#include "stack.h"
#include "../producer.h"
typedef struct {uint32_t handle,nominal_bytes,command,timeout;} ep7q_producer_input;
typedef struct {uint32_t command,scope;int timeout;} ep7q_producer_args;
typedef struct {ep7q_stack stack;ep7q_producer_ops producer;} ep7q_producer_context;
/* expected_scope_return is the linked address of the self-authored wrapper's
 * native return label, not an arbitrary PC accepted as allocation provenance. */
bool ep7q_producer_layout(const ep7q_stack *,uint32_t,const ep7q_producer_input *,uint32_t,ep7q_producer_args *);
/* Exact producer602ac3de entry owns associated in a2 and captureID in d0.
 * The provider must prove live associated/node reciprocal identity and exclusive
 * controller sidecar lifetime, then copy ALREADY frozen state. No late UI sample. */
bool ep7q_capture_snapshot_unresolved(uint32_t,uint32_t,ep7p_snapshot *);
void ep7q_capture_scope_entry(uint32_t,uint32_t,ep7q_capture_scope *);
bool ep7q_producer_context_unresolved(unsigned,uint32_t,ep7q_producer_context *);
int ep7q_producer_entry(const ep7q_producer_input *,uint32_t);
#endif
