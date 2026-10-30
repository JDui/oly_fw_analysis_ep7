# E-P7 HSL：控制差异与交互提案

核查日期：2026-10-30。上游基线 `539fcf1fa9eda5fdef8ede4deeab94a4691d94c3`。这是研究与 UI 设计，不是 E-P7 已实现/已实机验证的功能。

## 先明确移植目标

E-P7 原生 COLOR 提供 **12 色区饱和度 ±5、COLOR1–4**，另有暗角、高光/阴影/中间调。手册里的 “Set the hue using the front dial” 是选择要调的色区，不表示逐色 Hue 偏移；全局 Color Creator、色调曲线也不等同逐色 H/L。目标应是保留原生 S，补每色区 H 与 L；L 的实际固件算法/系数意义须另验，不能仅凭名称保证 Lightroom 等价。官方依据：[E-P7 手册 p.51–53](https://download.omsystem.com/pages/inst/ep7/manual_ep7_ENU.pdf#page=51)。

## 实体控制对照（不是键码对照）

| 项 | PEN-F | E-P7 | 移植要求 |
|---|---|---|---|
| 色彩入口 | 前部 creative dial 的 COLOR 档；后 lever 重开编辑器 | 前部 COLOR/MONO profile switch；`u` 快捷键进入当前 profile 控制 | 不虚构 E-P7 rear creative lever；不得全局接管 `u` |
| 命令拨轮 | 前/后双拨轮 | 前/后双拨轮 | 均可原生前轮选色区、后轮调 S；事件编号仍分别确认 |
| 功能键 | Fn1、u/Fn2、放大键 | AEL/AFL、R；可自定义控件表只列 AEL/AFL 与 R | 不设计不存在的 Fn1/Fn2；不挪用录像、曝光/对焦锁 |
| 通用按钮 | OK、方向键、INFO、MENU、删除、回放 | 同类按钮；上=ISO、左=AF、右=闪光、下=连拍/自拍 | 映射只在 HSL 编辑上下文生效；退出恢复原语义 |
| 屏幕 | 触控屏 | 触控屏 | 有触控硬件不等于色轮可触控；先做实体键完整路径 |
| 色彩配置 | COLOR1–3 | COLOR1–4 | 不照搬三组 profile/存储跨度 |

依据：[PEN-F 手册 p.10–11、39、74](https://learning.omsystem.com/PEN-F/zz_pdf/pen-f_eng.pdf#page=10)；[E-P7 手册 p.12–13、33、51–52、112](https://download.omsystem.com/pages/inst/ep7/manual_ep7_ENU.pdf#page=12)。E-P7 p.12–13 已本地渲染核对实体标识；`u` 是顶面快捷键，AEL/AFL 是后部按键。E-P7 菜单/方向键不是“空闲按键”。

## PEN-F 所谓“不兼容”：证据边界

- 已确认的局部扩展：Delete 在 COLOR 色轮里切 **S → L → H → S**；INFO 保持 ALL；短 OK 退出，长 OK 重置当前轴。文档强调轴之间共享色区游标，否则下一次拨轮会从旧内部状态跳转。[上游 EDITOR.md L24–28](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/docs/color/pen-f/EDITOR.md#L24-L28)
- 代码的 `hsl_dispatch` 比较的是 **PEN-F UI 事件 `0x9016`**，不是 E-P7 已确认 GPIO/keycode；切轴还校验 editor 对象、profile、child 数及长按/计时状态。[editor.s L197–278](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/patches/hsl/pen-f/src/editor_storage/editor.s#L197-L278)
- 明确限制：不得把 COLOR 局部 Delete 映射推导成 live view/回放/菜单里全局可用；main/sub dial 的物理对应也要按 board/context 核对。[INPUTS.md L54–69](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/docs/boot/pen-f/INPUTS.md#L54-L69)
- ALL 不是逐带独立 clipping：任一色带到边界时，该方向整组停止；S 的重置是 profile 出厂默认，不一定全零。H/L 默认中性。[EDITOR.md L75–93](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/docs/color/pen-f/EDITOR.md#L75-L93)
- 已查询公开全部 issues（API `state=all`）：只有 issue #1、#3 与 PR #2，未发现 PEN-F 按键 bug 报告。因此用户担忧应保留为**待复现兼容性问题**，不能写成已证实全面失效。[公开 issues](https://github.com/fishcu/oly_fw_analysis/issues)；[完整 API 查询](https://api.github.com/repos/fishcu/oly_fw_analysis/issues?state=all&per_page=100)。这不排除站外/未提交报告。

## E-P7 新证据：Delete 仅为待资格审查候选

本机静态创建链已定位 COLOR selector 的 GUI machine 4 / state 29（`0x041d`）。
该机器的完整 112 项事件表有 OK `0x900c`、INFO `0x9014`，但**没有 Delete `0x9016`**。
这只证明该表路径没有直接准入，不排除预分发、事件重编码或直接对象调用。
因此“底层 handler 支持 9016”不等于实体 Delete 能进入当前 COLOR 面板。
原 Delete 首选方案降级为**端到端路由、modal/hold/repeat 均验证后才能启用的候选**；
可能需要 E-P7 专属的上层事件准入，不能直接搬 PEN-F leaf hook。
后续已沿具体 GUI task 检查预处理：在所审默认/门禁路径中，`9016` 被吞掉或原样传给该机器，未发现改码或直达 actuator 的旁路；这仍不是全程序或实体按键失效证明。
详见 [GUI 与 capture 后续证据](GUI_AND_REQUEST_OWNERSHIP.md)。

## 设计目标：最小单手控制 + 明示事务

右手前轮选色区、拇指后轮改数值；不要求按住某键再转轮。底栏始终显示 `COLORn | 色区/ALL | H/S/L | 数值 | 未保存`，切轴只改变编辑目标、不改变图像。实时预览与最终 JPEG/RAW 路径必须另行证明一致。

| 动作 | 建议映射与边界 |
|---|---|
| 进入 | COLOR/MONO 开关位于启用档，`u` 进入原生 profile 控制；在饱和度行打开 HSL。首次仍为 S，不能把 MONO/CRT 也重定向 |
| 选色/改值 | 前轮色区，后轮数值；保留原生档位步进、不预先承诺 ±7；一格一个可解释刻度 |
| 切轴 | **路由资格待证的候选**：仅 HSL 面板内短 Delete：S→L→H；按释放边沿单次切换、消抖，不让长按自动重复；保留共享色区与 ALL 状态 |
| 单色/全部 | INFO 切换单色/ALL；ALL 清晰显示，边界策略明示并测试，不能静默把各色差异压平 |
| 确认 | 短 OK：提交当前 profile 的整组 HSL，并退出到拍摄；显示保存结果 |
| 取消 | MENU：恢复进入编辑时的快照并退出；只有在 staging/rollback 证明后才标“取消” |
| 重置 | 长 OK 打开带范围说明的重置面板，默认“当前色区/当前轴”；可选“当前轴全部色区”“当前 profile 全部 HSL”，OK 二次确认；MENU 取消。S 选“出厂默认”与“归零”须明确区分 |
| 快门/录像 | 半按优先退出编辑、撤销未确认草稿，传递 AF/AE；全按/录像继续原有动作，使用已确认值。不得吞掉 release 或排队迟发拍摄；此路径需要原子回滚/事件转发验证 |
| 模式/开关/回放/休眠 | 离开受支持上下文，取消未确认草稿，恢复已确认值；不偷偷保存。发生于 busy/capture 时不能重入或改已捕获图像参数 |

**上述确认/取消/暂存并非原生已具备能力。** 上游原生每次值变化会走 property commit/GUI setter/settings manager；内部 `900c` 也不是物理 OK。[EDITOR.md L30–57](https://github.com/fishcu/oly_fw_analysis/blob/539fcf1fa9eda5fdef8ede4deeab94a4691d94c3/docs/color/pen-f/EDITOR.md#L30-L57) 若无法隔离预览与持久参数，就不能用“OK 保存、MENU 取消”的虚假文案，也不能靠退出时把旧值写回假装没有写入。

### 保守路线（仍待输入准入证明）

先复用原生即时编辑语义，INFO/拨轮/短长 OK 尽量不变。**局部 Delete 切轴必须先证明上层准入与完整路由，当前不能视为已可落地。**画面明确“实时应用并保存”；短 OK=完成，MENU=返回（不是撤销），不承诺快门退出会取消。按轴重置沿用可证明的原生行为；每色区/整组重置暂列待开发，不以危险隐藏组合键实现。此阶段比新增事务更小，但必须在发布说明承认无会话取消。两方案不得混搭含糊语义。

### 新的有依据备选：扩展原生类别，不强占 Delete

已核实 selector/list ID 193 的四个原生类别值为 0..3，记忆索引在 RAM，不是已证明的持久化 property。可优先研究保留 0..3 后新增 COLOR-only H/L 类别：上下键仍是类别导航，INFO 保留原生编辑器内 ALL 行为（APP 0x5704 的条件 INFO 回调也须保留），拨轮保留选色/改值角色。必须同时扩展 parent switch、viewer/标签、独立轴状态与 H/L 存储，并处理切到 MONO 时禁用类别和焦点归一化；**不是改 list count 就能用**。

[原生 selector 证据和纯主机设计测试](NATIVE_SELECTOR_DESIGN.md) 已落地；这些测试只验证提案，不是相机 UI 或 HSL 实现。没有找到可宣称可用的 H/L 触控命中区。

### 备选与不推荐

- 若 Delete 不可安全准入或已有用途：优先研究显式 H/S/L 轴选项或独立子面板，复用已准入的选择/确认路径；新 widget、焦点与导航仍须静态证明。不得把 INFO 改为切轴，也不得占用原生上下类别导航。额外子面板的左右/上下方案只作设计备选，不能假定这些键在该焦点下已兼容。
- 触摸轴标签/色区作为后续可选快捷操作，不能作为唯一入口；需验证不会触发触摸快门、AF 或拖动串扰。
- 不推荐：全局 Fn/R 绑定 HSL、INFO 同时兼任切轴和 ALL、长按 Delete 重置（与回放删除产生危险心智冲突）、按住快门/ISO 再转拨轮、通过切轴触发隐藏持久写入。

## 实施验收与阻塞

1. **完整输入资格未证实**：E-P7 1100 已有逻辑键→app→条件GUI转发和COLOR GUI上下文证据，但Delete上层准入、实体press/release/hold、拨轮与modal路径仍未闭合；不能套PEN-F地址或把表映射当实机资格。
2. **状态钩子未证实**：识别 E-P7 COLOR1–4 editor、profile 主页与 MONO/CRT/shared viewer 边界，验证所有不匹配状态回落原处理器。
3. **事务/持久化未证实**：确认 live-preview 与 settings save 边界、NVRAM 写策略、正常关机、重启、profile 切换与重置；无依据不得挑“空闲”存储区。前期仅记录可测试语义，不刷机。
4. **交互回归清单**：S/H/L × 12 色区/ALL × COLOR1–4 × ±边界；短/长/重复 Delete、OK hold+Delete、快轮滚动、半按/全按/松开、R、ISO、MENU、回放、模式改变、忙态。显示数字、轮廓与实际影像一致；只切轴不得改任何值。
5. **存储验收**：仅确认动作触发事务方案的持久化；取消/退出不写；重置范围精确；检查 restart 与 JPEG/ORF 实拍处理参数，不能以 UI 正确替代图像链路证据。

当前可以交付的是控制设计与上游风险定位；E-P7 可刷补丁、完整输入准入/路由资格、事务取消及实机验证均未完成。下一步由静态分析定位 E-P7 本机 editor/event/property 路径，再做离线状态测试；不得把设计图或 PEN-F 通过测试写成 E-P7 兼容证明。
