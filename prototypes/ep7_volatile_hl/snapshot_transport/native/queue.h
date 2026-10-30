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
#endif
