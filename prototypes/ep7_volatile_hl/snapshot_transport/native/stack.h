#ifndef EP7_QUEUE_STACK_H
#define EP7_QUEUE_STACK_H
#include "../owned_io.h"
typedef struct {
    const unsigned char *bytes; /* live contiguous current-task stack mapping */
    uint32_t low;
    size_t extent;
    /* Trusted installer/task provider proves all five frame edits and queue/I/O
     * publication group. Matching PCs, pointers or mapped capacity cannot set it. */
    bool expanded_group_ready;
} ep7q_stack;
const unsigned char *ep7q_stack_span(const ep7q_stack *,uint32_t,unsigned,unsigned);
bool ep7q_stack_word(const ep7q_stack *,uint32_t,unsigned,uint32_t *);
#endif
