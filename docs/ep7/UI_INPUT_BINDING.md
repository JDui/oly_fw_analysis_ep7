# E-P7 H/L 原生输入与完整拨轮计数接合

本批实现 `ui_native/input.c` 和三座原生边界桥，复用原有 raw adapter、同一 runtime
core、MVC/session 和 native text lifecycle。`ep7_ui_native_admit_unresolved` 已由完整
事务替代：准入、frame 查询、编辑都在 MVC/显示 owner 持有期间完成，不返回借用的
可变 UI 指针。仍是未安装候选。本文记录输入节点的检查结果；后续已由
[COLOR gating](UI_COLOR_GATING.md)接入真实 mask 启用及失效归一，默认值仍为禁用。

## 从同一事件复制完整计数

GUI task entry `60dd5067` 调用主循环 `60cfd311`。循环把28字节事件包放在本地
`SP+396`，`60cfd53a` 以 `[d2,a2,a3],224` 调用完整预处理 `60e9fa88`。预处理返回1
就重新取包；其余结果进入 `60cfd558`，以 `[d2,d3,a2,a3],48` 调用 engine 内部入口
`60d1144d`，参数为 D0=event、A1=packet+12、D1=packet+16、A0=GUI machine。
候选只接受预处理正常返回0的子集。A3始终提供同一循环包地址。

五条来源都在调用原厂 setter `60ea3b2c` **之前从寄存器保存完整 D0**，随后照常执行
原厂 setter，再把保存值复制到私有 scope。没有在消费时重读共享 `61fc4fb8`，也没有
把 packet+12 的方向/缩小计数误当完整 delta。

|预处理原事件|原厂服务 selector|采样 CALL / 返回PC|服务状态寄存器|输出事件|
|---|---|---|---|---|
|9031|1|60ea0070 / 60ea0075|D2|9031|
|9032|0|60ea00f7 / 60ea00fc|A2|9032|
|904f|2|60ea0d70 / 60ea0d75|D2|9031|
|9051|4|60ea0deb / 60ea0df0|D2|9031|
|9050|3|60ea0e66 / 60ea0e6b|D2|9032|

这些是逻辑服务 selector，不标为物理前/后拨轮。服务必须返回0；完整 delta 限于
[-64,64]，-32768和超限输入直接拒绝。9031正数归一参数为1或2、负数为-1；9032
为正1/否则-1，最终事件/参数仍须匹配。重复 sample、未知返回PC、不同包或后来
预处理改写不匹配都不能编辑。零计数不编辑。

永久68字节 scope 只在固定 GUI task 修改：idle → preparing → pending → dispatch
→ idle。完整预处理入口检查真实 TCB stack 包含28字节包，清掉旧候选；不允许在
preparing/dispatch 内再次进入。完整 engine 入口消费 pending，核对包地址、event、
parameter、extra 和真实 `61fb2564` machine；要求 machine4/state29。完整 engine
返回必定清掉本次 scope。过期、丢弃或不匹配事件不会留给下次同址包使用。

## 真实 parent 与一次准入

engine 将当前 handler index 写到 machine+8，handler137 `60e5da87` 使用
`61fc436c` container 调用 `60e4d032`。其 virtual0 CALLS 在 `60e4d0ff`，返回PC
为 `60e4d101`、A3为container。扩展后的52字节 parent bridge 除原三项输入外，
还复制返回PC和container；owned H/L 要求这些实际来源与登记图一致。

仅9031、9032、9014进入 H/L 事务；原厂类别0..3及其余键仍调用完整原厂 parent。
一个 dispatch scope 最多尝试一次 owned 事件，即使准入或核心访问失败也不重放。
此外检查：

- engine仍为同一machine4/state29/handler137；实际 `61fc1bac` 必须为0。
  INFO在hash表 `6114041c` 有独立分支 `60dd55bb`，也要求0，不能套用普通 fallback
  的“0或相同event”条件。
- 成功setter receipt的MVC/独立session/owner代际、viewer/content、category匹配；
  selector实际index匹配且对应H/L mask确实启用。
- 持有MVC后核对实际owner和ID7e10成员，并保持text.busy直到raw dispatch结束；
  mode111仍为同一COLOR profile，viewer缓存selector/content/category/mode仍匹配。
- 同一runtime的core frame/编辑走原有poll-only锁。失败不写S，也不晚取另一个事件的值。

owned路径复现原parent的+24/event、+28/parameter和条件+36=200记录。INFO接受后
调用原厂 `60d1050a` 清掉队列中的同类事件，再经raw adapter切换 single/ALL一次。
H/L没有重建原厂INFO hold timer或S setter/reset语义。changed返回native1，由原厂
container请求完整viewer；其余返回0，释放两层持有后仅刷新文本确认。未登记对象
保持stock委托；已登记但图失效的对象在委托前隔离。

## ABI、安装 cohort 与放置要求

|桥|继承/自身帧|原厂调用|
|---|---|---|
|preprocess|继承224；局部12..47；独立保存D3|再次调用完整原厂，嵌套224；保留A0/D0/D1/A1返回|
|engine dispatch|继承48，额外20，总68；原saved f0在52..67|原厂内部入口60d1144d，caller48|
|wheel sample|自身64；sample12..31，volatile/MDR32..47，saved f0在48..63|setter caller0；恢复输入寄存器/MDR|
|parent virtual0|自身48；输入12..31、saved f0在32..47|stock完整入口60dd5250自有80|
|INFO drop|自身4|60d1050a caller `[d2,d3,a2],16`|

cohort同时核对 parent vtable `6118957c+0`、两处原宽7字节CALL及五处原宽5字节CALL
的opcode、位移、save mask、frame和目标。五条短CALL共用sample入口的起始地址
必须在 **60e98e66..60ea806f**；这不是已找到可用ROM。224+224嵌套开销、GUI循环、
全部原厂下游及中断总栈仍必须在G6计入，局部 `.su` 数值不能代替总栈证明。

新增外部名称均有原厂事实来源：preprocess `60e9fa88`、engine `60d1144d`、setter
`60ea3b2c`、parent `60dd5250`、drop `60d1050a`，三个global `61fb2564/61fc1bac/
61fc3808`，以及两处主循环CALL和表中五个setter CALL。没有用一个未实现的 admission
provider替代这些绑定；完整冷启动安装、任务存活和合法放置依然未实现。

## 本次最小验证与下一步

- [原厂报告](../../research/ep7/ui-input-binding-current.json)：178条精确指令、4项固定
  数据、5条预处理hash路由和3条GUI041d事件路由通过。复用旧事件探针的必要witness，
  使用当前无SHA结构解码入口，没有运行旧hash检查。
- [组合host报告](../../research/ep7/ui-input-binding-host.json)：8组新增输入场景，复用
  19组viewer/MVC/content场景，strict与ASan/UBSan通过。真实runtime/core/UI、held
  provider、owner/text C参与；native任务、栈extent、预处理/engine边界和绘制仍是fixture。
  覆盖全计数、正负/零/超限、失败/重复、参数/状态/代际、INFO门槛、owner失效和重入；
  编辑后的图像snapshot仍保留捕获值。mask仅fixture启用。
- [目标报告](../../research/ep7/ui-input-binding-target.json)：47对象，59个剩余外部符号
  均为实际原厂地址。新增组合桥84条指令，parent桥20条；input C1918字节+BSS68，
  cohort587字节，组合桥222字节，parent桥52字节。input route局部帧100；owner hold/
  release/present为28/16/32。未链接、未目标执行、未整体编译固件。

入口是 `ui_native/check_input.py`、`tools/ep7_ui_input_binding.py` 和目标检查器
`--ui-input-only`。旧 `ui_native/check.py` 保留历史工具验证入口，本次仅复用其纯
assembly validator；旧历史报告不重写为本次结果。

后续 [COLOR gating](UI_COLOR_GATING.md)已完成真实资格和失效恢复，当前事件边界先做
门控，归一事件禁止回落S；本文历史输入数据仍保留。G1/G2/G3退出闭包、G6 placement/
atomic install/cache/总栈以及G8准入仍保留。
