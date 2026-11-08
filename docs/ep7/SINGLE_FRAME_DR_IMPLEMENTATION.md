# E-P7 JPEG 高光映射实施记录

2026-11-08。当前主方案已按用户更正改为 **保持曝光与采集增益不变的 JPEG 高光映射**。旧富士式增益方案停止推进，见[归档](SINGLE_FRAME_DR_GAIN_IMPLEMENTATION_ARCHIVE.md)。当前行为以[修订设计](SINGLE_FRAME_DR_DESIGN.md)为准。

## 当前候选

**023 当前候选（2026-11-08）：**022 实机报告 `V42 P72`，成片效果偏弱且有
色阶。OFF 半按没有期望效果，200 和 400 半按各自正确。022 的状态码未区分
底表。023 把三组 12-bit RGB 表在原厂亮度 3968 的压缩量对齐为 168/336，
用斜率递减的肩部替换 022 的反翘尾部，保留白端 4095。原厂亮度曲线继续应用。
成功码按底表拆分，继续复用既有状态字和画面布局。见 [023 说明](EXPERIMENTAL_SD_023.md)。

六张表的亮度锚点、端点、逐节点强度及肩部斜率通过构建检查。定向回放覆盖三种
底表、换键、缓存复用和原厂上传。另以类型 16、原厂高光 +7 的显式请求回放
`6034fcd2 → 603b0a70`，OFF/400 的亮度表 512 B 完全一致。最亮 12 个节点每步
只升 1 个 10-bit 码，说明原厂亮度曲线本身也能压缩亮端级差。未测得机身本次
使用的原厂高光值。

023 实验 SD 包已通过既有原厂加载、五组件加和、升级器路由与失败停止和 ZIP
回读，最终镜像等于定向回放候选。交付为
`generated/ep7/flash-packages/EP7HSL-023-EXPERIMENTAL/EP7HSL-023-EXPERIMENTAL-SD.zip`
（82,752,118 B，13 文件）。机身启动和图像效果待实测。

**022 历史版本（2026-11-08）：**用户在 021 返回 `V42 P91`，预览及 JPEG 无
变化，但对焦过程中能看到期望的 HDR 画面。曲线强度保持 021，不把 AF 期间亮度
变化直接当作经过像素验证的映射证据。

确认 HDR UI 原先只写 ACTIVE/typed queue 并重绘，没有 COLOR 处理刷新通知。
现在 `ui.c` 在成功改档／复位后复用 015 `_ep7h_refresh`，其 profile 0..3 调用
`602b5e91/602b5eaa/602b5ec3/602b5edc`，原厂确认当前 profile 后进入 `602b8916`。
不修改 015 源码，构建器绑定其已安装符号；调用在设置临界区之外，入队之后。

`highlight_gamma.c` 将资格判断改为 COLOR 源采样器传入的冻结等级。非 COLOR
源及新构造 job 清零；后续请求键可变化，不再按 request+8!=000b0000 拒绝。
双向 owner/回调、类型 0/16、family 1/2、特殊标志、等通道与三张白名单原表
保持检查。新诊断 71/72 表示来源有效而内部请求键不同的成功选表。

桥接现在把 selector 状态作为第三个 GCC 参数，位置为 caller SP+12，已按最终
反汇编的 callee 下移 44B 后读取 SP+56 核对。初次测试发现误放 SP+4 导致未选 HDR，
已在交付前修正并重新执行 RGB 定向回放。selector=0 只记录 C0；与恢复原始
603ae830 指令的参考执行比较 context、cache、outputs 字节相同。

实际实机 P91 的键值未被记录，AF 与普通预览切换也未完整复现。上述缺口修复与
本地回放不能替代实际调度或 JPEG 验收。见 [022 交付说明](EXPERIMENTAL_SD_022.md)。

022 最终镜像的五份定向回放均通过；最终重编与该候选逐字节一致。原厂加载器、
两份 ELF 叠加、五组件加和与回读、原厂 mode1 路由及失败停止、ZIP 回读通过。
`generated/ep7/flash-packages/EP7HSL-022-EXPERIMENTAL/EP7HSL-022-EXPERIMENTAL-SD.zip`
为 82,753,693 B，13 文件，两份 BIN 各 111,017,984 B。final build 保留源码快照；
代码 11,126 B、状态 184 B；没有 SHA、相机写入、commit 或 push，015 基线未改。

**021 历史版本（2026-11-08）：**用户返回 020 的 `V42 P90`，仍无明显 HDR 效果。
V42 仅证实最近取景配置选中 400 表；P90 共用模式键、请求类型及来源判断，不能
单凭此码确认哪一项失败。已确认原厂 `603aaced` 的 0/16 两种类型与 family 1/2
均进入 `603b17e6` / `603b1819` → `603b1466` → `603ae80d`；020 错误排除了
16。021 接受 0/16，保留类型 3 等转换阶段的回退，拒绝码分为 91/Ex/Fx。

`ep7_highlight_gamma.py` 改为有理肩部加正二次尾部（T=16），节点 0–48、端点、
单调与不增亮约束保留，所有计算在构建期完成。三组 400 最大压缩为 687/279/235，
200 为 344/140/118 个 12-bit 码，不能作为真实 EV 或 JPEG 效果证明。

新增回放执行实际原厂类型分发、类型 16 RGB builder、Ex/Fx 回退；执行原厂
`60346e37` 上传到 `9f00a400` / `9f00d000` 的模拟 RAM，逐项核对 256 个表值，
覆盖缓存复用与切档刷新。第二 bank 可在相同身份且无 dirty 时跳过 RGB，第一
bank 原厂逻辑仍会强制更新；没有修改该行为。互斥服务 603b30e7/603b3109 以明确
RET 服务边界代替，其余上传指令原样执行。没有新增硬件上传钩子或真实硬件写入。

候选 `generated/ep7/highlight/021-candidate` 的五份必要回放均通过，显示版本
`1.1v021`；完整变更及诊断见 [021 说明](EXPERIMENTAL_SD_021.md)。尚未完成本版
实机 JPEG 和关机保存验收，020 的 P90 也尚未被实机细分到具体字段。

021 交付封装通过：最终 `generated/ep7/flash-build-021` 镜像逐字节等于上述候选，
既有加载器、两份 ELF 叠加、五组件加和、原厂 mode1 路由与失败停止、ZIP 回读
通过。`generated/ep7/flash-packages/EP7HSL-021-EXPERIMENTAL/EP7HSL-021-EXPERIMENTAL-SD.zip`
为 82,753,188 B，13 文件，两份 BIN 各 111,017,984 B。源码快照随 final build
保存；无 SHA、相机写入、commit 或 push，015 tracked 基线未改变。

**020 历史版本（2026-11-08）：**019 用户实测可调节，但 COLOR 1 预览/JPEG
无明显 HDR 效果；原厂高光／阴影与 Midtone 正常。用户随后将范围明确收敛到
COLOR，因此只启用 COLOR1–4，其他模式渲染保持原厂；未新增 Natural 转换挂点。

定位并修正 `highlight_gamma.c` 对 request+1524 的无条件拒绝。原厂 selector
`603ae386..603ae3c0` 会校验复用表的 variant，随后取其首个 RGB 指针；不匹配时
回到普通选择。020 在原厂成功选择后仍检查请求归属、标准灰阶、特殊标志、RGB
一致性及三张已知 ROM 表，替换本 job 的指针，不修改复用对象。019 的相同输入在
新增原生回放中失败（错误回到原表并触发重建），020 的拍摄／预览复用分支及缓存
复用通过。还覆盖 variant 不匹配时原厂回退与未知 identity 表保持不变。

`highlight.c` 增加 24 B 只读用途的阶段观测；HDR 页在既有 26 个 UTF-16 字符区内
显示 `Vxx Pxx`。切档清除，重新进入时显示后续源快照／job／RGB 结果，不增加定时器
或控制路径依赖。并发记录仅代表最近观测，不是像素完成凭据。CPU 0/1 完整 UI、
最大长度及非零状态码显示回放通过。新候选为 `generated/ep7/highlight/020-candidate`，
五份必要回放通过，版本文字为 `1.1v020`，强度保持 019。见 [020 说明](EXPERIMENTAL_SD_020.md)。

020 已完成交付封装，最终 `generated/ep7/flash-build-020` 镜像与测试候选逐字节
一致；原厂加载、两份 ELF 叠加范围、五组件、native mode1 路由和后端失败停止、
ZIP 回读均通过。`generated/ep7/flash-packages/EP7HSL-020-EXPERIMENTAL/EP7HSL-020-EXPERIMENTAL-SD.zip`
为 82,752,758 B，13 文件，两份 BIN 各 111,017,984 B。`delivery-check.json`
为 passed。保存当次源码和回放脚本；没有 SHA、相机写入、commit 或 push，015
tracked 基线保持不变。019 复现失败日志留在 020 候选目录，不覆写 019 的原证据。

随后更正 COLOR 操作说明，包内仅替换 README，ZIP 更新为 82,752,930 B；重开
两份归档逐文件回读确认其余 12 项完全相同，包括两份 BIN。delivery-check 标明
documentation_only_revision 和 firmware_binary_changed=false，仍无需重刷固件。

曲线计算发现 400 的三种最大压缩为 61/72/153 个 12-bit 码，旧版本强度偏保守；
本次不把该数学差值当作实机原因，也不据此承诺 JPEG 动态范围增加。实际所走路径及
上传/像素仍待 V/P 状态和实机结果。用户指出 COLOR 没有手动“灰阶标准”入口，
此前安装步骤混淆了内部处理条件与菜单操作，已纠正。内部键 8eb9/9961 仍影响
UI 的 N/A 提示，实际映射还检查 request+1797；没有根据菜单不存在就推断这些
内部值恒为零，也不要求用户修改它们。若出现相关拒绝，由固件侧继续定位。

**019 历史版本（2026-11-08）：**用户反馈 018 原因码 `0010`，对应 `622484fa`。
原厂 `602b35a4` 首入在 `602b35d2` 置 1，于 `602b36d4` 返回而不清除；
`602b36d7` 是独立结束函数，不是前者收尾。此前将此会话状态当作 busy 是实现错误。
公开进入调用 `602af922/602afbd9` 与独立退出调用 `602afbf1` 也支持该区分。

019 从 selected/display readiness 与诊断中去掉该持续状态，保留原值及其原生生命
周期；新增 `602b35a4` / `602b36d7` 整段 epoch 包装（原 CALL frame 分别为
`[d2,d3,a2,a3],32` / `[],4`）。精确重放各 7 B 入口，分别回到 `602b35ab` /
`602b36de`，覆盖内层 bank copy 前后通知；原内层及其他 bank 包装、写抑制、HFW
guard、队列稳定性检查不变。诊断位 0010 停用。

`generated/ep7/highlight/019-candidate` 已通过五份定向证据：CPU 0/1 UI 回放先执行
真实外层 enter/re-enter/leave 控制流（原生通知与内层模式体是边界），覆盖内层返回
0/非 0，检查 frame、参数、深度 1/2 和退出清理；随后保持原厂标志 1 完成全部 UI
流程。设置与 owner→gamma 回放也始终保留该标志，验证不是仅修复显示。版本为
`1.1v019`；本地通过不等于 019 实机通过。见 [019 安装说明](EXPERIMENTAL_SD_019.md)。

019 已完成封装：`generated/ep7/flash-build-019` 与五份定向回放覆盖的候选镜像
逐字节一致；原厂 loader、完整 overlay、五组件、native mode1 路由与失败停止检查
通过。交付包 `generated/ep7/flash-packages/EP7HSL-019-EXPERIMENTAL/EP7HSL-019-EXPERIMENTAL-SD.zip`
为 82,752,681 B、13 文件；两份 BIN 各 111,017,984 B。ZIP 回读通过，
`delivery-check.json` 为 passed。保存源码和回放脚本快照；未做 SHA、相机写入、
commit 或 push。所有 015 tracked 基线文件保持不变。

**018 历史定位版：**017 经用户实机确认可进入页面，但持续 Unavailable，等级拨轮
不可调；不能把 CPU 1 回放中复现的两页循环当作全部根因。018 新增只读
`ep7dr_settings_blockers`，将原厂 busy、三核 bank epoch、typed queue 等原因位
绘制为 `HDR unavailable: XXXX`，不改变等级读取、写入或拍摄守卫。
`generated/ep7/highlight/018-candidate` 是本轮候选，版本显示 `1.1v018`。
当时为取得实机状态的定位版，不宣称 HDR 已修复；后续 0010 定位见上方 019。

018 已封装到 `generated/ep7/flash-packages/EP7HSL-018-EXPERIMENTAL/`，ZIP 为
82,751,808 B，含 13 个文件。CPU 0/1 原因码与输入回放、设置、gamma、版本显示、
原厂加载、封装和升级路由检查通过；最终镜像与已回放镜像逐字节一致。
`delivery-check.json` 为 passed。未执行 SHA 或相机写入；用户随后反馈 0010。

**017 更新（2026-11-08）：**用户实测 016 在各曲线入口按 INFO 只在原厂两页循环。
本轮在 CPU 1 回放复现；016 UI、构造／清理及 setter 均有未经实机验证的 core-0
限制，旧 UI 夹具只提供 core 0。017 去掉 UI 的该限制，保留 native 对象归属，
采用非零核原厂 typed producer/consumer。CPU 0 ACTIVE 根为 `6250ba00`，非零核
使用其 `a250ba00` 别名，避免原厂 setter 的地址域拒绝；native 队列与 kernel 调度
完成边界仍不等于实机调度验证。GUI 可显示已提交队列中的当前等级，但 capture
必须继续等待 queue 清空；设置忙碌不再隐藏 HDR 页。

017 的工作候选是 `generated/ep7/highlight/017-candidate`。`ui-probe-core0.json`
和 `ui-probe-core1.json` 覆盖相同 INFO／双拨轮／复位／触摸／销毁流程，另覆盖 busy
时仍显示 HDR 及拒绝写入。CPU 1 测试执行原厂 typed producer，再在 GUI 重绘后执行
core-0 consumer；未完成写入时拍摄 getter 返回不可用。最后镜像的 settings 与
owner→gamma 回归通过。没有委派其他代理，也没有 SHA。

新增 `version.c/s` 模块。原厂版本 record 的 8 B 字段保持，只在机身当前版本的
两个原生 text setter CALL（`60d7f271` / `60d7f2cd`）把 `1.1` 替换为只读 UTF-16
`1.1v017`；其他版本及空值继续原厂路径。机身文字 rect `61041f5c` / `61041f9c`
两种显示宽度均向左加宽，保留右缘与附件布局。构建器 release 参数同时生成该文字、
报告和包编号；`highlight-version-probe.py` 验证原生 CALL、文本 setter 参数、固定
record 不变及镜头版本不变。LCD 实际排版尚未验证。

以下 016 记录作为前一版保留；017 使用同一高光映射与安装封装路线，见
[017 安装说明](EXPERIMENTAL_SD_017.md)。用户已试用 016；本轮工具未操作相机。

最终交付已完成：`generated/ep7/flash-build-017` 与上述已回放候选逐字节相同；
原厂 loader、完整 overlay、五组件封装与 native mode1 路由／后端失败停止通过。
`generated/ep7/flash-packages/EP7HSL-017-EXPERIMENTAL/EP7HSL-017-EXPERIMENTAL-SD.zip`
为 82,751,676 B，含 13 个文件；安装与原厂恢复 BIN 各 111,017,984 B。
ZIP CRC 和逐文件回读通过，`delivery-check.json` 为 passed；未执行 SHA、相机写入、
commit 或 push。源码快照同时保存本轮四个定向回放脚本。

构建器：[ep7_highlight_candidate.py](../../tools/ep7_highlight_candidate.py)，复用现有 015 叠加链接器、UI 和设置机制。产物：

`generated/ep7/highlight/candidate/EP7HL-NONINSTALLABLE.decoded-main.bin`

它是不可安装的 decoded main，不是 SD 升级文件。新代码约 9.6 KB，新增状态 160 B。既有 015 HSL 尾部 24 B 保持，原生 job 构造器的 15512 B 扩为 15516 B，并清零新增 4 B。

新构建的 strategy 为 `highlight_mapping_only`。默认只编入 `highlight`、`highlight_gamma`、共享 `settings` 与 `ui`。旧 exposure、transport、gamma 的降增益及强制补偿失败实现不参与链接。构建清单和逐处原始字节检查确认：原先的曝光提交、Sv 修改、元数据分配、结果绑定、捕获属性替换、转换失败、gamma 配置／调度错误钩子都未安装。原厂曝光和增益入口保持 015 字节。

## 初版曲线与逐帧配置

下表为初版 016 数值。生成器直接读取本地 ROM 三组 Normal Gradation 曲线。
初版保留前 49 个节点，用单调有理肩部渐进到 4095，200 在原厂和 400
之间等权混合。当前版本见上方候选记录和[曲线生成器](../../tools/ep7_highlight_gamma.py)。

| 原厂 LUT | 原厂首次纯白节点 | 新纯白节点 | 200 在旧白点后留下的 12-bit 码跨度 | 400 同项 |
| --- | ---: | ---: | ---: | ---: |
| 604ede78 | 237 | 255 | 31 | 62 |
| 604ee078 | 243 | 255 | 10 | 19 |
| 604f3e78 | 237 | 255 | 13 | 26 |

这些数值是 LUT 输入节点和输出码值，**不是 EV、8-bit 成片层次数或已测动态范围提升**。实际硬件插值、上游裁剪、后续对比度和用户曲线会影响结果。彩色高光的色相／饱和度变化需像素验证。

直接复用已安装 015 的六处 helper CALL：capture sample、clone、两个 capture→job 转换，以及 live sample、live→job。新 observer 保留寄存器和参数，尾调用原 015 helper。因此 HSL 和原厂路径继续执行；新等级在各自已采样的 owner 上冻结，不在 gamma 回调读取当前 GUI。

- Capture 25 个原生池位与一个临时 clone 保存等级。模式／COLOR selector 来自已填充的 capture 字段。
- Preview 使用原生五个 980 B owner，raw mode +941、COLOR selector +944。保留原厂 +181 的 skip 语义；成功 setter 将同一 owner 的等级复制到 job。
- Normal Gradation 的 Natural/COLOR 请求和已知相同 RGB 指针才替换 LUT。其他请求保持原厂映射；不因“补偿缺失”报错或中止拍照。
- `603ae830` 的 pre-cache 入口复用原厂指针比较、输出系数和缓存失效机制；只读 LUT 不被后续切档覆盖。

曝光不再改变，因此没有用于本功能的 gain/frame 对齐问题，Auto ISO 和 AEL 直接保持原厂行为。UI 不再施加 ISO 下限。RAW 采集数据没有新增修改路径；RAW-only 可保留渲染选择，不强制切录制格式。具体嵌入预览是否走本映射尚未单独验证。

## 设置与交互

沿用 INFO：高光／阴影 → Midtone → HDR 等级 → 高光／阴影。保留 OFF/200/400，双拨轮、边界停止和 HDR 页长 OK 单项复位。重建和析构清理 HDR 子页状态；三档通过原厂 guide 文本呈现。Native gamma 兼容范围之外显示 N/A；不再显示 ISO400+/ISO800+ 门槛。

九个 native curve scope 使用 part-1 tagged word，旧／无效值解为 OFF。读写 bank 事务覆盖 core 0/1/2；早期未加载状态时 bank observer 不访问新增 RAM。已识别的 native typed setter 把非零核写入排到 core 0，consumer 写完后才推进 tail。候选在 queue 非空或 epoch 不稳定时拒绝读取半更新设置。

## 当前候选的定向验收

以下检查均已执行通过；没有 SHA 或无关全套回归：

| 检查 | 证据及实际范围 |
| --- | --- |
| 构建与曲线 | 交叉编译／链接通过；六张 LUT 的前段、端点、单调、强弱关系、无增亮和最终白点检查通过；报告在 candidate/report.json |
| 同镜像 owner→gamma | [highlight-candidate-probe.py](../../research/ep7/highlight-candidate-probe.py)：实际安装的 015 helper CALL、原生 ACTIVE getter、snapshot、原厂 RGB builder 运行；clone/200 经后续 400 和池位复用保持原值；HSL 保留；cache reuse 与 OFF 恢复；preview skip/刷新、三核只读和 bank pending 回退通过。结果在 candidate/replay.json |
| 原生设置 | [settings candidate probe](../../research/ep7/single-dr-settings-candidate-probe.py)：两组 tagged word、相邻 H1、14,152 B 原生 bank 保存召回、实际 typed consumer、三核 epoch 和未映射新增 RAM 的冷态 observer 通过。结果在 candidate/settings-probe.json |
| INFO UI | [curve UI probe](../../research/ep7/single-dr-curve-ui-probe.py) 的 `--candidate` 模式运行本次 EP7HL 镜像，原厂三页事件、释放隔离、两拨轮、长 OK、触摸隔离、重建和析构通过。Auto ISO 不再得到 N/A；HDR400 在旧 ISO800 门槛下仍显示可选项。实际文字消费到原厂 text setter 边界，非 LCD 截图。 |

这些回放中 owner RAM、job 几何、部分 GUI 服务和配置输入由夹具提供。它们不是完整相机开机、原厂 RTOS 调度或 ISP 像素执行。

## 可复现命令

复用 Docker 镜像 `rust:1.96-bookworm` 和现有只读工具链卷 `ep7-research-toolchain-20261030`，挂载仓库为 `/repo`，工作目录 `/repo`，使用 `--rm --pull never --network none`。

```text
python3 -B tools/ep7_highlight_candidate.py --prefix /work/install/bin/mn10300-elf- --baseline generated/ep7/flash-build-015 --out generated/ep7/highlight/candidate
python3 -B tools/ep7_highlight_gamma.py generated/ep7/full-input/main.decoded.bin
python3 -B research/ep7/highlight-candidate-probe.py --candidate generated/ep7/highlight/candidate --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu --out generated/ep7/highlight/candidate/replay.json
python3 -B research/ep7/single-dr-settings-candidate-probe.py --candidate generated/ep7/highlight/candidate --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu --prefix /work/install/bin/mn10300-elf- --out generated/ep7/highlight/candidate/settings-probe.json
PYTHONPATH=/repo/tools python3 -B research/ep7/single-dr-curve-ui-probe.py --candidate generated/ep7/highlight/candidate
```

## 尚未完成的验收

- ISP 前级到 RGB LUT 的输入域和裁剪余量，实际 JPEG 的高光纹理收益、中灰和色彩表现。曲线本身无法证明恢复了前级已丢失的信息。
- 完整实机取景、拍照、实体按键和 LCD、关机保存／再开机，以及新增代码／RAM 区域的机身稳定性。
- 原曲线页紧凑状态标记的位置；其他图像模式、Gradation Auto 及特殊开发路径的兼容性。

因此当前结论是“渲染方案的本地构建及定向配置回放通过”，不是完整机身或真实 JPEG 动态范围验收通过。

## 016 实验 SD 包交付

2026-11-08 用户明确要求“给我新的固件”。复用现有 Olympus 五组件容器工具、原厂 loader 回放和 updater 路由器，经[016 交付脚本](../../tools/ep7_highlight_sd_package.py)生成本地实验包：

`generated/ep7/flash-packages/EP7HSL-016-EXPERIMENTAL/EP7HSL-016-EXPERIMENTAL-SD.zip`

最终构建在 `generated/ep7/flash-build-016`，其 decoded main 与上一节已回放的高光映射候选逐字节相同。核对了已交付 015 基线、其记录的源码与两代码段 ELF、当前叠加 ELF、完整补丁范围、原始 boot prefix、原厂加载器从污染内存加载并初始化全部 8192 B 状态区域，以及已知写入范围不冲突。当前新代码 9,543 B，状态 160 B。没有重复未改动的 UI／成像回放，也没有用旧单 ELF 的 manifest 冒充新叠加布局。

ZIP 为 82,750,842 B，含安装文件、原厂恢复文件、README 和验证记录，共 10 个文件；每份固件 111,017,984 B。全部五组件原厂加和通过，四个未修改组件保持原字节，main 回读等于最终候选。原厂 updater 的 mode1 五路写入请求全部在模型中拦截，返回 0；模拟后端失败返回 0x3102 并停止后续请求。完整 native mode2 解码未重复，未做 SHA。ZIP CRC 和全部文件字节回读通过。

这是用户授权的手动 SD 实验包，不是实机验收完成。原厂恢复文件需要可用的更新入口；没有相机写入、提交或推送。使用说明见 [EXPERIMENTAL_SD_016.md](EXPERIMENTAL_SD_016.md)，包内 `manifest.json`、`delivery-check.json`（目录旁）和 `evidence/` 区分软件结果与实机未验证事项。
