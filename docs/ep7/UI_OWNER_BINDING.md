# G4：显示 owner 捕获与撤销接合

`ui_owner` 已把完整 screen manager 的调用前/后，以及显示 owner 的 cleanup、bulk
cleanup、析构接入已有 native text lifecycle。现在有具体的来源限定回调，创建时使用
自有112字节资源、实际 child-ID 查询和原厂 allocator selection。该初始节点只写空文本；
[显示接合](UI_VIEWER_JOIN.md)现已增加MVC frame更新和原生setter
保护。真实输入和gating尚未绑定，也没有启用完整 `renderer_ready` 或安装hook。

## 登记与保留责任

`ep7_native_ui_owner` 为永久、初始清零的196字节目标存储。首次合法完整 manager
调用固定 GUI task 的 tid/domain/TCB/entry/stack 与 service；除 `started` 外均只允许
该 GUI task 使用。TCB 比较不是跨任务锁、存活 lease 或同址重建的证明。

1. 调用前取消 `active`，递增 generation，保存深度 token；保留旧 owner/child。
2. 原厂完整 manager 执行创建、bind、旧页面回收和发布。嵌套 busy 拒绝不能登记外层
   尚未完成的 owner；切换期间不向旧页面继续显示。
3. 原厂返回0且当前 owner 未变，只能恢复先前已经成功显示的 child；首次 setter
   失败的 child 即使 `bound=1`，也不能因此变成可显示。失败路径不重复创建。
4. 完整 request278 返回1且没有未清责任，才从 service+416 取刚完成发布的 owner。
   核对 type6111、ID0112、parent、context6/slot0或1、槽占用、list vtable60f94aa0。
   来源是刚返回的原厂分配/bind/发布链；这些字段比较不是任意指针资格检查。
5. 准备独立 descriptor/layout，调用现有 `ep7_text_native_open`。其 qualifier 仅在
   `opening` 且 manager 深度归零、相同 task/service/cohort/current owner 时通过。
   只有 attach/bind/set 全部接受才设置内部 `display_ready/active`。

generation 到 `UINT32_MAX` 永久停止新准入，仍处理旧资源。重入切页或销毁发生在
text busy/opening 中，以及已开始后的 task/cohort/service 不一致，进入现有
`quarantine.s` 终止保持实现；不会继续原厂 free。真实异常处理行为仍须 G6 验证。

## 三个销毁边界

撤销只匹配所记录的 owner，旧页面后续析构不能清掉新页面。cleanup 或 bulk 入口
在原厂遍历/释放 child 之前撤销 attached 句柄，child 仍由原厂父列表负责释放。
若直接到析构且仍记录 attached child，则拒绝继续：原厂纯析构只释放列表节点，
不能把它误当 child cleanup 后丢掉所有权。

未 attach 的 fresh child 先重试既有 rollback；拒绝时保留完整 fresh 来源与永久资源
存储，不独立 free、不重复创建。当前实现可在下一次完整 manager 返回后重试；该
软件分支不访问已经退出的 owner。**原生部署前仍须证明对应 allocator/pool 在保留
期间不被 reset/free/recreate**；仅 owner 不再引用该 child，不能证明 pool 存活。
本批主机 fixture 只验证记录未丢失与恢复流程，未证明此原生生命周期条件。

## 原生桥与安装组

|待安装方法|原厂完整入口|原厂自身帧|桥自身帧|
|---|---|---:|---:|
|service60faaab4 +784|60d37b53|64|64|
|owner61032f10 +152|60d43d4b|36|48|
|owner61032f10 +432|60d42d69|32|48|
|owner61032f10 +0|60d7ab79|4|48|

四个桥以 CALL `[],0` 调用完整自建帧入口，不跳进函数中部。manager 桥保存原输入
A0/D0/D1/A1，以及原返回的四个 scratch 寄存器；retire 桥恢复原输入后才调原厂。
析构返回 A0 的 deallocator 不被后续 C 调用破坏。独立记录16字节，位于桥栈+12。

`cohort.c` 读取上述四个实际表项，全部等于本组桥才允许首次登记；不使用可随意
置真的 enable 参数。四个词相等仍不证明安装顺序、source 映射、GUI 排他、方法
直接调用/内部入口的旁路闭包或 service/pool 存活。G6 必须在冷启动安装这些表项和
独立存储，并完成这些证明；当前没有写表、修改原厂方法或给表项指定新地址。

## 初始 owner 节点验证

以下保留初始范围与尺寸，当前组合代码/检查见[显示接合](UI_VIEWER_JOIN.md)。

- [原厂证据](../../research/ep7/ui-owner-binding-current.json)：30条精确指令、4项
  vtable 数据；新增检查 header 的 descriptor→object type/ID 写入、list vtable 与
  四个完整入口的帧责任。发布/回收顺序沿用前两批已检查证据，未重跑全部旧窗口。
- [主机结果](../../research/ep7/ui-owner-binding-host.json)：12组 strict/ASan/UBSan
  场景，实际组合 owner/cohort/native lifecycle/rollback C；覆盖失败切换、旧/新
  页面和地址复用、fresh 保留、显示失败、嵌套调用、错误身份、bare destructor 与
  generation 耗尽。原厂 leaf、资源构造器和 manager 执行均为 fixture，非原生执行。
- [目标对象](../../research/ep7/ui-owner-binding-target.json)：21对象通过；owner C
  1550字节代码/196字节BSS，cohort63字节，四桥197字节/73条指令/9项重定位。
  enter/leave/retire 局部帧为48/68/28；尚未计算包含原厂被调函数的最坏总栈。
  剩余19个符号都是原厂函数或数据地址，没有把它们解析为假地址。

复现入口：`ui_owner/check.py`、`tools/ep7_ui_owner_binding.py`、目标检查器
`--ui-owner-only`。没有 SHA 校验、原生链接/执行、整体固件编译、安装或相机试验。
MVC/session与viewer接合已推进；下一项为原生input/provider与gating，再汇合G1/G6。
