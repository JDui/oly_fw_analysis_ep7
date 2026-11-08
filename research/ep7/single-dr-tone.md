# E-P7 1100 single-frame DR tone path

2026-11-08 / 022: the user reports V42 P91 and an apparent HDR view only during
AF. The previous UI omitted the existing COLOR refresh callback. HDR edits now
reuse that callback after the accepted ACTIVE write/enqueue. RGB qualification
uses the frozen COLOR-origin level rather than equating every later operation
key with the UI mode; pass, ownership and LUT checks remain. Native selector
status zero is observed as C0 without changing its outputs; 71/72 means an
accepted COLOR-origin request used another internal key. Exact camera keys,
AF scheduling and real pixels remain unobserved. Curve strength stays at 021.

2026-11-08 / 020 correction: scope is now COLOR1–4 only, as requested by the user.
The stock selector at `603ae386..603ae3c0` admits an ordinary borrowed RGB pointer
after checking its variant; `request+1524 != 0` alone is not a reason to reject a
known supported tuple. The 019 rendering guard incorrectly rejected it. The
020 replay executes the stock borrowed selector/cache for capture and preview,
including variant mismatch fallback and an unknown identity tuple left stock.
The source borrowed object stays unchanged. Actual camera use of this branch
and pixel output are still unverified; V/P observations distinguish sample,
transport and RGB selection. The curve strength is unchanged from 019.

2026-11-08 correction: the current candidate uses unchanged-exposure highlight
mapping via `ep7_highlight_gamma.py`, with knots 0–48 retained and no input gain
rescaling. The native selector/cache/upload evidence below remains applicable;
the 2x/4x compensated LUT prototype and forced compensation guards are archived
gain-route work. See [current implementation](../../docs/ep7/SINGLE_FRAME_DR_IMPLEMENTATION.md).

2026-11-07. This evidence covers stock CPU configuration and table upload. The source is the local `generated/ep7/full-input/main.decoded.bin` mapped at `0x60020020`. No SHA verification, firmware build, device operation or ISP pixel execution was performed here.

## Native routes

| Stock code window | Observed behavior |
| --- | --- |
| `603b17e6` / `603b1819` → `603b1466` | Shared colour stage-list wrappers. The list calls RGB configuration `603ae80d` at `603b14a6`. Its normal branch then calls `603af7c6`, the 015 HSL selector `603b0252`, and luminance LUT builder `603b0a70` at `603b14fa`. The predicate at `603b14b4` can select the alternate branch, so a match on the common entry alone is insufficient. |
| `603ae80d..603ae830` | With `C` the stage context, loads request `R = *(C+4)` and colour output `O = *(C+12)`. Calls RGB selector `603ae354` at `603ae82b`. Its three output pointer slots are local `sp+68/+72/+76`. The continuation `603ae830` preserves its return byte for later tests. |
| `603ae630..603ae706`, `603ae2fd..603ae351` | The normal selection checks `R+1879`, then `603b564d` (`R+1797 == 2`, Gradation Auto), then uses row 0 or row 2 of the ROM pointer table at `60530b6c`. Columns depend on `u16 R+14` and variant helper `603b5606`, which reads the request family and flag bits. `R+1808/+1809`, effect IDs and ART/bypass cases have earlier special branches. |
| `603ae8a4..603ae8f3`, `603ae98e..603ae9da` | The native RGB cache compares all three selected pointers and request conditions against state reached through `*(R+1484)+5736`. The rebuild calls `603ae7d3`, which stores pointers at `O+2596/+2600/+2604`, and updates that state when present. The reuse branch clears `C+108` bit 0. A late store into `O` alone could leave old gamma in hardware or desynchronize native coefficients. |
| `603b5e8c..603b5fc0` | Reads selected RGB LUT entries, including entry 255 at byte offset 510, masks with `4095` and derives a curve-dependent coefficient. The RGB builder uses these results when building words at `O+320/+324/+328`; special paths can configure additional words. |
| `603b0a70..603b0c26` | A separate luminance LUT pointer lives at `O+2608`. The selector path `603b092f → 603b039b` reads contrast `R+1796` and gradation `R+1797`. `R+1512` is the tone-control block pointer. With an active tone block, stock copies 256 halfwords to `O+2612`, applies `6034ff93` using `C+64` and the `R+1802` bit-7 flag, then points `O+2608` at that buffer. The 512-byte buffer ends at `O+3124`. The stage has disabled/override routes and can leave the pointer null. |
| `60345f81..60345fc2`, `60346e37..60346fd5` | The stock uploader can program colour bank `0x9f001000` and gamma/table bank `0x9f00a400`, or the corresponding `0x9f805000` and `0x9f00d000` path. `60346e37` compares the native context identity at `C+56` with the selected bank's state in `0xa27360ec`. A cached context can skip RGB upload unless `C+108` bit 0 is set. Matching RGB pointers allow the one-LUT path at `60346f09`; otherwise the writer fills separate RGB subranges. The writer loads 256 halfwords and writes 32-bit words; luminance starts at table bank +4096. |
| `6039a97b..6039a9b1` → caller `6035169b..603516d2` | Another consumer of `603ae354` stores the green gamma pointer at descriptor +0 and a luminance pointer at +8. Its caller configures an 80×60 descriptor with stride 192 at job+14960. This is evidence of a small-image consumer; the window alone does not establish its downstream role or make it a substitute for live-view development. |

The matching PEN-F structure is its common builder `604f8543`, RGB setup `604f6083`, and luminance selector/config `604f7c76 → 604f75e5`. The E-P7 addresses and native cache behavior above were read from the E-P7 stock input. The independent same-build Caduceus tone hook provides precedent for a luminance remap after native tone. It also explicitly accounts for a reused live-view context, which can otherwise apply a remap repeatedly. [PEN-F processing map](../../docs/color/pen-f/CREATIVE_PROCESSING_JOBS.md), [Caduceus tone research](https://github.com/cakelesscoder/caduceus-ep7/blob/main/docs/TONE_ENDS.md), [Caduceus tone implementation](https://github.com/cakelesscoder/caduceus-ep7/blob/main/patches/tone_ends/tone.s.in).

## Tables and narrow native replay

ROM row 0 at `60530b6c` contains eight pointers, in order `604ede78`, `604ee078`, `604ede78`, `604f3e78`, `604ede78`, `604ee078`, `604ede78`, `604ee078`. Each selects a 256-entry `u16` RGB curve with values between 0 and 4095. Row 2 includes `604ee278`, `604ee478` and `604f4078`. The first full-white sample in the three row-0 variants is at knot 237, 243 and 237 respectively. The identity RGB table `604edc78` has samples 0, 16, 32 at knots 0–2, and 4095 at knot 255. Luminance contrast-0 table `604fa082` has samples 0, 257, 514, 1023 at knots 0, 64, 128, 255. The identity tables, mask and writer establish table representation and output ranges. The exact input coding and the extent of earlier clipping remain a separate question. [Independent RGB selection and log analysis](https://github.com/cakelesscoder/caduceus-ep7/blob/main/docs/VIDEO_LOG.md).

The existing strict MN103 runner executed the two stock builders for three isolated inputs. Context, request and output were explicit RAM fixtures. The selector/builder instructions and ROM tables were original stock. Each call returned normally with no fault.

| Input fixture | RGB pointers | Luminance pointer | Native instructions, RGB / luminance |
| --- | --- | --- | --- |
| Natural key 2, normal gradation, contrast 0 | `604ede78` ×3 | `604fa082` | 506 / 209 |
| COLOR key 11, normal gradation, contrast +2 | `604ede78` ×3 | `604fb482` | 506 / 214 |
| Natural key 2, Gradation Auto, contrast 0 | `604ee278` ×3 | `604fa082` | 508 / 163 |
| COLOR key 11, normal gradation, `R+14=0`, `R+48=4` | `604ee078` ×3 | — | 507 / — |
| COLOR key 11, normal gradation, `R+14=2`, `R+48=4` | `604f3e78` ×3 | — | 490 / — |

To reproduce the disassembly, use the installed `/work/install/bin/mn10300-elf-objdump` in the `ep7-research-toolchain-20261030` Docker volume with `-b binary -m mn10300 -D -z --adjust-vma=0x60020020` and `--start-address` / `--stop-address` from the table. For the replay, use `tools/ep7_candidate_startup_sim.py`'s `Machine` with `/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu` and the same stock image. Use zeroed RAM at `C=0x19200000` (128 B), `R=0x19300000` (2048 B), `O=0x19400000` (8192 B). Set the three context pointers at `C+4/+8/+12` to `R/0/O`, set `C+52` to the effect key and `C+60` to `2`. Put the key at `u16 R+10`, `0x100d` at `u16 R+12`, `0x0105` at `u16 R+28`, and signed contrast and gradation bytes at `R+1796/+1797`. Enter through a synthetic native CALL with `a0=C`, register mask `0xf0`, and frame 16 for `603ae80d` or 176 for `603b0a70`. Inspect the four words at `O+2596`. The replay does not establish which settings or upstream request producers would generate a given fixture.

## Unintegrated RGB prototype

`tools/ep7_single_dr_gamma.py` exposes `gamma_table(stock_image, stock_pointer, level)` for the three checked row-0 addresses. It returns immutable 512-byte little-endian tables. Level 0 returns the stock slice byte for byte. For levels 1 and 2, an ideal 2×/4× reduction in linear input is an explicit model assumption. At input knot `i` through the reduced midtone anchor, the table uses stock knot `2i` or `4i` exactly. The nominal anchor is stock knot 32, approximately 1/8 of input scale. Its output depends on the native variant and remains equal to the corresponding stock output.

The shoulder starts at that anchor. For `s` knots past it, its added output is a linear `s` codes plus a rational term. The rational term fills the remaining distance to 4095 and has an initial slope chosen so that the combined slope matches the preceding sample interval. The linear term retains at least one output code per knot, even after rounding. Each curve reaches 4095 at its last sample, avoiding the stock table's existing plateau. This is a per-channel RGB mapping model, so high-saturation colours, white-balance interaction and the actual hardware's interpolator still require measurement.

```powershell
python -B tools/ep7_single_dr_gamma.py generated/ep7/full-input/main.decoded.bin
```

The command checked all six LUTs. Both endpoints and the midtone range passed for each, and each shoulder was strictly rising. The remaining 12-bit table-code spans from the modeled stock-white input onward were:

| Stock table | Anchor code | HDR200 model | HDR400 model |
| --- | ---: | ---: | ---: |
| `604ede78` | 1888 | 364 | 486 |
| `604ee078` | 2600 | 225 | 316 |
| `604f3e78` | 2756 | 211 | 292 |

The reported spans are coefficients under the ideal gain model. The tool generates no firmware and has no capture, preview or upload hook. A shared ROM pointer alone cannot authorize eligibility, since special branches may reuse the same table address.

## Native gamma cache interposition replay

The research probe assembles and links [a 124-byte AM33 veneer](single-dr-gamma-bridge.s) with the installed toolchain. It redirects `603ae830` in a temporary in-memory copy of stock using the exact five-byte preimage `f8 92 3c 5c 24`. The veneer reads a level from a byte appended to each explicit request fixture at `R+1884`. It checks the selector's success status and an equal, whitelisted RGB tuple, then substitutes three pointers to one read-only LUT before the stock cache compares the tuple. It replays `movbu d0,(60,sp)` and `mov (36,sp),a0` and rejoins at `603ae835`. The strict trace checks selector status, the displaced output load, SP, MDR, PSW and the other live registers at resume.

The fixture maps a shared native cache through `R+1484` and separate read-only requests and writable output records. All three requests use Natural, request format `R+14=2`, source family `R+28=0x0105` and zero context flags at `C+60` to enter the cache comparison. The harness initializes `C+108` bit 0 before each call and observes whether stock clears it. The level byte and addresses belong only to the fixture. The test does not allocate or use that byte in any camera request.

| Native builder sequence | Cache behavior | Instructions |
| --- | --- | ---: |
| Request A, HDR200 | Rebuilds output and cache with A's table | 609 |
| Repeat A | Reuses the same table and clears `C+108` bit 0 | 448 |
| Request B, HDR400 | Rebuilds output and cache with B's table | 609 |
| Request OFF | Rebuilds the stock tuple | 590 |
| Unmodified builder, OFF from the same post-B state | Rebuilds the stock tuple | 574 |

OFF matched the unmodified call across the context, all output records, native cache bytes and final registers. A's output record and selected table remained byte-identical through B and OFF. No MMIO or ISP pixels ran in this probe. The replay supports the pre-cache seam and immutable-pointer design. It leaves the live/capture owner, actual cache flags on each production mode, hardware upload state and ADC behavior to be established.

```powershell
$ep7Root = (Get-Location).Path
docker run --rm --pull never --network none `
  --mount "type=bind,source=$ep7Root,target=/repo,readonly" `
  --mount type=volume,source=ep7-research-toolchain-20261030,target=/work,readonly `
  rust:1.96-bookworm python3 -B /repo/research/ep7/single-dr-gamma-probe.py `
  /repo/generated/ep7/full-input/main.decoded.bin `
  --tool-prefix /work/install/bin/mn10300-elf- `
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

## Candidate seam and evidence still needed

- The strongest RGB seam is immediately after `603ae82b` returns and before the stock cache comparison and curve-dependent calculations. It can replace only a positively identified native LUT tuple with an immutable table keyed by that tuple and the frozen effective DR level. The stock selector result and ABI must be preserved. The incoming capture or preview snapshot still needs qualification. A live GUI lookup at the shared builder would make in-flight capture timing-dependent.
- A rebuilt RGB LUT can preserve the native response near grey and roll its top end toward code 4095, leaving the native luminance builder, H/S/M, contrast, and 015 HSL processing untouched. An input remap must account for the existing white plateau in the source LUT. Immutable tables avoid job-buffer lifetime and concurrent mutation. The narrow replay confirms native gamma cache transitions with the explicit fixture flags. A production hook still depends on request propagation and upload-state qualification.
- Gradation Auto is a real change in native RGB and can also select a different luminance route. The byte and its effect are verified; the relationship to any AE or exposure adjustment remains open. Keep it explicitly ineligible while the combination is unqualified.
- The stock luma uploader and the Caduceus Blacks/Whites example establish an adjustable tone table downstream of the RGB path by comparative interpretation. Neither is evidence that earlier sensor/ADC, white balance, matrix or front-end normalization retains the gain headroom needed here. The common COLOR configuration graph and the existing 015 transport provide places to trace capture and preview, while they do not prove equal gamma input or physical highlight protection.

## Upstream configuration and preview boundary

- The type-0 development builder `603397db` can call `603aaced` at `60339870`. That dispatcher chooses the shared colour list for `R+16` kind 0/16 with `R+28` family 1/2. The family-1 wrapper calls `603ab13b` and `603ac0c1` before the common list. At `603ab158..603ab256`, the former chooses other colour-configuration tables by request-format low nibble, the `603b5606` variant and effect ID. Hidden log IDs 2000 and 2001 explicitly receive different sets when the low nibble is 2–5 and the variant is set. Their behaviour cannot isolate the effect of the gamma table alone.
- The variant-dependent values begin to enter `O+332` at `603ab262`. `603466c7..603466e1` copies words from `O+320..492` into colour-bank `+384..556`, while `60346e37` uploads the LUTs into the separate table bank. At `603ae87a` the gamma builder initializes a local 14-bit value to 16383 and `603af184..603af1ba` puts its low 14 bits into `O+320/+324/+328`. In a derived variant the builder can use the result of `603b5e8c` instead. These are observable configurable limits and coefficients. The CPU writes do not identify the hardware comparison stage or its units.
- A second upstream interaction is concrete. `60354dcf..60354de5` copies four halfwords from job `+11330` into `R+1568`. Stock `60354050..60354122` populates this block using WB adjustment helper `603b5769`. The RGB builder reads `R+1568` channels in its coefficient path at `603af149..603af180`. This confirms gain-dependent configuration in the neighbourhood of the proposed substitution. It does not map ADC clipping or channel clipping after white balance.
- The proved native preview transport is the 015 chain. `603118d6` obtains the acquired owner, then `603119bb → 603220ea` updates the native job. `60322155 → 60324071` copies compact processing parameters. The successful `603119d6 → 60322215` arm resets the job through `60353d02`. A separate per-job stepping entry `60311a1a → 60322272` passes the same job-table object at `0x626693e8` to `60354214` (`603222d0`), whose `6035428e` dispatches a stage callback. The existing `014` schema and 015 H/L source establish owner/transport and stock COLOR use. The mode-specific callback row connecting every supported preview request to the new RGB hook and actual live acquisition gain still needs verification. [015 handoff](../../docs/ep7/HANDOFF.md), [native preview owner mapping](candidate-014-live-schema-observation.json), [native request chain](../../docs/ep7/STORAGE_AND_INLINE_JOB_DESIGN.md).

Within these windows there is no source-backed numeric mapping from sensor gain codes and ADC saturation through the ordinary colour setup to gamma input. The nearest concrete boundary is the stock MMIO configuration: the CPU gives the colour and LUT banks the above coefficients, then relies on opaque hardware to execute them on the frame. A replay can establish pointer, coefficient and upload behaviour. Quantitative retained range requires sensor calibration or matched RAW+JPEG evidence, including a saturated channel, under the intended gain strategy.

## Kind19 JPEG candidate

The candidate reads the level from the image job allocation extended by its constructor. The native operation binder at `60354bb0` writes the operation pointer to the embedded request at job `+11364`, with the operation's reciprocal request link at `+8`. The operation comes from one of 16 slots with a stride of 56 at job `+14576` and has a job link at `+0`. The hook requires both links, the stock request callback `60355fd4` and the kind19 job callback `603e7b83` before consulting the trailer. A request with the same callback can also be external, so the hook checks slot membership before dereferencing a derived job address. The separate capture join owns ticket publication.

For dispatch `0x2001`, `603e611e` builds the job header. `60353c70 → 60354709 → 603666c7 → 60368e97` initializes the ordinary sequence `603687d4`, `603687ed`, `6036884d`. The constructor can append `60356116` at `60354781..6035479a` as a separate format conversion. Conversion `603e689e → 60353d02` resets the index before the ticket binder runs. The binder qualifies these exact rows, requires no stage mutation callback and excludes auxiliary jobs. For the auxiliary-stage precondition, capture `+24050` is loaded from key `0x69b9` at `602a855a..602a856a`. Conversion copies it to parameter `+5560` at `603e6891..603e6897`, then reset sets job `+11339` when its low byte is 2 through `60354145 → 603666d0`.

At processing index 2, the observer checks the native kind, effective key, input family, mutation callback and ordinary variant fields. Natural and COLOR use the three known stock tuples listed above. Only after the observer replaces all three selected pointers does it mark the job trailer. That marker describes one configuration attempt and is cleared before its next stock config call. The original stock gamma builder runs after the interposition and retains its pointer-keyed cache behavior.

The stock type-0 builder calls the shared colour list at `60339870` and immediately calls `60343b23` at `60339878`. The latter sets bit 3 or 18 in the hardware mask at `*(C+8)`, selecting one of the ISP colour banks. The install path uses those bits at `60345f81..60345fbd` to call the gamma uploader. The CPU configuration joins the selected LUT to a bank. Hardware activation and clipping remain device measurements.

The guards cover distinct failure paths in the ordinary route.

| Native address and stock bytes | Guard |
| --- | --- |
| `60334ded` `cd f0 48 a0 48` | Run the original config `603396dd`. When it returns success, require a fresh marker for the same request before slot installation `60334e1b → 603450dd`. |
| `60334dda` `58 c0 fa ec 00 80` | Preserve the native test of bit 15 in context `+188`. An obligated job cannot take `60334de2 → 6033513d`, which bypasses the normal config. |
| `60354290` `5c 08 f0 70 1c` | Require the marker at the processing stage return before advancing. Replay the native status store to job `+11316`. The original scheduler cleans up outstanding operations on an error. |
| `603f28b0` `f8 bc 0c a0 00` | Check the same `0x2001` descriptor's live kind19 job before the success branch. If the original status is zero and the job still owes compensation, write `0x9e02` to the original stack status. |

The driver rejection sets `D2=0x9e02` and uses the existing context release at `60334e57 → 60344ef4`, before slot installation. The stock worker `60355aec..60355b1b` only sets job cancel for `0x9e01`. The existing still operation can normalize `0x9e01` to zero at `603e6286`, so the final guard also covers native cancellation before the processing callback. In the ordinary descriptor path `603f28b0..603f28d7`, nonzero status skips the success callback `603e6b83`, frees resources, and becomes the returned descriptor status. These windows establish the native cleanup and success-callback boundaries. A real file lifecycle and sensor-to-JPEG run remain outside the fixture.

The focused target replay runs the compiled gamma veneers and real native builder with explicit kind19-shaped jobs. The linked-image mode uses the candidate's actual trailer functions. The guard fixture substitutes a bounded native config body that either invokes the stock RGB builder or returns without it, and stops on entry to the original context cleanup. The fixture does not emulate the ISP allocator, MMIO, sensor capture or JPEG output.

The linked-image replay passed Natural HDR200, repeat cache reuse, COLOR HDR400 and OFF. Their instruction counts were 805, 644, 813 and 783. OFF matched the unhooked 575-instruction builder across context, output records, cache bytes and return registers. The retained Natural output and LUT were byte-identical through COLOR and OFF. The failure replay accepted a fresh marker, cleared and rejected an older marker on an unconfigured retry, blocked the bypass for an obligated job, and stored `0x9e02` on a missing marker at scheduler return. The final descriptor guard used the original branch to distinguish missing proof, fresh proof, OFF and an existing native error. OFF reached the original config continuation with all registers equal to unhooked execution. A request with an external callback-matched object continued with its derived job address unmapped.

~~~powershell
$ep7Root = (Get-Location).Path
docker run --rm --pull never --network none `
  --mount "type=bind,source=$ep7Root,target=/repo,readonly" `
  --mount type=volume,source=ep7-research-toolchain-20261030,target=/work,readonly `
  rust:1.96-bookworm python3 -B /repo/research/ep7/single-dr-gamma-target-probe.py `
  /repo/generated/ep7/full-input/main.decoded.bin `
  --candidate /repo/generated/ep7/single-dr/candidate `
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
~~~
