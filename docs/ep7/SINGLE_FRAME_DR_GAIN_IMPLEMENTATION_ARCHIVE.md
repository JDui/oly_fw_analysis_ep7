# E-P7 单帧 HDR200 / HDR400 实施记录

> 历史归档：这是降采集增益路线的研究，不是当前 JPEG 映射方案。
> 当前候选与验收见 [SINGLE_FRAME_DR_IMPLEMENTATION.md](SINGLE_FRAME_DR_IMPLEMENTATION.md)。

2026-11-08。执行基线为 `EP7` 上的 015，原厂 1.1 / build 1100。沿用[设计合同](SINGLE_FRAME_DR_DESIGN.md)，下列地址均为 decoded main 的运行时地址。

## 固定 ISO 单拍候选

目标端源文件在 [native_single_dr](../../prototypes/ep7_volatile_hl/native_single_dr)，由[叠加构建器](../../tools/ep7_single_dr_candidate.py)链接到现有 015 解码镜像。产物是本地 `generated/ep7/single-dr/candidate/EP7DR-NONINSTALLABLE.decoded-main.bin`。构建逐处检查 015 指令、指针及原有 24B H/L 尾部，仅额外申请并清零相邻的 4B DR 尾部。候选目前仅对明确的 Natural／COLOR、普通 JPEG、Normal Gradation、无闪光、固定 ISO400／800 条件尝试生效。200 的保守采集地板为 ISO400，400 为 ISO800，两者要求原厂当前标称 Sv 与提交的曝光记录一致。

- `StlRdy2` 在 `6029d68e` 提交前把设置和 capture 分配代绑定到本次原厂 metadata。只有最终 selector 7 的完整原厂调用祖先和对应 metadata 能降工作 Sv，临时 selector 7 和原生的其他调度路径保持原值。模拟增益校准或发布失败时，在生成 TG_GAIN 前恢复原厂计算。原厂曝光回显仍保留标称 ISO。
- 原厂工作 Sv 改动通过验证后，先给 capture 标记待绑定补偿的义务。普通 `StlTake` 的 `6029e966` 和选帧事件 `602a283c` 各自核对命令及分配代，再发布完成档位。影像 clone 保留当帧状态，kind19／`0x2001` 开发写入该 job 的尾部。采集前锁存的 JPEG 格式、画面模式及开发条件也用于同一 capture 的后续原厂属性调用。
- 若增益已降而 capture 绑定丢失，原厂 kind19 调用者收到 `0x9e02`，跳过 `603f2890` 开发和 `603f28b8` 成功后处理，仍进入原厂清理并把错误写到描述符。若对应 gamma 建表没有证明映射生效，配置、绕过和 stage-2 完成的守卫也返回同一错误。已核对的原厂处理对 `0x9e01` 有特别取消语义，候选使用 `0x9e02` 作为错误。
- INFO 接线复用 015 的曲线子项、双拨轮、长 OK 和清理事件。原厂 guide 字体同时显示三档，以括号标出所选项，低 ISO 给出门槛，已识别的不可用条件显示 `N/A`。原曲线页的两个 guide 矩形重叠，保留原有本地化文案，尚无可安全叠放的 HDR 短标。实物 LCD 与按键时序待验收。
- 九个逻辑作用域用独立标签存进原厂 ACTIVE part 1，正常模式加载、银行保存与复位沿用原厂记录。候选对相关原厂事务维护读写 epoch，旧格式或未知标签读作 OFF。普通组与 COLOR1 的原厂 ACTIVE 写入已在同镜像回放核对。物理关机保存和启动回读仍需实机验收。

[同镜像定向回放](../../research/ep7/single-dr-candidate-probe.py)在一个严格 MN10300 状态中保留 A 的 clone，再切换到 COLOR／400 并复用 metadata/capture 池位。后端开发始终消费同一帧绑定的档位。

| 回放 | TG_GAIN 两路控制字 | 成片 gamma |
| --- | --- | --- |
| A，Natural／200，提交后把 A 的选项改到 400 | 3070／3070 | A 的 200 LUT，经过 B 的模式切换与池位复用 |
| B，COLOR1／400 | 2046／2046 | COLOR 的 400 LUT |
| OFF | 3583／3583 | 原厂 COLOR LUT |
| 强制丢失 A 的结果绑定 | 3070／3070 | `0x9e02`，执行原厂错误与清理分支 |

回放运行候选中的实际桥、所有权传递、原厂元数据回写、原厂增益数学、TG 串行缓存打包及 gamma builder。RTOS 提交、属性服务、capture 池服务、结果 metadata 主体、clone memcpy、转换器主体与最终 allocator 释放使用明确的 service shell。Job 阶段表和 ISP 请求是原厂形状的夹具。故障用例运行原厂 kind19 调用者与清理函数至作业析构边界，检查未进入开发/成功分支、析构的 job 地址及描述符错误。没有运行总线或真实 ISP 像素。

取景的 AE、TG 提交、MCON 和 ISP gamma 使用另一条路径。现有证据定位到串行 payload 和 gamma 上传 bank，但缺少把已实装的 gain 和实际显示帧连接起来的回执。Auto ISO 已验证原厂 min/max 求解入口和 AEL 旁路，早期求解时当前 capture 命令可为空，仍需把 AE/AEL 结果版本传给后续拍摄。两条路径未启用。 [取景证据](../../research/ep7/single-dr-live-view.md) · [Auto ISO 与 AEL](../../research/ep7/single-dr-auto-iso.md)

## 第一轮定位记录

| 路径 | 已定位 | 仍需闭合 |
| --- | --- | --- |
| 曲线 UI | 在 015 内存模型中交叉编译并回放了原生 `GUI041d` 第三页。INFO、释放、双拨轮、长 OK、触摸隔离、owner 重建与 1088 复位通过 | 原型仅限 COLOR1，档位存于模拟器。最终文案、状态提示、正常退出与持久化尚未接线 |
| 作用域 | 已核对 9 组作用域和候选 ACTIVE part 1，原厂写读、两 COLOR 档位、bank 整份复制及两条定向复位在 MN103 回放通过 | 核实 bank 中间状态与曝光冻结的串行化、机身关机保存、UI 和成像连接 |
| 曝光 | 原厂 AE 的 `A04A` 通到普通 STILL 的命令元数据。严格 MN103 已把独立工作 Sv 沿原厂数值链回放到 TG_GAIN 串行载荷 | AE/AEL/Auto ISO 前置锁存、标称 ISO 与实装增益的对应、实际生效与 RAW metadata 传播 |
| ISP | 独立 RGB gamma 与亮度曲线、缓存和 MMIO 上传已定位。六张 2×/4× LUT 数值通过，原厂 gamma builder 回放通过 A/200、B/400、OFF 与缓存回退 | 将与采集一起冻结的等级传到 JPEG／取景，处理原生早期截断和 Gradation 约束 |

现有 015 的 H/L 捕获快照用于后处理，不能据此判定采集增益写入时序。原生曲线和 H1 按各自字段继续追踪，`compact+2116/+2117` 保持原厂字段语义。

## 本轮证据与产物

- [曲线 UI](../../research/ep7/single-dr-curve-ui.md)复用实际 015 GUI 状态机与原厂曲线子控件，实验 veneer 只注入私有模拟器内存。命令、八个窗口及模拟边界均随证据保存。
- [设置](../../research/ep7/single-dr-settings.md)复用原厂 ACTIVE、bank、reset 与存储记录结构。9 个候选字段的原生回放结果在[设置探针记录](../../research/ep7/single-dr-settings-probe.json)；已有 H1 不重叠。
- [曝光](../../research/ep7/single-dr-exposure.md)与[标定](../../research/ep7/single-dr-calibration.md)记录名义 Sv、校准 Sv、数字乘数和 TG_GAIN 的分离。夹具固定名义 Sv Q8 为 1792，单独将工作 Sv 降 256／512，两路控制字 `3070 → 2046 → 0`，原曝光 Tv/Sv/Av 回显和 Q16 乘数保持原值。原厂串行数据字节同步变化。还回放了 Sv4 和 Sv8，区分 ROM 标定与机身 FLASH。仿真边界是缓冲写入，实际快门与总线时序待验证。
- [ISP 路径及数值原型](../../research/ep7/single-dr-tone.md)记录真实选表、缓存比较、硬件配置，以及[离线 LUT 工具](../../tools/ep7_single_dr_gamma.py)验证的中间调、shoulder、端点和 OFF 字节保持。[gamma 定向探针](../../research/ep7/single-dr-gamma-probe.py)交叉编译 124 字节 veneer，在原生缓存比较前选择请求私有档位。A 的输出在 B/400 和 OFF 后逐字节保持，OFF 的缓存、输出和返回寄存器与原厂对照相同。档位来自明确标注的请求夹具。
- [冻结与传递接线](../../research/ep7/single-dr-owner.md)汇总原厂 96B 曝光记录、两处 engine 提交、selected event 回读、kind19 后处理、015 H/L 与 bank 的所有权约束。

复用已安装的 Docker/MN103 工具链，未做 SHA 校验。当前交付是研究源码和模拟器原型。最直接的采集变更候选是 `6012e6ef` 之前的工作 Sv，最直接的映射候选是 `603ae830` 原厂缓存比较之前。`StlRdy2` 先提交传感器命令才运行 015 H/L 采样，现有两个原厂 bank 守卫也有静态覆盖缺口。把两处接入同一不可变捕获身份、接通取景以及验证 AE/AEL 与 bank 中间状态是当前固件集成的放行条件，因此没有生成可刷 SD 候选。

## 备选合同，供原对话审查

现有证据显示原厂支持独立模拟增益控制，优先路线仍有继续推进的依据。如果后续确认特定硬件模式无法同时保住模拟增益与成像映射，备选限定在受支持的 P/A/S 单拍 JPEG 或 RAW+JPEG。它通过原厂曝光求解安排短 1／2 EV 的实际光子曝光，再接同一类中间调补偿与高光压缩。用户 EV、标称 ISO 属性和 AEL 继续按原厂方式保存，Auto ISO 不得在曝光减少后自动抵消保护。低 ISO 资格由可用快门／光圈余量决定。M 固定、没有足够曝光余量、取景无法同步等情形保留选择并显示不可用。采用备选会改变快门或光圈，需先更新设计与验收合同。当前原型只验证独立增益路径。
