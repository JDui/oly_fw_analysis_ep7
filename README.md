# Olympus E-P7 HSL / 奥林巴斯 E-P7 HSL 固件

[中文](#中文说明) · [English](#english) · [下载 / Releases](https://github.com/JDui/oly_fw_analysis_ep7/releases)

## 中文说明

本项目参考 [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis) 的研究与实现，对奥林巴斯 **E-P7（EP7）** 固件进行逆向与修改。目前已实现 **H（色相）、S（饱和度）、L（明度）三个可切换的色轮**，沿用机身原有色彩转盘的操作方式，为各个色区增加 H/L 调节。

### 项目原则与稳定性

本项目以 E-P7 原厂 1.1 为基础，尽可能保留原生逻辑，用最低限度的改造提升机内 JPEG 直出效果。HSL 色轮和高光压制分别扩展原厂色轮与曲线，沿用机身原有操作及处理流程。改动集中在原厂 COLOR 色轮的轴切换、每色区 H/L 参数的保存与应用，并沿用原厂色轮界面、COLOR 预设和拨轮操作。打开 COLOR 色轮调节页面后，**每按一次删除键（垃圾桶键）切换一个色轮，顺序为饱和度 S → 明度 L → 色相 H → 饱和度 S**。切换后用前拨轮选色区、后拨轮调整当前轴。

已有版本在已测试的机身场景中运行非常稳定。023 新增高光过渡调整，实机直出效果仍待确认。

### 机型限制与风险

> **固件仅面向奥林巴斯 E-P7，基于原厂 1.1 / build 1100。不兼容 PEN-F、OM PEN、OM-3，以及其他带色彩转盘的机型。请勿跨机型刷入。**
>
> 目前我手里只有 E-P7，无法对其他机型进行实机验证或开发；外观、菜单或功能相似不代表固件兼容。
>
> **刷机有风险，操作需谨慎。** 这是非官方实验固件，可能导致黑屏、重启、功能异常，甚至相机无法使用。请自行评估并承担刷写风险。附带原厂返回文件，但回刷依赖相机更新入口仍可用，不保证能够救砖。

能刷到这个项目算是运气好。请不要大肆宣传、推广或引流，大家小范围内使用，解决自己的色彩问题就好。

### 当前版本

GitHub Releases 中的最新公开试用包为 **EP7HSL 023 EXPERIMENTAL**。下载 `EP7HSL-023-EXPERIMENTAL-SD.zip`。[Releases](https://github.com/JDui/oly_fw_analysis_ep7/releases)

023 保留 015 的 HSL 色轮，加入两档高光压制，并调整亮部过渡以减轻前序试用版出现的色阶。机身版本显示为 **1.1v023**。定向离线与封装验证已通过，实机 JPEG 效果待确认。[023 版本说明](docs/ep7/EXPERIMENTAL_SD_023.md)

030 本地 SD 试用版调整 Rec HDR1 的第四帧收尾，并让静音电子单张沿用原厂 HDR 合成路径。P/A/S/M 的 Rec HDR1 使用当前单张驱动的快门类型，实际成片待实机验收。[030 试用说明](docs/ep7/EXPERIMENTAL_SD_030.md)

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

建议先对同一场景拍摄 H/L=0 与修改参数后的 JPEG 作比较，并检查正常关机后设置是否保留。023 的实时取景效果请以实际机身表现为准。

### 高光压制（HDR200 / HDR400）

这两档参考富士 **DR200 / DR400** 保留亮部细节的思路。它们通过单帧 JPEG 的 RGB Gamma 曲线压低亮端、放缓向白点的过渡。在天空、白衣和逆光等反差大的场景中，亮部有机会保留更多纹理和渐变，从而改善 JPEG 直出的有效动态范围与观感。HDR400 的压制强于 HDR200。档位数字代表曲线力度，实际改善取决于场景和曝光。相机沿用原厂曝光、ISO、采集增益和 RAW 采集流程，曲线的作用范围限于前级仍保留的亮部信息。[富士 DR 参考](https://app.fujifilm-dsc.com/en/manual/x-m5/x-m5_manual_en_s_f.pdf)

1. 将前方色彩控制拨杆切到 **COLOR**，选用 **COLOR 1–4** 中的任一组。使用原厂曲线拨盘进入**高光／阴影**曲线页。
2. 按 **INFO** 循环切页，顺序是 **高光／阴影 → Midtone（中间调）→ HDR → 高光／阴影**。从高光／阴影页连续按两次即可进入 HDR 页。
3. 在 HDR 页转动前拨轮或后拨轮，选择 **OFF**（原厂映射）、**HDR200**（温和压制）或 **HDR400**（更强压制）。方括号标出当前档位。短按 OK 退出，长按 OK 将当前 HDR 档位复位为 OFF。
4. 半按快门观察取景，再拍摄一张 JPEG 查看亮部。可用相同构图、ISO、快门、光圈、白平衡和原厂曲线，依次拍摄 OFF、200 和 400，比较天空、白色物体上的纹理及明暗交界处的过渡。
5. HSL 色轮继续用删除键切轴。原厂高光、阴影和 Midtone 仍可在各自页面调整。HDR 页上的 V/P 是取景和拍摄选表诊断码，含义见 [023 版本说明](docs/ep7/EXPERIMENTAL_SD_023.md)。

### 来源与研究资料

感谢原项目 [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis) 的逆向研究、工具和 PEN-F HSL 实现参考。本仓库保留原项目历史、署名与已有许可说明；**原项目的 PEN-F 固件不能用于 E-P7，本项目固件也不能用于 PEN-F**。

[E-P7 研究资料](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/README.md) · [当前研究状态](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/HANDOFF.md) · [工具与复现](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/REPRODUCING.md) · [权利、许可与来源](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/RIGHTS-AND-PROVENANCE.md)

## English

This project reverse-engineers and modifies **Olympus E-P7 (EP7)** firmware, drawing on the research and implementation in [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis). It now implements **three switchable color wheels: H (Hue), S (Saturation), and L (Lightness)**, extending the camera's existing color-wheel controls with per-color H/L adjustments.

### Project principles and stability

The project improves straight-out-of-camera JPEGs with minimal changes to stock E-P7 firmware 1.1. The HSL wheels and highlight compression extend the original color and tone controls while retaining the camera’s native workflow. The changes focus on switching axes in the stock COLOR wheel and storing and applying per-color H/L values. The firmware retains the stock wheel interface, COLOR profiles, and dial controls. Open the COLOR wheel adjustment page and **press Delete (the trash button) once per wheel to cycle Saturation S → Lightness L → Hue H → Saturation S**. Use the front dial to select a color sector and the rear dial to adjust the active axis.

Earlier versions ran very stably in the camera scenarios tested. Version 023 refines highlight roll-off and awaits on-camera JPEG confirmation.

### Compatibility and risk

> **This firmware is exclusively for the Olympus E-P7, based on stock firmware 1.1 / build 1100. It is incompatible with the PEN-F, OM PEN, OM-3, and all other color-wheel camera models. Never flash it onto another model.**
>
> I only own an E-P7, so I cannot develop or verify firmware on other camera models. Similar controls, menus, or features do not imply firmware compatibility.
>
> **Flashing firmware carries risk. Proceed with caution.** This is unofficial experimental firmware and may cause a black screen, reboot loops, malfunction, or an unusable camera. Assess and accept these risks before proceeding. A stock return file is included, but restoring it requires a working update path and is not a guaranteed unbricking method.

If you happened to find this project, consider it a lucky find. Please avoid widespread publicity, promotion, or driving traffic here. Keep its use within a small circle to address your own color-control needs.

### Current release

The latest public SD trial package on GitHub is **EP7HSL 023 EXPERIMENTAL**. Download `EP7HSL-023-EXPERIMENTAL-SD.zip`. [Releases](https://github.com/JDui/oly_fw_analysis_ep7/releases)

Version 023 retains the 015 HSL wheels and adds two highlight compression levels with a revised roll-off aimed at reducing banding seen in earlier trials. The camera displays **1.1v023**. Targeted offline and package checks passed. JPEG output still awaits on-camera confirmation. [Version 023 notes](docs/ep7/EXPERIMENTAL_SD_023.md)

The local 030 SD trial package releases Rec's simulated shutter after the fourth frame and routes silent single-frame shooting through the stock HDR combiner. Rec HDR1 uses the shutter selected for single-frame shooting in P/A/S/M. Image output awaits on-camera validation. [030 trial guide](docs/ep7/EXPERIMENTAL_SD_030.md)

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

Start by comparing JPEGs of the same scene with H/L at zero and with adjusted values, then check persistence after a normal shutdown. Judge version 023's live-view behavior on the actual camera.

### Highlight compression (HDR200 / HDR400)

The two levels take their cues from Fujifilm **DR200 / DR400** for retaining highlight detail. A single-frame RGB gamma curve compresses bright tones and softens the transition to white in the camera JPEG. This can retain more texture and gradation in bright skies, white clothing, and backlit scenes, improving usable JPEG dynamic range and rendering. HDR400 applies stronger compression than HDR200. The labels indicate curve strength, and the visible effect depends on the scene and exposure. Exposure, ISO, capture gain, and RAW capture follow the stock workflow. The curve works with highlight detail still present at that stage. [Fujifilm DR reference](https://app.fujifilm-dsc.com/en/manual/x-m5/x-m5_manual_en_s_f.pdf)

1. Set the front color-control lever to **COLOR** and select any profile from **COLOR 1–4**. Use the camera's original curve control to open the **Highlight & Shadow** page.
2. Press **INFO** to cycle **Highlight & Shadow → Midtone → HDR → Highlight & Shadow**. From Highlight & Shadow, press INFO twice to reach HDR.
3. On the HDR page, turn either dial to choose **OFF** (stock mapping), **HDR200** (moderate compression), or **HDR400** (stronger compression). Brackets show the selected level. Press OK briefly to exit or hold OK to reset the HDR level to OFF.
4. Half-press the shutter to check live view, then take a JPEG and inspect the highlights. For a comparison, shoot OFF, 200, and 400 with the same framing, ISO, shutter speed, aperture, white balance, and stock curve settings. Compare texture and transitions in bright skies and white objects.
5. Delete still switches axes on the HSL wheel. The original Highlight, Shadow, and Midtone controls remain on their respective pages. The HDR page's V/P codes identify the live-view and capture curve selection. [Version 023 notes](docs/ep7/EXPERIMENTAL_SD_023.md)

### Attribution and research

Thanks to [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis) for the original reverse-engineering work, tools, and PEN-F HSL implementation reference. Upstream history, attribution, and existing license notices are retained. **Upstream PEN-F firmware cannot be used on the E-P7, and this project's firmware cannot be used on the PEN-F.**

[E-P7 research](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/README.md) · [Research status](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/docs/ep7/HANDOFF.md) · [Tools and reproduction](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/REPRODUCING.md) · [Rights, licenses, and provenance](https://github.com/JDui/oly_fw_analysis_ep7/blob/EP7/RIGHTS-AND-PROVENANCE.md)
