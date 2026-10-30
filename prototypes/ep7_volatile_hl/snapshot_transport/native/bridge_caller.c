#include "queue.h"
/* Self-authored compile probe: constants expose outgoing register/stack slots.
 * Not an enabled native caller, a queue installation, or executable fixture. */
int ep7_queue_receive_probe(void *buffer)
{ return ep7_gcc_queue_receive_local(0x4b,buffer,-1); }
int ep7_queue_send_probe(const void *buffer)
{ return ep7_gcc_queue_send_local(0x4c,buffer,312,-1); }
