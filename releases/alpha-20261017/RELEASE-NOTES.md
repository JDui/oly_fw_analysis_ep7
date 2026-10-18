PEN-F HSL alpha for **Olympus PEN-F firmware 3.1**.

New since the 13 October alpha:

- Hue, Saturation and Lightness now cover **−7…+7**.
- H/L are preserved by ordinary **OM Workspace settings backup/restore**.

The ZIP contains the patched BIN, stock-restore BIN, instructions, checksums
and patch details. **Both firmware BINs include main and
OSD components (44,433,408 bytes each)**, so the Value bitmap is included and
no previous HSL installation is required.

[Release README](https://github.com/fishcu/oly_fw_analysis/blob/alpha-20261017/releases/alpha-20261017/README.md)
· [Installation and downgrade instructions](https://github.com/fishcu/oly_fw_analysis/blob/alpha-20261017/releases/alpha-20261017/INSTALLATION.md)

Install BIN SHA256:
```text
4f9a36e6742728ded3d9b443915355f1d1eea0371e1da673f322de970994f717
```

Stock-restore BIN SHA256:
```text
e13f9813d01d15441082ed907966aec54356d70ba0f75ae9b6c2b259ff01f26a
```

Before downgrading, bring every saved COLOR saturation value within −5…+5,
including custom modes. The firmware menu continues to display 3.1.

Stock restoration followed by installation of this exact combined release
BIN passed on the project camera on 17 October 2026. Offline updater and
checksum checks also pass. Experimental firmware is used at your own risk;
recovery from every failure is not guaranteed.
