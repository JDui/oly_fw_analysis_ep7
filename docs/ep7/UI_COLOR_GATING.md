# E-P7 COLOR 资格、H/L 退出与原厂类别恢复

本批把实际资格判断接到类别重建、完整 viewer 绘制和每次 parent 事件入口。
H/L 两项现在有真实 C 启用路径，只有 property111 的完整32位值为54/55/56/64、
同一已发布 runtime 仍接受新工作、六项 selector/输入 cohort 匹配、显示 owner 和
ID7e10 子控件当前有效，且至少有一个可恢复的原厂类别时才启用。仍未安装任何 hook。

## 资格与失效路径

`ui_gate/gate.c` 是扩展 mask4/5 的唯一运行时写入者，保留原厂 mask0..3。
它在 MVC busy 持有期间读取实际 mode，核对 initializer 表项和完整输入 cohort，
并用现有 `ep7u_hold_ready` 核对当前 owner 身份/成员关系。runtime/UI session serial
耗尽也拒绝新准入；短暂 core poll 失败只撤销显示 receipt，不抹掉 sector/ALL 选择。

gate 同代记录最后一个原厂类别。失去资格时先禁用 H/L、撤销 session/receipt 并尝试
清空文字，再按“当前 selector 指向的可用原厂类别 → 同代最后原厂类别 → 首个可用
原厂类别”恢复；每个候选都要求原厂 mask 为0且有当前 mode 的合法工厂参数。
cat0/3 使用固定 key111/383；cat1/2 只接受 ROM 表中的八个精确 mode。
`0x10036` 不会因截断被当作 COLOR54，也不制造原厂未知 mode 的 key0。

所有原厂 mask 都禁用或新分配失败时，保留原有56字节 H/L child，恢复 selector+86
和 remembered `61fc26ae`，保持 H/L mask 禁用、session/receipt 撤销。下一次实际 GUI
边界可以重试；不会为了退出而强行开放一个原厂 mask，也不会发布 NULL content。

显示 owner suspend 立即撤销 receipt；mask/内容归一在串行 GUI 的绘制、事件或完成
回调边界执行。直接在 owner cleanup 忙碌阶段调用其文本方法不属于此流程。
四套 COLOR 之间切换及 H↔L 保留有效 session 的 sector/ALL；离开后重新进入使用新
session serial，已捕获图像快照不受 UI 撤销影响。

## 原厂恢复路径与分配失败

原重建 `60e266a9` 先销毁 parent+80，再调用通用工厂 `60dd518e`。后者在创建器
返回 NULL 时仍于 `60dd51bf/c2/c5` 写入 +32/+36/+38，因此不能把它直接当安全恢复。
新 `ui_content/stock.c` 复用通用工厂表中的三个完整创建器，取得非空并匹配原厂
vtable 的对象后才销毁 H/L，并更新 parent/MVC/selector/remembered。

|原厂类别|创建器入口 / kind|对象大小|自身栈帧|vtable|
|---|---|---|---|---|
|0|60de33a7 / 0|144|8|61155a7c|
|1、2|60e2054e / 7|188|20|61187534|
|3|60df002e / 14|240|32|61159ea8|

这三条路径都在顶层 scalar new 返回 NULL 时直接返回。kind14 读取**三个 halfword**，
不是一个 key：原重建的相邻两个栈 word 是 `{key, mode111}`，第三个 halfword 正好
为 mode 的低16位。新适配器保留这两个 word，不传只有4字节的临时 key。
cat1/2 使用原地址 `61189278/611892b8` 的 mode/key 表；cat0 在发布后照常执行
`60e26795` 的选择状态更新。

创建前复现工厂清零 `61fc1ba8/61fc1bac`；失败恢复两项旧值，成功后复现三个
post-creator 字段清零。私有 H/L 的原厂 base destructor `60dd50d8` 仅返回 NULL，
不会在新对象创建后破坏其状态。原创建器的内部子分配与其他原厂副作用仍保留，
本批不声称修复全部原厂 OOM。stock→stock 继续原重建及其原有失败语义。

## 事件、计时与绘制边界

stock↔H/L 切换及 H/L 失效会复用 stop535 `60dd5857`、cancel537/572 `60ea15ca`，
随后清 parent 的 +16/pending state、+20/pending event、+44/pending flag、+84/wheel
feedback。只有成功进入 H/L 才清旧 stock 状态；分配新 H/L 失败不会先销毁 stock。
仅开放 H/L mask 而仍在 stock 类别时不取消原厂计时器。

原 cancel 持有其计时锁，匹配 service/id 的已占用 timer 条目后清除条目并调用
`60d102a7` 移除相应排队项。该队列清理有匹配条件，不能声称所有已到期事件都被
无条件移除。清空 parent pending state 阻止旧537通过原 handler 重放 held event；
535 stop 同时清全局 `61fc1bbc`，wheel feedback 标志也直接撤销。原厂调度时序尚未
实机执行验证。

每个 parent 事件先检查资格，包括原厂 UP/DOWN 导航。若本次9031/9032/9014令 H/L
归一到 stock，该事件返回0，并将当前完整 engine scope 标为 consumed2；同一 scope
重复进入也返回0，不能把 H/L 拨轮误送到原厂 S。下一次独立 stock 事件照常委托。
未登记 parent 保持原厂路由，已登记但关系失效/重入的对象在委托前隔离。

绘制 begin 在持有 MVC 后归一；原完整 draw 随后针对新对象执行，end 在同一持有下
刷新文本 receipt。事件/owner 完成导致的归一则通过独立 veneer 调用未修改的完整
draw `60e26ab0`，再核对 viewer+388/+392/+396/+400。一次边界不会因无条件递归 refresh
重复尝试失败的恢复分配；setter 失败导致 owner 不可显示时立即再执行一次失效归一。

新增 stock veneer 共93字节/25指令，原 draw veneer15字节/4指令。前者 GCC→native
创建器使用自身20字节和 caller frame0；postselect caller `[a2],8`；stop535 caller4；
cancel caller `[d2],8`。原 draw 自身36字节，新 veneer 自身4。局部 C `.su` 包含
gate52、stock restore44、held refresh108字节，均不代表完整 GUI/原厂下游/中断总栈。

## 本次检查与后续编译关卡

- [原厂证据](../../research/ep7/ui-color-gate-native.json)：当前 E-P7 build1100 输入的
  135条指令、7组表项通过；复用结构/加法和/回转解码入口，没有 SHA 校验。
- [host 结果](../../research/ep7/ui-color-gate-host.json)：8组真实 gate + MVC/content/
  owner/input/runtime/core C 场景 strict、ASan/UBSan 通过。覆盖四类恢复、全32位 mode、
  mask 保留、分配失败、同事件重放、owner/text 失效、token 耗尽和创建器重入。
  另运行一次受影响的既有输入/绘制回归；旧 checker 的 gate/stock 边界仍为 fixture。
- [目标结果](../../research/ep7/ui-color-gate-target.json)：51对象通过，新增29条 veneer
  指令及调用 frame/重定位核对通过；67个外部项均为已列出的原厂绑定，软件依赖闭合。
  未链接、执行或安装目标代码，也未开始整体固件构建。

入口是 `ui_gate/check.py`、`tools/ep7_ui_color_gate.py` 和目标检查器 `--ui-gate-only`。
其余 joined UI 目标模式也包含现在实际需要的 input/gate/stock 依赖；历史 JSON 不改写。
新增地址绑定为上述三个 creator、postselect、stop535、cancel、两表连续起点61189278
及 active-content global61fc1ba8；已有 input gate、remembered、原 draw 绑定继续复用。

G4 的 COLOR 启用/退出软件接口已实现。通用 chrome 仍使用原四个 stock 图标，H/L
由自有文字指示；LCD 可见性、字体布局与真实交互尚待硬件验收。G1 的捕获节点排他/
全别名释放，G2/G3 的退出、队列/任务存活和启动同步，以及 G6 的合法 ROM/RAM 放置、
完整安装顺序、cache/重定位/总栈仍是 G8 前的必需工作。此节点不开放安装权限。
