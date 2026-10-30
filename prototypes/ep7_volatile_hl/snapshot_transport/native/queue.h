#ifndef EP7_NATIVE_RAW_QUEUE_H
#define EP7_NATIVE_RAW_QUEUE_H
/* GCC-facing callable veneers, NOT hook-entry ABIs.
 * Only for independently qualified local queues/task domain and live buffers.
 * Raw receive has NO capacity argument: buffer must cover the queue's proven
 * configured maximum before the call. Positive return is actual byte count;
 * negative return is native error. These local veneers must not be rebound to
 * remote wrappers: those can return positive 255 on allocation failure.
 * No nonlocal exit, task migration, retained async buffer, or reentry permitted.
 */
int ep7_gcc_queue_receive_local(unsigned handle,void *buffer,int timeout);
int ep7_gcc_queue_send_local(unsigned handle,const void *buffer,unsigned bytes,int timeout);
/* Native600514b6 normalized send preserves queue notifications and error hooks.
 * Same local-domain/capacity/lifetime qualification required. Production sender
 * adapters use this entry, not the raw send veneer above. */
int ep7_gcc_queue_send_preserving_hooks(unsigned,const void *,unsigned,int);
/* ep7q_ops callback vocabulary: map named timeout-2 to canonical raw timeout-50;
 * owned I/O then restores stock normalized-2 exactly once. */
int ep7q_send_local_preserving(void *,unsigned,const void *,unsigned,int);
#endif
