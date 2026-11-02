# Olympus E-P7 HSL / 奥林巴斯 E-P7 HSL 固件

[中文](#中文说明) · [English](#english) · [下载 / Releases](https://github.com/JDui/oly_fw_analysis_ep7/releases)

## 中文说明

本项目参考 [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis) 的研究与实现，对奥林巴斯 **E-P7（EP7）** 固件进行逆向与修改。目前已实现 **H（色相）、S（饱和度）、L（明度）三个可切换的色轮**，沿用机身原有色彩转盘的操作方式，为各个色区增加 H/L 调节。

### 机型限制与风险

> **固件仅面向奥林巴斯 E-P7，基于原厂 1.1 / build 1100。不兼容 PEN-F、OM PEN、OM-3，以及其他带色彩转盘的机型。请勿跨机型刷入。**
>
> 目前我手里只有 E-P7，无法对其他机型进行实机验证或开发；外观、菜单或功能相似不代表固件兼容。
>
> **刷机有风险，操作需谨慎。** 这是非官方实验固件，可能导致黑屏、重启、功能异常，甚至相机无法使用。请自行评估并承担刷写风险。附带原厂返回文件，但回刷依赖相机更新入口仍可用，不保证能够救砖。

能刷到这个项目算是运气好。请不要大肆宣传、推广或引流，大家小范围内使用，解决自己的色彩问题就好。

### 当前版本

最新版本为 **EP7HSL 014 EXPERIMENTAL**，请在本仓库 [Releases](https://github.com/JDui/oly_fw_analysis_ep7/releases) 下载 `EP7HSL-014-EXPERIMENTAL-SD.zip`。

三轴切换、数值调节和设置保存已有前序版本的实机反馈，012/013 保存的 JPEG H/L 效果已获确认。014 修正 H/L 实时取景的参数来源和轴标题填充，已完成定向离线检查与封装检查；**014 的实时取景、标题显示、切页清理和 JPEG 仍待该版本的实机确认**。具体范围见 [014 版本说明](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/EXPERIMENTAL_SD_014.md)。

### SD 卡刷入

以下是本项目在 E-P7 上采用的 SD 更新方式，不是官方安装流程。

1. 确认机型为 **E-P7**，使用充足电量的电池，先备份 SD 卡上的照片和需要保留的设置。刷入前将拍摄模式设为 **A**、图像模式设为 **Natural（NAT）**。
2. 解压下载的 ZIP。把 **`install` 目录里面的 `DCOLYMP` 文件夹**复制到 SD 卡根目录，最终路径应为 **`SD:/DCOLYMP/E1429999.BIN`**。不要把 `install` 文件夹整体放到卡根目录，也不要混入原厂返回文件。
3. 相机关机后插入更新卡，**按住 OK 键开机**，指示灯开始后松开 OK。更新过程中保持供电，不要取卡。
4. 等待 AF 指示灯从**常亮转为快速闪烁**的完成指示，再拨到 OFF。指示不符时，不要把任意等待时长当作更新已完成。
5. 关机后取出更新卡，**不按 OK** 正常开机。先确认画面、菜单和拍摄正常，再进入 COLOR 色轮测试。再次使用该卡前，请移除更新文件，避免误触发更新。

如需返回原厂，使用包内 **`restore-stock/DCOLYMP/E1429999.BIN`** 替换卡上的修改固件，按相同步骤更新。安装文件和原厂返回文件同名，**每次卡上只放一套 `DCOLYMP`**，不要混用。

### 色轮操作

1. 将机身色彩控制拨杆切到 **COLOR**，按原厂操作进入色轮调节页面。
2. 在色轮页面按**删除键（垃圾桶键）**，循环切换 **S → L → H → S**，标题对应 **Sat / Lum / Hue**。
3. **前拨轮选择色区，后拨轮调节数值**；INFO 切换单色区 / ALL。H/L 范围为 **−5～+5**，四个 COLOR 组分别保存参数。
4. 短按 OK 退出；长按 OK 复位当前轴，H/L 复位为 0。重新开机默认显示 S，切到 H/L 可查看保存值。

建议先对同一场景拍摄 H/L=0 与修改参数后的 JPEG 作比较，并检查正常关机后设置是否保留。014 的实时取景效果请以实际机身表现为准。

### 来源与研究资料

感谢原项目 [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis) 的逆向研究、工具和 PEN-F HSL 实现参考。本仓库保留原项目历史、署名与已有许可说明；**原项目的 PEN-F 固件不能用于 E-P7，本项目固件也不能用于 PEN-F**。

[E-P7 研究资料](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/README.md) · [当前研究状态](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/HANDOFF.md) · [工具与复现](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/REPRODUCING.md) · [权利、许可与来源](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/RIGHTS-AND-PROVENANCE.md)

## English

This project reverse-engineers and modifies **Olympus E-P7 (EP7)** firmware, drawing on the research and implementation in [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis). It now implements **three switchable color wheels: H (Hue), S (Saturation), and L (Lightness)**, extending the camera's existing color-wheel controls with per-color H/L adjustments.

### Compatibility and risk

> **This firmware is exclusively for the Olympus E-P7, based on stock firmware 1.1 / build 1100. It is incompatible with the PEN-F, OM PEN, OM-3, and all other color-wheel camera models. Never flash it onto another model.**
>
> I only own an E-P7, so I cannot develop or verify firmware on other camera models. Similar controls, menus, or features do not imply firmware compatibility.
>
> **Flashing firmware carries risk. Proceed with caution.** This is unofficial experimental firmware and may cause a black screen, reboot loops, malfunction, or an unusable camera. Assess and accept these risks before proceeding. A stock return file is included, but restoring it requires a working update path and is not a guaranteed unbricking method.

If you happened to find this project, consider it a lucky find. Please avoid widespread publicity, promotion, or driving traffic here. Keep its use within a small circle to address your own color-control needs.

### Current release

The latest version is **EP7HSL 014 EXPERIMENTAL**. Download `EP7HSL-014-EXPERIMENTAL-SD.zip` from this repository's [Releases](https://github.com/JDui/oly_fw_analysis_ep7/releases).

Axis switching, value adjustment, and settings persistence have on-camera feedback from earlier versions; JPEG H/L effects were confirmed for 012/013. Version 014 corrects the H/L live-view parameter source and axis-title fill, and has passed targeted offline and packaging checks. **Live view, title rendering, page cleanup, and JPEG output still require on-camera confirmation for version 014 itself.** See the [014 notes](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/EXPERIMENTAL_SD_014.md) for the verification scope.

### Installing from an SD card

This is the SD update method used by this project on the E-P7, not an official installation procedure.

1. Confirm that the camera is an **E-P7**, use a sufficiently charged battery, and back up photos on the SD card and any settings you need. Before flashing, select **A** shooting mode and **Natural (NAT)** picture mode.
2. Extract the ZIP. Copy the **`DCOLYMP` folder inside `install`** to the SD card root. The resulting path must be **`SD:/DCOLYMP/E1429999.BIN`**. Do not copy the enclosing `install` folder to the root or mix in the stock return file.
3. With the camera switched off, insert the update card. **Hold OK while switching the camera on**, then release OK once the indicator starts. Keep power connected and leave the card inserted throughout the update.
4. Wait for the AF indicator to change from **steady illumination to rapid flashing**, indicating completion, then switch the camera OFF. If the indicator behaves differently, do not assume an arbitrary elapsed time means completion.
5. Remove the update card with the camera off, then switch on normally **without holding OK**. Check the display, menus, and shooting before testing COLOR mode. Remove the update files before reusing the card to avoid an unintended update.

To return to stock, replace the modified firmware on the card with **`restore-stock/DCOLYMP/E1429999.BIN`** from the package and repeat the same procedure. The two firmware files have the same name: keep **only one `DCOLYMP` set** on the card at a time.

### Using the color wheels

1. Set the camera's color-control switch to **COLOR** and open the color-wheel adjustment page using the normal camera controls.
2. On that page, press the **Delete (trash) button** to cycle **S → L → H → S**, labeled **Sat / Lum / Hue**.
3. Use the **front dial to select a color sector and the rear dial to change its value**. INFO switches between a single sector and ALL. H/L values range from **−5 to +5**, with separate settings for each of the four COLOR profiles.
4. Press OK briefly to exit; hold OK to reset the current axis, with H/L resetting to 0. After restarting, the editor defaults to S; switch to H/L to view the saved values.

Start by comparing JPEGs of the same scene with H/L at zero and with adjusted values, then check persistence after a normal shutdown. Judge version 014's live-view behavior on the actual camera.

### Attribution and research

Thanks to [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis) for the original reverse-engineering work, tools, and PEN-F HSL implementation reference. Upstream history, attribution, and existing license notices are retained. **Upstream PEN-F firmware cannot be used on the E-P7, and this project's firmware cannot be used on the PEN-F.**

[E-P7 research](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/README.md) · [Research status](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/HANDOFF.md) · [Tools and reproduction](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/REPRODUCING.md) · [Rights, licenses, and provenance](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/RIGHTS-AND-PROVENANCE.md)
