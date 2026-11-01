# EP7HSL 005 实验刷机包：构建与交付记录

> **2026-11-01 后续实机反馈：005 正常重开持续黑屏，暂停安装。**
> [故障与恢复记录](BOOT_FAILURE_005.md)优先于本页历史交付状态。
> 本页通过项仅保留其构建/离线范围，不能作为实机启动验收。

2026-11-01，用户明确要求“编译可刷机固件”。本次已生成实际E-P7 SD安装目录、原厂
回刷目录和独立ZIP，进入用户可手动进行实机测试的阶段。交付范围是实验刷机包；
没有把相机启动、画质、物理更新入口或独立恢复改记为已验证，也没有操作相机。

## 交付文件

目录：`generated/ep7/flash-packages/EP7HSL-005-EXPERIMENTAL/`

|产物|实际大小|
|---|---:|
|`EP7HSL-005-EXPERIMENTAL-SD.zip`|82,790,298B|
|`install/DCOLYMP/E1429999.BIN`|111,017,984B|
|`restore-stock/DCOLYMP/E1429999.BIN`|111,017,984B|

ZIP包含10个成员：两个BIN、README、manifest和6份构建/执行证据。所有成员CRC和
解压后字节比较通过；两个BIN及其他文件落盘回读一致。ZIP外的`delivery-check.json`
记录最终交付核对。用户操作见[随包说明原稿](EXPERIMENTAL_SD_005.md)。安装与回刷
目录分开，只选择其中一个DCOLYMP复制到卡根目录。

## 构建与验包

1. `generated/ep7/flash-build-005/`复用106个已编译对象，重新整体链接/合成；当前
   实现源、头文件、编译配方相对候选005没有变化。98补丁、36 veneer、8KiB初始化
   状态与完整原厂启动前缀检查通过，CPU2保持32槽。新decoded main与此前通过
   GUI/worker/加载检查的候选005逐字节一致，因此不重跑这些功能测试。
2. 最终111,017,984B五组件容器实际执行原生更新器mode2，686,924,203条指令后
   返回0；全部解码缓冲区与fishcu解析结果一致，没有提出写入请求。随后在同一组
   解码缓冲区上运行mode1，1,556条指令截获五项原生写入路由；后端错误3102会停止
   后续flash请求。console、service与flash后端仍为显式模型，没有实际擦写。
3. `tools/ep7_sd_test_package.py`复用既有`ep7_candidate_package.package()`和fishcu
   parse → replace_payload → reconstruct；重新核对最终ELF/补丁/五组件，并要求
   输出字节与上述原生验包输入完全相同，才生成SD交付目录和ZIP。
4. 原厂回刷文件与原厂五组件输入完全相同。保留五组件及独立版本，不引入PEN-F的
   E122名称、两组件裁剪、持久化或其他未请求功能。

本轮使用原生加和、直接字节比较及ZIP CRC，没有SHA校验。构建/验包输入只读；
没有复制到真实卡、连接相机、创建tag/Release或发布固件二进制。Git仅提交源码、
文档及检查记录，固件和ZIP保留在本地generated目录。

## 证据

- [新链接构建](../../research/ep7/flash-build-005.json)
- [最终完整原生验包及路由](../../research/ep7/candidate-005-final-updater.json)
- [SD交付manifest](../../research/ep7/experimental-sd-005.json)
- [ZIP与文件回读](../../research/ep7/experimental-sd-005-delivery.json)

旧候选报告的NONINSTALLABLE和installable:false保留为离线阶段记录，不回写历史。
本交付的`manual_sd_test_package_ready:true`表示实验SD产物已完成；
`hardware_validated:false`和`independent_recovery_proven:false`仍明确保留。
原厂回刷依赖更新路径存活，不是本机备份或独立救援。E-P7物理OK+开机/AF指示尚待
现场确认，说明明确区分本机软件证据与fishcu其他机型的实际经验。
