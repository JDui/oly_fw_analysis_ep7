# E-P7 HSL port research / E-P7 HSL 移植研究

> **EP7 checkpoint: research paused at the user’s request; no flash-ready E-P7 firmware.**
> **当前研究检查点已提交，按用户要求暂停；PEN-F H/S/L 到 E-P7 的移植尚未完成，禁止把 PEN-F 固件或偏移直接用于 E-P7。**

**本地运行： [Windows / WSL / Linux QUICKSTART](docs/ep7/QUICKSTART.md)** · **[当前交接与阻塞](docs/ep7/HANDOFF.md)**

先跑电脑端测试，不连接相机；不会生成可刷镜像。

This branch investigates full per-color **Hue / Saturation / Lightness** controls
for the E-P7, building on [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis).
The stock twelve-color saturation editor is not already a full-HSL editor.
The first research target is **E-P7 1.1, internal build 1100, model 1420**,
identified by an exact stock hash—not every firmware with a similar name.

Current work:

- Trace the PEN-F patch's editor, settings and image-owned H/L transport contracts.
- Revalidate existing E-P7 COLOR table/builder landmarks with a read-only audit.
- Design controls around E-P7's own buttons/profile switch, not PEN-F's rear lever.
  Delete axis switching remains a routing-qualified candidate: the identified
  COLOR GUI machine event table does not directly admit local `0x9016`.
- Byte-verify all **four** COLOR profiles, including noncontiguous COLOR4 IDs,
  raw selectors **1–4**, storage/recall and conditional CPU coefficient construction.
- Develop a [compile-checkable volatile H/L prototype](prototypes/ep7_volatile_hl/):
  raw logical UI → captured-profile snapshot → fresh host job → bounded CPU lanes.
  A direct lifecycle path now avoids task-ID lookup; an exact-site native→GCC
  bridge and32-bit setup observer compile, but remain unlinked/uninstalled.
  Host integration tests run, and verified-source MN10300 GCC compiles the core,
  UI and bounded job decoder to unlinked objects. Native UI/lifetime adapters remain unbound,
  settings reset on boot, and **camera HSL has not been demonstrated**.
- Run an [actual software vertical slice](prototypes/ep7_volatile_hl/integration/):
  logical edits → real H/L state → UTF16 text payload → captured snapshot →
  all16 fresh-job operation slots → direct coefficients → revoke/free. Strict
  host and ASan/UBSan tests pass; native admission, allocation/processing and text
  setter callbacks remain fixtures, **not a camera demonstration**.
- Follow the conditional **kind19/0x2001 capture route** to its distinct fresh-job
  wrapper; the earlier concrete0x100d producer is labeled RecView/createAfFineTune,
  not demonstrated normal capture. Keep metadata ACK/free and image identity explicit.
- Establish E-P7-specific storage, capture, rendering and recovery evidence before
  enabling any patch builder. No E-P7 patch offsets or install image are supplied.

Start with the [research status, compatibility matrix and port plan](docs/ep7/README.md),
[bounded input/editor and processing trace](docs/ep7/INPUT_AND_PROCESSING_TRACE.md),
[GUI bridge and request ownership](docs/ep7/GUI_AND_REQUEST_OWNERSHIP.md),
[capture transport/completion](docs/ep7/CAPTURE_TRANSPORT_AND_COMPLETION.md),
[native selector design](docs/ep7/NATIVE_SELECTOR_DESIGN.md),
[storage and inline-job design](docs/ep7/STORAGE_AND_INLINE_JOB_DESIGN.md),
[capture admission](docs/ep7/CAPTURE_ADMISSION.md),
[capture attachment lifetime](docs/ep7/CAPTURE_ATTACHMENT.md),
[kind19 capture/job route](docs/ep7/KIND19_CAPTURE_ROUTE.md),
[task-scoped design](docs/ep7/TASK_SCOPED_ADMISSION.md),
[controls proposal](docs/ep7/CONTROLS.md),
[logical wheel mapping](docs/ep7/UI_EVENT_MAPPING.md), and
[read-only stock audit](tools/ep7_stock_audit.py).
The audit emits JSON only and never contacts a camera. The official **1.1/1100
stock input has now been acquired and byte-validated**, including all five
components, COLOR table/builder linkage and four profile defaults/dispatch cases.
See the [actual audit result](research/ep7/stock-audit-1100.json) and
[source record](research/ep7/stock-source-1100.json). The firmware itself is not
included. Input-event mapping, persistence/capture integration and hardware
testing remain open. Separate real-pthread integration passes strict, ASan/UBSan
and TSan runs; this does not qualify the camera’s native semaphore/domain/atomic
backend. The [private poll-only provider](prototypes/ep7_volatile_hl/poll_lock_provider/)
compiles without an atomic helper. Its [bootstrap](prototypes/ep7_volatile_hl/poll_lock_provider/bootstrap/)
now preserves native-handle ownership through startup failure, but native hook
installation, publication and [task-domain qualification](docs/ep7/TASK_DOMAINS.md)
remain open; published-runtime teardown is not implemented.

The native [text widget path](docs/ep7/TEXT_WIDGET.md) can copy UTF16 text, offering
a concrete alternative to the stock ±5 icon maps. Self-authored text formatting
and a setter ABI bridge compile, but [resource/factory qualification](docs/ep7/TEXT_WIDGET_CREATION.md),
unattached-child cleanup and H/L category binding remain unresolved. No native
renderer is enabled. Additional [node disposal evidence](docs/ep7/NODE_DISPOSAL.md)
and a [state-generation boundary](docs/ep7/NODE_STATE_GUARD.md) prevent treating the
earlier five observed free sites as complete lifetime coverage.

The user reports installed camera firmware **1.1**; this is not device testing
or a readback of the installed image.

Upstream history, notices and attribution are retained. There is **no
repository-wide license**; see [rights and provenance](RIGHTS-AND-PROVENANCE.md).
PEN-F releases linked below are **not E-P7 releases**.

---

# Upstream: Olympus / OM System firmware research

Shared knowledge and tools for studying and modifying Olympus and OM System
camera firmware. The repository covers update files, startup, settings, image
processing and camera interfaces.

PEN-F has the deepest coverage. Comparisons also cover E-M1, E-M5 and E-M10
models, E-P7, OM-3 and OM-5. Findings identify the model and firmware build;
similar code does not imply identical hardware or interchangeable patches.

- [Browse findings by topic](docs/README.md)
- [Set up the tools](REPRODUCING.md)
- [Choose a tool](tools/README.md)
- [Build the PEN-F HSL patch from source](patches/hsl/pen-f/README.md)
- [Use IDA with the MN103 module](docs/tooling/ida/README.md)
- [Find firmware identities and sources](provenance/README.md)
- [Contribute a finding or another camera model](CONTRIBUTING.md)

The tools include a component decoder, checksum checks, disassembly helpers,
and an MN103 instruction emulator. Image-processing hardware is not emulated.
Reports distinguish code inspection, execution with modeled hardware, and
physical camera tests.

References are organized by function, with model-specific details below each
topic. Shared formats and cross-model comparisons stay at the topic level.

Supply the firmware files required by each tool. A matching version label is
not enough: check the exact hash. The [update and recovery reference](docs/boot/pen-f/RECOVERY.md)
explains the limits of checksum and recovery evidence.

Ready-to-install PEN-F HSL packages are available under
[Releases](https://github.com/fishcu/oly_fw_analysis/releases):
[17 October 2026](https://github.com/fishcu/oly_fw_analysis/releases/tag/alpha-20261017)
and [13 October 2026](https://github.com/fishcu/oly_fw_analysis/releases/tag/alpha-20261013).
Each includes the patched firmware, stock restore, instructions and checksums.
See [license information](RIGHTS-AND-PROVENANCE.md) before reusing code.
