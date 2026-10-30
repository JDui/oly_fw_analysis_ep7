#ifndef EP7_MATERIALIZER_FRAME_H
#define EP7_MATERIALIZER_FRAME_H
#include "../owned_io.h"
typedef struct {
    const unsigned char *bytes; /* live contiguous current-task stack mapping */
    uint32_t low;
    size_t extent;
    /* Trusted installer/task provider proves all five frame edits and queue/I/O
     * publication group. Matching PCs, pointers or mapped capacity cannot set it. */
    bool expanded_group_ready;
} ep7q_stack;
enum {EP7Q_NORMAL=1,EP7Q_DRAIN_FIRST=2,EP7Q_DRAIN_NEXT=3};
typedef struct {
    uint32_t command,descriptor;
    int timeout;
    unsigned origin;
} ep7q_materializer_args;
/* Resolves only the exact receive603dfc9b frame and three reviewed caller chains.
 * Reads are bounds-checked before access. No native pointers are dereferenced by
 * this portable mapper; output addresses refer to the supplied stack mapping.
 * Failed resolution clears output and performs no queue operation or write. */
bool ep7q_materializer_layout(const ep7q_stack *,uint32_t wrapper_sp,
    unsigned handle,ep7q_materializer_args *);

typedef struct {
    ep7q_stack stack;
    void *queue_context;
    bool (*qualify_queue)(void *,unsigned,unsigned);
} ep7q_materializer_context;
/* Target binding must establish installation state, exact task/current stack,
 * local queue domain and a stable publication lifetime before any frame read.
 * On target stack.bytes==(const unsigned char *)(uintptr_t)stack.low.
 * The queue qualifier checks actual maximum and remains valid through raw I/O.
 * The provider is deliberately unresolved until G3/G6 install bindings exist. */
bool ep7q_materializer_context_unresolved(unsigned,uint32_t,ep7q_materializer_context *);
int ep7q_materializer_entry(unsigned,uint32_t);
#endif
