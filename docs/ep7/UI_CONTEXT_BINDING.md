# G4：文本回滚的原生分配器上下文绑定

本批实现现有 `ep7_text_rollback` 的原生上下文回调。仍只生成离线目标对象，
没有安装 hook、执行原生调用或启用 `renderer_ready`。控件创建/资源和 GUI 排他
资格仍须继续完成；当前任务检查不是锁，也不能给任意指针建立生命周期。

## 实际服务和两个字节

GUI 初始化 `60cfd438` 请求 2880 字节，成功后调用 `60d39f41`，经
`60d43e80 → 60cff51e → 60cfd747` 构造。最终 vtable 为 `60faaab4`，
type 半字为 `0101`；`60cfd455` 经 `60d337a4` 将对象发布到 `61fb3138`。
基类构造期间也会暂时发布该对象，因此单凭全局非空不能认为初始化完成。

`60d3379b` 只返回该全局指针。三个构造阶段的 vtable `60f9477c`、
`60fac34c`、`60faaab4` 的 +244/+248 均分别指向：

|方法|原厂入口|原生 ABI|行为|
|---|---|---|---|
|选择分配器上下文|`60cfe586`|A0=service，D0/D1=两个字节|写 service+28/+29，RETF[],0|
|读取当前选择|`60cfe58f`|A0=service，A1/D0=两个输出地址|读 +28/+29；自行保存 A2 并 RETF[A2],4|

两者都是无失败分支的短叶函数。原厂 bulk child cleanup 在清理前选择控件保存
的两个字节；返回的 deallocator `60cfe5c9` 再从全局 service 读取当前选择，
传给 `60d109db`。这证明上下文会影响释放，未证明上下文是线程局部变量或有锁。

## 实现和资格顺序

`text_rollback/native_context.c` 新增 `ep7_text_rollback_native`，复用既有
rollback 的对象字段检查及 cleanup→destructor→returned-deallocator 顺序。
调用者继续提供真实 fresh allocation 的 `qualify`，不以 vtable 替代来源证明。

1. 在读取控件字节前，复用实际 TCB provider，要求 domain0 和 GUI entry
   `60dd5067`，然后调用对象来源资格回调。
2. 在调用方已保证存活的 GUI 服务上，核对最终 vtable/type；保存该服务指针。
3. 进入释放前再次核对任务 TCB/ID/栈以及同一个全局服务。拒绝时未更改选择。
4. 原生 exchange 保存两个旧字节，再选择控件 +28/+29。
5. 完成原生释放后，用独立栈上的旧值恢复同一服务，不读取控件，也不重新执行
   可能失败的资格查询。ops、局部上下文和保存值都独立于待释放对象。

从第 1 步之前到第 5 步之后，**活服务存储、分配器选择和控件必须处于已证明的
串行 GUI 所有权范围内**。不允许外部任务、重入、service 替换或 teardown 打断。
该前置条件仍由后续具体创建/事件/退出接入证明；本批不新增虚构 mutex。
GUI 构造使用 16384 字节栈，不代表其剩余栈空间已完成预算。静态证据也未证明
GUI 必然在 domain0；运行时检查会拒绝其他域。

## ABI 和当前检查

`context_bridges.s` 的 service/exchange/select 使用 GCC D0/D1 入参，并明确
转为原厂寄存器；不把原厂 virtual 强转成 C 函数。共 30 条指令、86 字节。
三个桥自身帧为 4/20/4 字节。exchange 的 W+8/+9 保存旧选择，W+12 保存新值，
W+16 是保存的 A2；native getter 自身 4 字节帧位于 W 以下，不与局部值重叠。
既有 cleanup bridge 的 13 条指令、35 字节验证器直接复用。

本次检查范围：

- [当前原厂窗口](../../research/ep7/ui-context-native-current.json)：59 条指令、
  三对 vtable 项；整包结构/加法和沿用当前输入工具，不做 SHA。
- [定向主机检查](../../research/ep7/ui-context-native-host.json)：既有 9 个回滚
  场景及 12 个上下文场景的 strict、ASan/UBSan。覆盖拒绝无效对象而不解引用、
  错任务/服务替换、非零高位上下文字节、销毁覆盖对象后恢复。原生叶函数和 TCB
  是 mock，没有宣称实体执行。
- [目标检查](../../research/ep7/ui-context-native-target.json)：9 个对象；新上下文
  C 348 字节，其入口/qualify/enter/restore 局部帧为 60/28/44/12。剩余 6 个外部
  符号全部是原厂地址；这不是整体固件链接，也不是调用链总栈结论。

链接地址：service=`60d3379b`，context_get=`60cfe58f`，context_set=`60cfe586`，
text_cleanup=`60d048d0`，text_destructor=`60d4be64`，get_tid=`600317ac`。
放置、调用距离、服务/控件完整生命周期、实际资源和 parent ownership 尚待 G4/G6。

复现入口：`tools/ep7_ui_context_binding.py`，`text_rollback/check_native.py`，
`tools/ep7_sidecar_target_check.py --ui-context-only`。旧带 SHA 的 checker 主程序
没有执行；仅复用其中纯指令/relocation 验证函数。
