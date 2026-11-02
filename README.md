# Olympus PEN E-P7 HSL Firmware Port / E-P7 HSL 固件移植

## 最新进展 / Latest Status

> **2026-11-02 · 实机验证阶段 / On-device validation**

**本项目的 E-P7 改造固件已成功刷入实机，相机能够正常启动。初步功能测试结果正常，已测试的功能均有效。**

接下来将开展更全面的实际多场景使用测试。**待确认不同使用场景下运行稳定、未发现影响使用的问题后，将开放新固件下载。**

**目前尚未开放 E-P7 改造固件下载。** 仓库中的历史实验包与离线构建产物不代表已经通过实机验证的正式发布版本。

**The modified E-P7 firmware has been successfully flashed onto a physical camera and boots normally. Initial on-device tests indicate that the tested functions work as intended.** Further real-world testing across multiple scenarios is required. A firmware download will be made available after those tests confirm stable operation without significant issues.

**No E-P7 modified firmware download is available yet.** Previous experimental packages and offline build artifacts should not be considered validated releases.

## 研究资料 / Research Documentation

- [E-P7 研究文档与技术路线](docs/ep7/README.md)
- [历史实机启动问题记录](docs/ep7/BOOT_FAILURE_005.md)
- [构建和研究环境指南](docs/ep7/QUICKSTART.md)

## 来源与权利 / Attribution & Rights

This project builds on [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis). Upstream research, attribution and rights notices remain applicable; see [RIGHTS-AND-PROVENANCE.md](RIGHTS-AND-PROVENANCE.md). This repository does not declare a repository-wide license.

Upstream PEN-F firmware releases are **not** E-P7 firmware releases.
