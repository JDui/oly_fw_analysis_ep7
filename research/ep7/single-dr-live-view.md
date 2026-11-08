# Single-frame DR live-view route

2026-11-08 correction: the user chose rendering-only highlight mapping. The
sensor gain/frame receipt discussed below is a historical requirement of the
abandoned gain route, not a blocker for the current unchanged-exposure mapping.
The current implementation reuses the 015 source snapshots and successful live
setter described here; see [current implementation](../../docs/ep7/SINGLE_FRAME_DR_IMPLEMENTATION.md).

E-P7 1.1 build 1100. Native control flow and ownership research.

## Preview processing owner

Preview is a separate native owner family. `603114e0` obtains a current five-slot source through `60309eb9(1)`. At `60311543..60311549` it sets the job header callback to `60306ad5`. The path `6031178a → 60321d3b → 60321ea8 → 603537eb` allocates the job, then `603117a3` publishes it in the table at `626693e8`. Kind19 still development uses callback `603e7b83` and its own capture/clone identity. The callback `60306ad5` also appears in the recview constructor at `6031333f`, so preview eligibility needs the specific native caller and acquired owner as well as the callback.

The existing H/L owner transport supplies two useful seams.

- The native raw mode and COLOR profile tuple arrives through the 68-byte settings publication at `6030cc39..6030cc4f`. The five 980-byte preview slots begin at `a2731098`. In that slot, `+941` and `+944` are the raw mode and COLOR profile. Native acquisition changes the selected slot state from 1 to 2 at `6032cbe7..6032cbf0`, then calls the S acquisition through `6032cbf8 → 6030ba2b → 6030bb19 → 6030bccc`. Native owner reuse skips S refresh when the existing owner's flag is set. [014 owner evidence](candidate-014-live-schema-observation.json).
- The parameter update at `603118de` resolves the current acquired source. `603118ec` loads its native job from the table, `603119bb → 603220ea → 60324071` copies the compact settings, and the accepted update is reset/armed at `603119d6 → 60322215 → 60353d02`. The existing 015 veneer copies H/L from the same acquired source on native setter success. This is a join to processing parameters. The 68-byte queue belongs to settings publication, so its index is insufficient as a sensor-frame identifier. [015 live observer](../../prototypes/ep7_volatile_hl/native_hsl/live.s), [015 live owner code](../../prototypes/ep7_volatile_hl/native_hsl/live.c).

The preview scheduler `60311a1a` fetches the native job table entry and calls `60322272`, then `603222d0 → 60354214` dispatches job stage callbacks. Other native entry points include `60328388 → 60311a1a` and `6030efc7 → 60322272`. These consumers constrain possible settings lifetime. They do not establish that a fresh sensor frame was produced under any particular gain.

## Preview RGB mapping and upload

Observed COLOR H/L changes in live view on 014 provide separate camera evidence for the shared colour-list path. The 015 ordinary and borrowed H/L hooks sit downstream of `603b1466`, whose `603b14a6` invokes the native RGB builder at `603ae80d`. The pre-cache RGB pointer seam at `603ae830` is shared. A preview hook would need its own owner check and positively identified effective request tuple, including stock RGB pointer variant and Gradation. The current still hook's owner check excludes preview. [015 build and camera history](../../docs/ep7/EXPERIMENTAL_SD_015.md), [stock RGB and H/L windows](single-dr-tone.md).

The normal driver prepares the ISP slot at `60334e1b → 603450dd`. Its program path at `6034518f → 60345ebe` uses the hardware mask in `*(C+8)`. Bits 3 and 18 lead respectively to `60345f9b` and `60345fbd`, calling the native table uploader `60346e37` for MMIO apertures `9f00a400` and `9f00d000`. The uploader considers the context bank owner and the dirty bit before writing. The driver starts work at `60334e44 → 603451d3`. Repointing the tuple can drive stock cache invalidation without mutable tables. This is CPU configuration evidence. The frame in which the sensor gain and ISP bank become active still requires a common generation or hardware acknowledgement.

## Independent preview exposure owner

The native preview AE constructor `60403e50` initializes three type-7 rows at `62295ca8`, stride 1168. Row pointers at `+4/+8/+12/+16` refer to in-row blocks at `+168/+260/+352/+408`. The first and third blocks are the native `CAM_EXPOSE` and `CAM_CAPTURE_MODE` inputs. `60404915` selects and computes a row, with `60404ad6 → 60407b58` writing the exposure tag fields. Submission is `604053f6 → 6040542e → 60409ae8 → 601e77d8 → 6011f863`. The row callback `60408109` marks the owner-local `+868` byte and wakes the exposure task through `60417e39` event 2. That byte acknowledges the command. It carries no identified displayed-frame identity.

The ordinary preview branch for capture flags clear of `0x1f08` reaches the TOP queue through `6011f863 → 6011fa59 / 6011faa9`. `601200aa → 60120105 → 60120d73` selects job `0x8007`, which reaches `6014dc5a → 6014dc9c → 6014dd11`. The stable mode branch `6014dd99 → 6014de04 → 6014e734 → 6014e533 → 60141ff8 → 6013cc9d → 6013cd94 → 6013fe45 → 6013c2ef` produces native `TG_GAIN`.

The native TG stage keeps its newest/previous tag pair at `*621f555c +8/+12`. `60138c99..60138cac` copies the tag from `TG_GAIN+20`, populated from `CAM_EXPOSE+24`. The serial descriptor at `601bad04` has six bytes of payload at `621f5570`. Both the changed-state call `6013a4e4` and the equal-state call `6013a844` select a list containing it in their ordinary branches. `60138f32..60138f45` copies the newest tag to previous just after scheduling serial work. Completion is later at `60138f74`. The tag pair can identify a submitted exposure generation. It does not identify a captured frame.

The lower driver reads `9b80060c` into `621f5ef0` at `6014d6c8` before the bus begins. Its five direct scratch references in decoded main are stores, and the same MMIO read appears before unrelated register getters. The bus completion callback at `6014d927..6014d92b` runs after its queue drains. The inspected paths do not carry either value into MCON. On the other side, `6030cbf9 → 6030b1a4` consumes image parameters and copies 68 bytes to owner `+912`. The alternate `6030cc1d → 60309c36` path copies descriptor fields `+0..12` to owner `+660` and computes further fields through `+48`. Neither supplies a demonstrated TG receipt. The comparison at `6032cbc9` uses reusable owner indexes.

## Ownership and transition requirements

The curve page continues to edit the selected level for its native picture-mode scope. At an independently qualified preview acquisition handoff, freeze an effective preview generation from the committed settings and native eligibility. Carry its applied gain identity forward with the frame or a native sequence key. The RGB path may choose the immutable compensation table only when that generation matches its positively bound preview frame and active gain. The next frame after a settings change can still belong to the previous generation. A frame prepared before confirmation must keep the previous complete pair, or wait/drop if the native path supports that. A missing gamma proof after a gain transition must prevent that frame from reaching display. Returning OFF requires the same two-sided handoff.

Reuse the native owner lifetimes and the existing per-source copy if a matching frame key can be demonstrated. The H/L implementation is precedent for settings transport but cannot establish applied gain ownership. Compact `+2116` is the native LiveHDRType byte. It must remain native. Preview correction remains disabled in the still candidate until a frame sequence or equivalent receipt joins the applied preview TG command to the display bank transition.
