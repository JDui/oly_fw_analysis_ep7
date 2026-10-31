# 忙碌等待队列中的捕获快照

2026-10-31。当前输入核对发现正常 metadata producer 有两条路径：立即调用
`602ac3de` 的 associated 在 A2；忙碌时经 `602ac3f6` 入队，稍后从 `602ac5e8`
出队，associated 在 D2，并由 `602ac60e` 调用相同的 `602ac748`。
此前 scope 仅覆盖立即路径。现在两条路径都可以传送冻结值，metadata 仍为148字节。
这些是未安装的候选代码，不是目标固件执行结果。

## 原生队列与边界

`6223e7dc` 指向固定对象 `6223e7e0`：tag182、capacity25、element4、backing
`6223e7f4`。对象的 +12/+14/+16 分别为 count、write index、read index。
初始化 CALL `602abe96` 调用 `6020b949,[d2],4`，tag 来自其 incoming SP+8。
因此 reset 桥在保存/恢复寄存器后 tail-transfer，不能插入一个改变 tag 位置的帧。

|作用|原 CALL|原目标 / mask / frame|
|---|---|---|
|入队 associated|602ac3f6|6020b98b / [] / 8|
|正常出队|602ac5e8|6020b9ff / [] / 24|
|取消出队|602ac8f8|6020b9ff / [] / 24|
|重置队列|602abe96|6020b949 / [d2] / 4|
|拥有延迟 scope 的 service|602ac4fd、602ac5a6、602ac66c|602ac5d0 / [d2] / 8|

正常路径在 `602ac88a` 返回 false 时，调用 `602ac93a` 处理此 associated，随后
继续取下一个。因此每次 pop 都先清空当前栈 scope；拒绝一个元素不会遗留它的值。
取消路径 pop 后直接进入相同清理函数，没有 producer scope。
`602ad758` 处只读队列 count 用于诊断，不修改队列。

全 main 有限字节扫描核对了两处 metadata CALL、三处 service CALL，以及该全局、
对象和 backing 的全部已识别字面量引用。它不证明间接别名/并发控制流闭包。
list 的元素寻址仍包含未模拟的 `udf00`，复制调用仍是原厂 `47001052`；新增代码
保留原厂操作，并检查真实操作前后的 count/index/backing/result，不重写原生队列。

## 保存与转移

25 个独立账目与实际 ring index 对应。入队前，在已有 controller guard 内完成
associated/node/prefix 校验，复制已经 seal 的快照。每项保存 associated、capture
标签、generation 和原有32字节 `ep7q_capture_scope`。没有在出队时通过裸地址查询
当前 sidecar，也没有晚读 UI。发布前已经存在的队列元素保持中性。

guard 覆盖完整原生 enqueue/pop，包括其错误处理。新 helper 验证队列固定配置、
count/index 连续性、FIFO head 的 associated、原生返回值与实际 backing；不一致
隔离为 `0xe09`，hooked 重入仍为 `0xe05`。全队列 enqueue 返回0，成功返回4；空
pop 返回0。实际 list API 及硬件中断行为尚未执行。

正常 pop 将此 ring slot 的值复制到本次 service 的独立栈 scope，然后清除 slot。
取消 pop 直接清除。节点释放后仍可保留已经复制的值；associated 回池、associated
pool reset、capture release、capture prewrite、状态提交则使等待中的对应值中性。
状态 sentinel255 保留原代；33→33 撤销。实际 queue reset 清除全部账目并重新观察
原生 indices；generation/token serial 不重置。停止新准入后仍处理原生 FIFO，但
不再把值交给新的 producer。已经传出的独立值不被回写。

## 栈与发送 ABI

三个 service CALL 共同使用 `ep7_native_wait_scope`。入口另开64字节帧 S，scope
在 S+24..55，以 `[d2],8` 调用原 service。入口原生寄存器参数未被原 service 使用。

|位置|pop 桥 Wp|metadata send 桥 Ws|
|---|---:|---:|
|原生返回PC|Wp+24=602ac5ef|Ws+48=602ac870|
|metadata 调用返回|—|Ws+80=602ac613|
|自写 service 返回标签|Wp+32|Ws+88|
|owned32字节 scope|Wp+56|Ws+112|
|最外层原 CALL 返回|Wp+104|Ws+160|

最外层返回只接受602ac502/602ac5ab/602ac671。pop 的取消返回602ac8ff单独识别，
不读取更远 scope。范围/对齐检查和实际当前任务栈先行；send 还核对 native 保存的
captureID 与 scope ID 相同。资格丢失不得让旧 scope 泄漏到下一元素，非法 pop
栈链隔离为 `0xe0a`。立即路径继续使用原有 mapper。

两条路径共用现有 `ep7q_producer_send`：scope 一次消费、准备并发布 ticket，然后
发送带显式票据的28字节消息，保留原厂通知及失败清理责任。缺失快照按原16字节
路径发送。没有扩大 native metadata 分配，也没有新建第二套异步 ticket 协议。

## 本次必要检查

- [原厂证据](../../research/ep7/deferred-producer-native.json)：113条精确指令、上述
  有限引用清单、原厂整包结构/加法和/未修改回转。未做 SHA。
- [主机结果](../../research/ep7/deferred-producer-host.json)：原有31场景加14个新
  deferred 场景，strict/ASan/UBSan通过。覆盖冻结/FIFO/地址复用/撤销/取消/重置、
  满空与环回、停止/永久关闭、重入、异常返回、head 改写和三条有界栈链。
  原生 list/task/lookup/RTOS 调用为 mock；fixture 初次地址映射缺口及修正已记录。
- [目标对象](../../research/ep7/deferred-producer-target.json)：58对象自写符号闭合；
  37个剩余 externals 均为原厂地址绑定。新增桥214字节/83指令；capture native
  text3300/BSS1912，等待账目增加1216字节。enqueue/pop helper 的本地栈为88/80，
  另有40字节桥帧、GCC veneer、原生 list/memcpy/错误处理帧；不是任务总栈预算。

新增7个 CALL 纳入实际 capture cohort，共36个。service 三处短 CALL 的公共可达
区间为 `602a466c..602b44fc`，仅是距离约束，不是 ROM 空间资格。
新的原厂绑定：`ep7_stock_wait_initialize_unresolved=6020b949`、
`ep7_stock_wait_pop_unresolved=6020b9ff`、`ep7_stock_wait_service_unresolved=602ac5d0`；
enqueue 复用已有 `ep7_stock_associated_enqueue_unresolved=6020b98b`。

G1 仍需完整 engine/async 别名、controller 排他与间接旁路闭包。G2/G3 仍需把当前
原生路径证据汇入退出/丢弃和任务生命周期审查。G6 仍需安全放置、冷安装、cache
及总栈；G8 尚未通过。本批没有开始整体固件编译、安装 hook 或访问相机。
