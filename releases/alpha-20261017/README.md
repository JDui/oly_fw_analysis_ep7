# PEN-F HSL — alpha, 17 October 2026

Unofficial firmware adding Hue and Lightness to the Olympus PEN-F's existing
12-color Saturation editor. Requires a **PEN-F running firmware 3.1**, or an
earlier HSL alpha based on 3.1. Other camera models are not supported.

This release includes **both the main firmware and the Value graphics**.
No earlier HSL installation is required. The camera still displays version
3.1; use the release date and file checksum to identify the build.

## What's new since the 13 October alpha

- **−7…+7 for Hue, Saturation and Lightness**, including the wheel display,
  ALL edits, persistence and captured RAW processing data.
- **H/L included in ordinary OM Workspace settings backups and restores**,
  with Workspace itself unchanged. Combined and separate Current/C1–C4
  backups are supported.

## Included features

- H/S/L editing for all **15 COLOR profiles**: three shared by P/A/S/M and
  three in each of C1–C4.
- Changes apply to live view, EVF and JPEGs, survive restarts, and follow
  normal custom-mode registration and recall.
- In the COLOR editor, **Delete cycles Saturation → Lightness → Hue**.
  The selected color is shared between axes. The last axis is remembered
  until power-off. The former Vivid label reads **Value**.
- Hold OK to reset the selected axis. H/L reset to zero; Saturation resets
  to that profile's stock defaults. ALL retains the camera's group-edit behavior.
- New ORFs carry the captured H/S/L processing data. In-camera RAW development
  can use the selected COLOR profile's current H/L values.

## Installation and stock restore

Read [INSTALLATION.md](INSTALLATION.md) before flashing. It includes the SD-card
procedure, first checks, backup behavior and downgrade instructions.

| Purpose | File |
| --- | --- |
| Install this alpha | `install-alpha/DCOLYMP/E1229999.BIN` |
| Restore stock main and graphics | `restore-stock/DCOLYMP/E1229999.BIN` |

Both BINs are **44,433,408 bytes**. They contain components `0100` (main)
and `0101` (OSD graphics); the other two unchanged stock components are omitted.
The install changes 5,878 bytes versus matching stock: 5,145 main bytes,
725 bitmap bytes and eight checksum bytes. Component sizes are unchanged.

Install SHA256:
```text
4f9a36e6742728ded3d9b443915355f1d1eea0371e1da673f322de970994f717
```

Stock-restore SHA256:
```text
e13f9813d01d15441082ed907966aec54356d70ba0f75ae9b6c2b259ff01f26a
```

`SHA256SUMS` covers the package contents. `PATCH-SUMMARY.txt` and
`PATCH-RANGES.csv` describe the changes.

**Before returning to stock or an older alpha, bring all saved COLOR
saturation values within −5…+5, including custom modes.** Older firmware
cannot represent the extended saturation range.

## OM Workspace

Leave **Adjust Color unchecked** to develop an ORF with its captured H/S/L.
Workspace initially shows the embedded JPEG; actual redevelopment applies the
saved look. Saturation sliders populate, including ±7, but H/L sliders do not.
Enabling Adjust Color overrides the captured look.

Full settings backup/restore preserves H/L. A backup made before H/L backup
support supplies neutral H/L for restored banks. Loading a stock JPEG profile
through Workspace also resets H/L; JPEG profile-sharing metadata has not been
extended to carry the complete recipe.

## Testing and limitations

The exact combined release BIN has been installed successfully on the project
camera after restoring stock firmware. Stock restoration and installation of
this alpha were confirmed on 17 October 2026. Offline updater, checksum and
packaging checks also pass. Range/edit/reset/custom-mode tests and basic
Windows Workspace backup/restore and ORF redevelopment have passed; Windows
JPEG export has not been separately verified.

No recording-limit, grain, sharpening or other unrelated changes are included.
The added labels are English. Delete keeps its stock behavior outside the
COLOR editor. CRT and monochrome do not gain an HSL editor.

**Experimental firmware, used at your own risk.** Successful testing and
previous stock restores do not guarantee recovery from every failure.
