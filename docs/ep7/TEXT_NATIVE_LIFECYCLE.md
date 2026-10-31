# G4：实际文本创建、挂接与失败所有权

`text_lifecycle/native_lifecycle.c` 现将已审查的 factory、attach、bind、setter 和
fresh rollback 接入既有 `ep7_text_create_attach`，没有另写一套生命周期算法。
原生调用仍只编译为对象；具体 GUI owner 来源、资源副本、入口/退出 hook 尚未接好，
因此没有创建相机控件，也没有启用 renderer_ready。

## 两种不同的返回契约

支持的原厂显示容器 vtable 为 `61032f10`，工厂 `60d37a6f` 实际请求 **1360 字节**，
随后调用 `60d7ab3f`。其 +440=`60d037a3` 返回 owner+92 的 child list。
`60d02beb → 60d023d2 → 60d02314 → 60cfef7b` 用 allocator context5/0
分配 12 字节节点，将 child 保存到 node+8 并连接到双向链表。

- 返回 0：分配失败分支尚未写入链表，caller 继续拥有新 child，可以 fresh rollback。
- 返回 1：链表写入完成，所有权转给 parent，后续绑定或显示失败均不能独立释放 child。

文本 +148=`60d0487a` 先经 `60cfe0f8 → +124=60cfdfe0` 写 child+20=parent。
在已限定的 child+68/+88 均为 0 时，跳过两条附加回调，然后经 +564=`60d04b66`
向 parent+412 通知事件 6144。该精确 parent 的 +412=`60d7ab8c` 对 6144 走默认
**返回 -1**；这个 -1 会一路成为 bind 的返回值。

因此原生 bind 返回值不能按“==1 才绑定成功”理解。本实现同时要求预期通知结果 -1
和 child+20 确实等于 owner，才把 normalized bind 视为成功。只适用于上述精确
parent/text 类和保护字段，不能推广为其他原生 UI 方法的返回值转换。

## 具体接合与 retained 状态

`ep7_text_native_open` 在任何 owner/resource 字节读取前先核对实际 GUI TCB
domain0/entry60dd5067，再调用具体入口提供的生命周期资格回调。该回调必须证明
live1360 owner、已初始化 child list、稳定 live service、descriptor94 及嵌入引用、
font/layout 和完整串行范围。vtable 比较不能替代这些事实。ID 的实际冲突查询已随后
接入，见 [owner 生命周期与查询](UI_OWNER_LIFECYCLE.md)；查询至 attach 期间的列表
存活与成员稳定仍由具体入口保障。

之后核对精确 owner/service 类型、descriptor8010、两条 rollback guard、service
layout count=2/index=0或1。整个调用保持 owner 的 allocator selection，最后恢复
原先选择。既有 factory bridge 和 rollback bridge 各自仍保留独立恢复责任。

|阶段/结果|状态与处理|
|---|---|
|分配失败|返回 -1，没有新对象|
|初始化或 list attach 失败，rollback 完成|返回 -1，清除 fresh 记录|
|rollback 拒绝|返回 -2，保留 fresh 指针及来源；禁止新建/丢弃状态，可在合法 GUI scope 重试|
|attach 已成功，bind/set 失败|返回 0，保留 parent-owned child，绝不 fresh rollback|
|attach/bind/set 均接受|返回 1，记录 parent-owned child 和 bound 状态；不等于物理显示验收|

实际 factory 正常返回建立 fresh allocation 的来源记录。内部 rollback qualifier 仅
承认本次尚未 attach/publish/set-text 的对象；attach 返回 1 就撤销该 fresh 资格。
若 cleanup 被拒绝，原有 portable callback 的 void 返回不会丢失对象：外层保留记录
并显式返回 -2。`ep7_text_native_retry_rollback` 使用保留记录和实际 native rollback，
成功后才清除；它不会解引用可能已经结束生命周期的 owner。

`ep7_text_native_revoke` 在 parent teardown 之前清除显示句柄，不释放 parent-owned
child；存在 fresh retention/busy 时返回 0，调用方必须继续保留状态。具体入口还须
覆盖 parent 的真实销毁路线，不能从这个 API 的存在推断已安装退出 hook。

## ABI 与定向验证

`attach_bind.s` 的两个 GCC D0/D1 指针桥均自有 4 字节帧。attach 使用实际
CALL[a2],8；bind 使用 CALL[],0，由原生方法自己的 MOVM/add 创建 12 字节帧。
两桥共 10 条指令、34 字节。既有 text setter 的 5 条指令、17 字节检查器直接复用。

- [原厂证据](../../research/ep7/text-native-lifecycle-current.json)：96 条指令、
  7 个 vtable 项；涵盖 attach 失败无写入、成功链表发布、正常 bind=-1 和 setter
  使用 child 保存的 allocator bytes。未执行旧 SHA checker。
- [主机报告](../../research/ep7/text-native-lifecycle-host.json)：15 个定向场景，
  strict/ASan/UBSan 通过。调用实际 lifecycle/native-context/rollback C；native
  leaf 与 TCB 是 mock。包含资格拒绝无效指针、正常 -1、parent 指针不匹配、显示
  失败、cleanup 拒绝保留/重试、拒绝重建和 revoke 不重复 free。
- [目标报告](../../research/ep7/text-native-lifecycle-target.json)：15 个对象，剩余
  10 个符号都是原厂地址；新增 C 892 字节，open/retry/revoke 局部帧为84/24/20。
  仍未形成完整调用链栈预算、整体固件链接或硬件执行结论。

新增链接目标：`ep7_stock_ui_attach_unresolved=60d02beb`、
`ep7_stock_text_bind_unresolved=60d0487a`；setter 沿用 `60d4c9df`。
复现入口为 `tools/ep7_text_native_lifecycle.py`、`text_lifecycle/check_native.py` 和
目标 checker 的 `--ui-lifecycle-only`。

下一项落实真实 owner 的入口/结束位置及资源 descriptor+12 的语义，然后用独立
H/L 资源副本和具体 qualifier 驱动上述流程。当前 `qualify` 是必须完成的入口契约，
没有拿 constant-true provider 或假锁代替它；G4/G6 尚未整体通过。

后续节点已定位空导航表消费和 owner 的 bind/cleanup/destructor 关系，并接入实际
ID 冲突查询与共享游标恢复。上述96指令/15场景/15对象记录为本页初始节点的验证；
当前124指令、16场景、16对象和代码尺寸见 [后续报告](UI_OWNER_LIFECYCLE.md)。
