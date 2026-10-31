/* Runs under the ALREADY-ENTERED native kernel queue critical section.
 * The original function has proved a live queue object. Do not call get_tid,
 * private semaphore, allocation, scheduler, notification or fault callbacks here.
 * Original native frame W and its return slot are trusted ABI-owned storage. */
#include "runtime.h"
_Static_assert(sizeof(uintptr_t)==4,"target-only kernel gate addresses");
extern const unsigned char ep7_queue_receive_native_return[];
extern const unsigned char ep7_queue_raw_send_native_return[];
extern const unsigned char ep7_queue_named_send_native_return[];
static uint32_t word(uint32_t address)
{ return *(const volatile uint32_t *)(uintptr_t)address; }
static bool admitted(uint32_t object)
{
    ep7r *r=ep7r_get(&ep7_native_runtime_slot);ep7r_queue_object q;
    if(!ep7r_io_open(r))return false;
    q.object=object;q.handle=*(const volatile uint16_t *)(uintptr_t)object;q.reserved=0;
    q.attributes=word(object+20);q.maximum=word(object+24);
    q.ring_bytes=word(object+28);q.backing=word(object+32);
    return ep7r_guard_queue(r,&q);
}
bool ep7r_native_receive_gate(uint32_t w,uint32_t object)
{
    /* Other original callers retain their original ABI/behavior. Their buffer
     * capacity on expanded queues remains a separate installer caller-closure. */
    if(word(w+32)!=(uint32_t)(uintptr_t)ep7_queue_receive_native_return)return true;
    return admitted(object);
}
bool ep7r_native_send_gate(uint32_t w,uint32_t object)
{
    uint32_t pc=word(w+40);bool owned=pc==(uint32_t)(uintptr_t)ep7_queue_raw_send_native_return;
    /* Read parent+48 only after exact raw callsite proves the named frame48.
     * Both local branches of the notification-preserving wrapper are covered. */
    /* Both stock sites use seven-byte DD CALL32, not five-byte CALL16. */
    if(!owned && (pc==0x600514f3u || pc==0x60051557u))
        owned=word(w+88)==(uint32_t)(uintptr_t)ep7_queue_named_send_native_return;
    return !owned || admitted(object);
}
void ep7r_native_delete_observer(uint32_t object)
{ ep7r_note_queue_delete(ep7r_get(&ep7_native_runtime_slot),object); }
