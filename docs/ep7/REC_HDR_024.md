# EP7HSL 024 Rec HDR 实验里程碑

基于 E-P7 原厂 1.1（build 1100）和 023 的高光曲线。024 是用于离线验证的 decoded-main 候选，实机拍摄待验收。SD 卡试用包见 [023 版本说明](EXPERIMENTAL_SD_023.md)。

## 操作

1. 将模式拨盘转到 P、A、S 或 M。打开「按钮功能」，选择录像键对应的「◎功能（Rec）」，将功能设为「HDR」。可从 LV 超级控制面板进入按钮功能。
2. 在连拍/自拍菜单里选择单张拍摄、快门减震单张或静音单张（♥）。静音单张使用电子快门。
3. 全按快门键拍一张。短按一次 Rec 发起一组 HDR1，目标是以当前的快门类型拍四张不同曝光并在机内合成一张。下一次全按快门键继续单张拍摄。

Rec 的 HDR 功能适用待机的单张驱动。拍摄中、快门已半按或间隔拍摄开启时，准入检查会拒绝新的 Rec HDR 请求。HDR1 使用原厂多帧配方。HDR200/400 仍由原有曲线页单独设置。[E-P7 使用说明书，第 64、86–88、112 页](https://download.omsystem.com/pages/inst/ep7/manual_ep7_CHS.pdf)

## 固件接线

- 在 Rec 的原厂分配表（设置 ID `48`）追加功能值 `473`，复用原厂 HDR 标签和动作映射。按下事件沿原厂拍摄视图准入后进入单次拍摄 SDK。长按与松开由同一分支消费。按键映射参考 [Caduceus E-P7 按键研究](https://github.com/cakelesscoder/caduceus-ep7/blob/main/docs/BUTTONS.md)。
- 单次命令复用原厂 `1007` 事件及虚函数，独立的表指针用于区分 Rec 请求。拍摄任务在通过原厂权限检查后读取当前单张驱动，写入本次 HDR1 的三个有效属性 `600=1`、`1494=4`、`5=4`。在该拍摄对象上允许 HDR 包围类型继续通过原厂静音资格检查，电子快门仍由当前的 `764` 属性和控制器判定。正常和复位的原厂触发位清理点撤销这三个有效值。

## 离线复现与结果

在现有 GNU MN10300 工具环境下运行。`--engine` 指向本地构建的严格 MN10300 指令回放器。

```sh
python3 -B tools/ep7_highlight_candidate.py \
  --prefix /work/install/bin/mn10300-elf- \
  --baseline generated/ep7/flash-build-015 \
  --out generated/ep7/hdr-milestone-024/candidate --rec-hdr

python3 -B research/ep7/rec-hdr-probe.py \
  --candidate generated/ep7/hdr-milestone-024/candidate \
  --engine /path/to/ep7-mn103-mulqu \
  --out generated/ep7/hdr-milestone-024/candidate/rec-hdr-replay.json
```

定向回放覆盖 Rec 列表和动作选择、一次按键产生一个带标记的请求、三种单张驱动的原厂快门选择、电子 HDR 的原厂 AE 资格与四帧计数、触发位清理后的普通单帧计数，以及半按、重复请求、间隔拍摄的拒绝路径。默认 023 在同一 Python 进程内可复现为现有镜像的相同字节，023 封装器拒绝 024 实验策略。

回放模拟了 UI 服务、堆分配、请求传递和设置地址解析。需在实机确认任务域及跨核属性可见性、菜单显示与关机保存、完整曝光和合成、异常后单拍恢复。024 的输出仅用于离线研究。
