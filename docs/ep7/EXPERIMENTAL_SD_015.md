# EP7HSL 015 H/L 增强试用版

2026-11-07，适用于 E-P7 原厂 1.1 / build 1100。

014 实机反馈为实时取景与 JPEG 的 H/L 变化都偏弱。014 使用了 PEN-F 的 ±1 至 ±5 系数。
015 将 E-P7 色轮的 ±4、±5 分别映射到 [PEN-F 的 ±5、±7 系数](https://github.com/fishcu/oly_fw_analysis/blob/main/patches/hsl/pen-f/src/image_parameters/image_parameters.s)。

| 色轮档位 | H 系数绝对值（014 → 015） | L 系数绝对值（014 → 015） |
| --- | ---: | ---: |
| ±4 | 4,000 → 5,000 | 150 → 200 |
| ±5 | 5,000 → 7,000 | 200 → 300 |

±1 至 ±3 用于细调，系数沿用 014。已有 COLOR 预设可直接读取，其中 ±4、±5 会应用更强的效果。
使用包内 `install/DCOLYMP` 更新。需要回到原厂时使用 `restore-stock/DCOLYMP`，每次只将一套 `DCOLYMP` 放在 SD 卡根目录。

可选一个色彩鲜明的主体，分别比较同一色区 H 与 L 的 0、+5 和 −5，观察取景并拍摄 JPEG。
包内证据记录了 014 到 015 的系数表字节对照、取景和成片路径的模拟输出以及封装验证。实际画面幅度由机身确认。

## English

E-P7, based on stock firmware 1.1 / build 1100.

Camera feedback on 014 reported subtle hue and lightness changes in live view and JPEGs. In 015, the E-P7 wheel's ±4 and ±5 use the [PEN-F coefficients](https://github.com/fishcu/oly_fw_analysis/blob/main/patches/hsl/pen-f/src/image_parameters/image_parameters.s) for ±5 and ±7. The peak coefficient magnitude rises from 5,000 to 7,000 for hue and from 200 to 300 for lightness.

Steps ±1 through ±3 keep the fine adjustment scale. Saved COLOR presets load as before and apply the stronger curve at ±4 and ±5. Use `install/DCOLYMP` to update or `restore-stock/DCOLYMP` to return to stock. Place one `DCOLYMP` folder at the root of the SD card per update.

The included evidence covers the byte comparison against 014, the simulated preview and capture coefficient output, and the SD package checks. Compare 0, +5, and −5 on the camera with a colorful subject to assess the visual strength.
