# Owned descriptor consumption and retirement

`snapshot_transport/consumer.c` now completes the portable producer → three relay
→ worker value handoff. It requires a genuinely owned312-byte descriptor and its
original metadata identity at+48; a marker or numeric extent cannot prove this.

The first claim changes the local trailer from wire marker`E7T1` to cleanup-only
marker`E7C1` before attempting the transport lock. Only the original supported
kind19/dispatch2001 ticket may claim. Lock failure, unsupported routing and repeat
calls remain neutral, including if the route later changes back. The output value
is unchanged on failure. Ordinary wire decoding never accepts`E7C1` for forwarding
or application; cleanup alone accepts both markers.

ACK/drain/cancel calls`ep7q_retire_owned`. It marks consumed, extracts the full
metadata+serial key without route admission, and calls idempotent retirement. A
valid key already absent is complete; a stale serial cannot clear a newer ticket
at the same address. Lock failure retains the local trailer and returns false.
The adapter must keep the descriptor alive and must not ACK/free/reuse it until
cleanup succeeds. No retry may resample UI or claim the failed attempt again.

This is an explicit completion result, not an installed native wait/quarantine
policy. Native worker job registration, allocation extent, pre-free revocation,
ACK/drain seams and task-context providers remain required. Metadata identity
preservation through preprocessing/cleanup also needs native closure. A copied
snapshot survives transport retirement, but this does not extend a native job's
lifetime or authorize access after its native cleanup.

## Focused verification

- [Host integration](../../research/ep7/owned-consumer-integration-host.json): strict
  C11 and ASan/UBSan passed. Real consumer runs through all16 decoder operation slots;
  native backend/ABI/materializer/job callbacks are fixtures. Additional cases cover
  failed claim/retirement locks, changed route, drain, duplicate cleanup, stale serial
  and short owned extent. Sanitizer uses the previously justified non-PIE executable.
- [Target objects](../../research/ep7/owned-consumer-target.json): consumer text180
  bytes; compiler local frames48/40 bytes. The combined pipeline retains12 unresolved
  native/context symbols. No target link, execution, hook installation or firmware
  build; these are not full call-chain stack budgets. No SHA checks performed.

Next: bind the worker's fresh job allocation and revoke before native cleanup,
then use the same idempotent retirement at the qualified ACK/drain boundaries.
