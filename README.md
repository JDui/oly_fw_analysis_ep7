# E-P7 HSL port research / E-P7 HSL 移植研究

> **EP7 branch: research in progress; no flash-ready E-P7 firmware.**
> **当前正在研究将 PEN-F 的 H/S/L 功能移植到 E-P7，尚未完成移植，禁止把 PEN-F 固件或偏移直接用于 E-P7。**

This branch investigates full per-color **Hue / Saturation / Lightness** controls
for the E-P7, building on [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis).
The stock twelve-color saturation editor is not already a full-HSL editor.
The first research target is **E-P7 1.1, internal build 1100, model 1420**,
identified by an exact stock hash—not every firmware with a similar name.

Current work:

- Trace the PEN-F patch's editor, settings and image-owned H/L transport contracts.
- Revalidate existing E-P7 COLOR table/builder landmarks with a read-only audit.
- Design controls around E-P7's own buttons/profile switch, not PEN-F's rear lever.
- Map all **four** COLOR profiles, including noncontiguous COLOR4 setting IDs.
- Establish E-P7-specific storage, capture, rendering and recovery evidence before
  enabling any patch builder. No E-P7 patch offsets or install image are supplied.

Start with the [research status, compatibility matrix and port plan](docs/ep7/README.md),
[controls proposal](docs/ep7/CONTROLS.md), and
[read-only stock audit](tools/ep7_stock_audit.py).
The audit emits JSON only and never contacts a camera. The exact stock input is
not included; firmware acquisition/revalidation and hardware testing remain open.

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
