# 复用原厂文本工厂，并保留初始化结果

新增 GCC 可调用的 `ep7_gcc_text_factory(owner, resource, result)`，复用既有
原厂工厂，不重复实现分配、构造和资源初始化。它把 child 和 initialized 分别写到
独立结果结构，并在正常返回前恢复原有 UI allocator selection。目标对象尚未链接
到固件，实际 UI 创建/挂接流程仍待接入。

## 原生返回值没有丢失

原厂工厂内入口 `60d337b2` 的输入是 D0=type、D1=owner、A1=resource；原厂调用方
使用 `CALL[d2,a2,a3],24`。type8010 的直接表项 `60fa8e84` 指向 `60d33b02`：
申请 180 字节、调用文本构造、保存 allocator bytes，再调用 `60d4bfee` 初始化。

初始化失败路径 `60d4bffc` 将 D0 清零；成功路径 `60d4c092` 返回 D0=1。
共同工厂出口 `60d37b4b` 只将 A3 移到 A0，随后 `RET[d2,a2,a3],24`，**不会覆盖 D0**。
因此可同时取回 A0=child 和 D0=初始化状态。旧通用调用方忽略 D0，不代表必须重建
工厂才能取得结果。

|返回结果|调用方义务|
|---|---|
|child=NULL|没有新对象；veneer 将 initialized 归一为 0|
|child 非空、initialized=0|仍持有新分配；不得 attach 或丢弃，须执行 fresh rollback|
|child 非空、initialized=1|初始化完成；尚未绑定父控件、挂接、呈现或获得 ready 资格|

原厂 factory 会读取 owner virtual+248 并更改全局 service 的选择。新 veneer 在调用前
经实际 service getter/+248 保存旧选择；将返回结果存入独立结构后，经实际 +244
恢复旧选择。失败初始化后的 rollback 仍会选择 child 保存的 bytes 再释放，因此不
依赖 factory 遗留的全局选择值。

## 调用边界与栈

`text_lifecycle/native_create.h` 明确要求已资格化的 live owner、稳定 GUI service、
串行所有权和完整 resource/subobjects。对已定位的双布局模板，还需要 count=2、
index=0/1 并在创建期间保持不变；仅传入一个非空资源指针不满足条件。

GCC D0/D1 为 owner/resource，第三参数位于调用方 S+12。veneer 自身 40 字节帧 W：
W+4 保存 service，W+8/+9 保存旧选择，W+12/+16 保存两个输入，W+20 保存 result，
W+24..39 保存 D2/D3/A2/A3；第三参数从 W+52 取出。嵌套 factory 的 24 字节帧位于
W 以下。结果结构在目标上为 8 字节，child 位于 +0、initialized 位于 +4。

从 factory 返回到保存结果之间，没有会改写 D0/A0 的函数调用。只有 child=NULL
分支会清 D0。恢复 allocator selection 发生在结果存储之后，不会破坏结果。
所有前置存活/排他条件须保持到恢复结束；原生异常和非正常返回未建模。

## 本次定向验证

- [当前原厂证据](../../research/ep7/text-factory-result-current.json)：115 条相关
  指令和 factory 表项；旧脚本 witness 通过 AST 读取，不执行 SHA guard。
- [MN10300 目标检查](../../research/ep7/text-factory-result-target.json)：新增桥
  28 条指令、83 字节，四个原厂 CALL 和一个局部分支 relocation；精确核对恢复顺序。
  复用 context/rollback 后共 12 个对象，剩余 7 个符号全是原厂地址。
- 实际 GCC13.4 caller 输出验证了第三参数 S+12、结果字段布局和 pointer 返回寄存器
  A0。`factory_caller.c` 是编译器 ABI 探针，不是实际 UI flow。

首次目标校验发现 objdump 默认省略局部标号前的零字节；MN10300 的 `CLR D0`
恰是 opcode00。检查器对该桥启用 `-z` 后检查到全部 28 条指令，未删掉清零步骤
来迁就工具输出。没有重复执行无关主机测试、全套 pipeline 或 SHA。

复现：`tools/ep7_text_factory_result.py` 和
`tools/ep7_sidecar_target_check.py --ui-create-only`。原厂地址新增
`ep7_stock_widget_factory_unresolved=60d337b2`，其余沿用
[UI context 绑定](UI_CONTEXT_BINDING.md)。

下一项：把上述真实 factory result 接入既有 `text_lifecycle` 回调，完成资源副本中
opaque 字段、独立 ID、parent/list attach 与失败所有权的实际绑定，再联通 H/L viewer。
`renderer_ready` 仍为 false；本批不是整体固件编译或相机显示验收。
