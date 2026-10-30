# Retire owned tickets before native ACK

Three selected calls to original`603df97d` now have a bounded stack mapper and
self-authored bridge: normal rejection (`603dfc67`), command drain (`603e05c6`)
and worker completion (`603f2769`). These are candidate call-site substitutions,
not a global replacement of every ACK caller.

| Entry native SP `W` | Return atW+32 | Owned descriptor | Additional owner check |
|---|---|---|---|
|Normal command handler|`603dfc6c`|W+100|W+80=`603df8c0`|
|Command drain|`603e05cb`|W+44|Expanded drain frame and current stack provider|
|Worker completion|`603f2770`|W+36|Expanded worker frame and current stack provider|

The original native frame is`[a2,a3],32`. The bridge adds16 bytes, saves all four
native input registers, calls the retirement observer, restores the inputs and
tail-delegates to original ACK at the unchanged native SP. Original status,
notification payload, notification destination and native result remain stock.

Original ACK sends12 bytes containing the supplied status, descriptor+44 and
descriptor+48 to the destination at descriptor+32. Thus experimental retirement
must complete **before** that notification permits the original owner to act on
the metadata identity. The observer uses the owned cleanup key regardless of
changed route or prior claim. A failed lock retains the consumed trailer and
descriptor; it does not call original ACK until retirement succeeds.

The reviewed job-cleanup body directly clears descriptor+40, passes descriptor+36
to the job destructor, and does not directly write+48. This is not proof that all
transitive callees or other routes preserve+48. That native ownership invariant,
complete affected caller closure and teardown ordering still need closure.

## Current validation and limits

- [Stock seam report](../../research/ep7/ack-drain-current.json):38 exact instruction
  witnesses, including original ACK payload and next drain receive. No SHA checks.
- [Host integration](../../research/ep7/ack-drain-integration-host.json): strict and
  ASan/UBSan passed for the three layouts, true owned extent, unchanged native
  prefix, claimed/unclaimed/changed-route cleanup and withholding a modeled ACK
  during failed retirement. Native ACK, scheduler and C native binding were not run.
- [Target objects](../../research/ep7/ack-drain-target.json):16 bridge instructions,
  two relocations and native argument/frame preservation checked. Bridge41 text
  bytes, mapper190 with local48-byte frame, binding109 with local64-byte frame.
  Combined producer/relay/worker/ACK objects have19 unresolved native/context
  symbols. There is no target link, execution, installation or firmware build.

The trusted context provider and safe task progress callback are unbound. Once an
owned ticket exists, the provider must remain available until cleanup and cannot
downgrade lost qualification to an unknown stock path. Missing progress policy
retains the frame; this is not a validated fatal/recovery or RTOS waiting policy.
The next batch must implement shared runtime/task providers and their publication
and failure behavior before any installation group can be enabled.
