# EP7HSL 016 高光映射实验版

2026-11-08，适用于 E-P7 原厂 1.1 / build 1100，保留 015 的 HSL 功能。

016 增加 JPEG 高光映射：保持原厂 ISO、曝光、AEL 和采集增益，通过较柔和的曲线
减少高光过早进入纯白。`200 / 400` 是两档映射强度，不表示提高 ISO 或增加 1/2 EV。
当前支持 Natural、COLOR1–4 和 Normal Gradation；未验证组合显示 N/A。

## 安装与操作

1. 使用 `install/DCOLYMP/E1429999.BIN`，将这一套 `DCOLYMP` 文件夹放到 SD 卡根目录，
   按之前使用的 E-P7 SD 更新方式安装。不要把两套 DCOLYMP 同时合并到卡上。
2. 进入原生高光／阴影曲线设置，按 INFO：高光／阴影 → Midtone → HDR 等级。
3. 在 HDR 页用任一拨轮选择 OFF、200、400。INFO 回到高光／阴影；长按 OK 仅将
   当前作用域 HDR 等级复位为 OFF。原有曲线与 HSL 数值保留。

恢复原厂使用 `restore-stock/DCOLYMP/E1429999.BIN`，替换卡上的 DCOLYMP 后走同一更新流程。
恢复文件依赖机身更新入口仍可用，不是独立救砖镜像。

## 对比建议与当前状态

先用 Natural 或 COLOR、Normal Gradation，将高光／阴影／Midtone 设为 0，在相同曝光、
ISO、白平衡和构图下拍 OFF/200/400。重点看云层、窗外、反光物的高光层次和过渡，
以及肤色、彩色高光；不要通过降低曝光来代替本功能的同条件对比。
功能不会恢复采集或前级处理已经完全剪掉的细节。

本包已完成构建、同镜像参数／曲线与 UI 定向回放、原厂加载路径、五组件加和／封装回读、
升级器写入路由与错误停止检查。未执行 SHA，未重复完整 native mode2 解码。
升级器的写入请求在模型中拦截，没有操作相机。

**这是首次机身试用的实验版，尚未完成实机启动、显示、关机保存或 JPEG 画质验收。**
包内包含新固件、原厂恢复文件和验证记录。

## English

E-P7, stock 1.1 / build 1100. This experimental release retains 015 HSL and adds
highlight mapping for Natural/COLOR1–4 with Normal Gradation. ISO, exposure,
AEL and sensor gain remain stock. 200/400 indicate rendering strength, not EV gain.

Install the `install/DCOLYMP` folder at the SD card root using the same E-P7 SD
update procedure used previously. The native tone editor cycles with INFO through
Highlight/Shadow, Midtone and HDR Level. Either dial selects OFF/200/400; holding
OK on the HDR page resets only that level. Use `restore-stock/DCOLYMP` to return
to stock; it requires a working updater and is not an independent rescue image.

Software/packaging checks passed; physical boot, display, persistence and image
quality are untested. Compare OFF/200/400 at identical exposure and white balance.
