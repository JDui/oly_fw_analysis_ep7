# Engine 工作记录顺序与重新初始化代际

2026-10-31。本批绑定 engine pool/configure 的真实入口，并把当前回调表纳入捕获
资格检查。原生工作记录、节点、已输送快照各有自己的生命周期，不能用一个清零
操作替代全部退出责任。候选代码未安装，没有执行相机固件。

## 工作记录与正常完成顺序

`6029acd8` 初始化 list6223d0e0，backing6223d0f4，容量4、元素4；随后循环4次，
以基址6223d104和 `udfu01 12,d2` 形成记录地址。这里仍不模拟该自定义指令。
`6029b354` 明确清三个 word：+0 node、+4 current flags、+8 reported flags。
记录本身不由此 heap free。

`6029ae61` 在记录低16位尚未开始时调用6223d134的 selector，将返回的 node 存入
record[0]。各阶段把记录指针保存在实际 engine 子对象中，completion 再取回该记录。
启动位为1/2/4/8；完成位为10000/20000/40000/80000，另有可选100000。

state33 初始化 `602a2733..274f` 写入 engine+144=0x23、+128=3、+148=3、
+112=0x82000。`6029ada9` 由这些字段构造 required mask=`0x000f000f`。
`602a27e4` 把17项 callback/mask 表交给 `6029ad23`，后者复制到6223d134。
完整表已由[探针](../../tools/ep7_engine_epoch.py)核对，并与实际 C guard 的数组比对。

其中与本批结论直接相关的项：

|项|值|作用|
|---:|---|---|
|0|602a2d43|从节点队列选择节点|
|1|602a2ec7|全部必需阶段完成，置 node+4 的0x20|
|5|602a2f91|阶段8的启动回调，提交 type39 或 busy 快捷完成|
|13 / 14|602a3042 / 0x60000|选中通知0x4b及其完成位条件|
|15 / 16|602a2edd / 0x70000|associated flag1 的另一路0x4d|

`6029b387` 对两组 callback/mask 比较 current 与 reported；只有新达到完整 mask
才调用。循环结束才把 current 写入 reported。每个 completion 均先调用 b387，
再经过无分支的参数恢复调用 `6029aef8`。后者只有高16位等于 required 高16位，
才调用602a2ec7，然后清记录并重新入队。四个正常完成位中，0x60000 是0xf0000
的真子集。因此在**同一串行正常周期**，0x4b 选中回调先于全部完成回调。

type39 completion6029e8f1及 busy 分支给 node+4 置0x04；602a2ec7置0x20。
两者都调用602a302b，后者要求 `(flags & 0x24)==0x24` 才发0x4c。
这缩小了正常路径中的释放顺序不确定性，不证明回调互斥或 mailbox 投递成功。

## 为什么重新初始化需要独立撤销

`6029ad23` 在同一调用中改写全部17项、active/stop 状态及 required mask。
`6029acd8` 则清空并重新排入工作记录。仅在 controller state commit 撤销，不能
覆盖“状态值和 callback 内容相同，但工作周期已经被重建”的情况。

当前 full-main 有限 CALL 扫描找到：

|原 CALL|原目标|mask / frame|候选桥|
|---|---|---|---|
|6029ef4c、602a27e4|6029ad23|[a2] / 8|ep7_native_engine_configure|
|6029ce9d|6029acd8|[d2,d3] / 16|ep7_native_engine_pool|

两座桥保存 D0/D1/A0/A1/D2/MDR，调用 epoch observer 后恢复并 tail-transfer。
D3/A2/A3 由 GCC 保留，原生输入栈与原 CALL frame 不变。observer 在第一条原生
写入之前复用 `ep7c_transition(state,state)`，撤销现有节点登记与等待快照，保留
token serial；state33 中递增 generation。runtime 停止后仍撤销，外来任务或
额外 C 事务内的重入仍隔离，不能继续执行原生重建。

每次捕获 C 事务还检查 state33 的真实17项及 required mask。不匹配时先撤销旧代；
新准入保持中性，清理事务继续。以后即使表恢复为同样内容，旧节点与等待值也不会
复活，必须经过新的 fresh/population。这样允许之后正常重建的新捕获继续工作，
不将暂时的不受支持配置永久绑定成有效快照。已交出的独立按值快照保持原值。

实际 CALL cohort 从36扩至39。configure 两处短 CALL 的公共目标区间为
`6029a7e4..602a6f4b`；pool CALL 区间为 `60294e9d..602a4e9c`。它们只是距离
约束。新增原厂绑定为 `ep7_stock_engine_configure_unresolved=6029ad23` 与
`ep7_stock_engine_pool_unresolved=6029acd8`，尚未资格化 ROM/RAM 放置。

## 检查结果与剩余责任

- [原厂报告](../../research/ep7/engine-epoch-native.json)：250条精确指令；两个
  initializer 的3处 CALL、all-complete的5处 CALL、notification的9处 CALL清单
  匹配。校验当前输入结构、加法和及未修改回转，无SHA。
- [主机报告](../../research/ep7/engine-epoch-host.json)：5个新增场景加原45场景，
  strict/ASan/UBSan通过。执行真实 capture C、39处CALL decoder和字段读取；
  覆盖同表重建、表/掩码恢复不能复活、重入、外来任务和stop后撤销。原生 engine
  与 callback 没有执行，task/list/lookup/RTOS仍是fixture。
- [目标报告](../../research/ep7/engine-epoch-target.json)：59对象自写符号闭合，
  39个剩余外部符号为原厂地址绑定。新增桥92字节/36指令，自有帧40字节；observer
  局部栈28字节。capture native text3600、BSS1912。未链接或构建整体固件。

`6029ae33` 仅设置 stop request；`6029b35f` 等待 active=0且当前记录低位空才锁存
stop。**它不是已完成或已清空的证明。** controller event43清空尚在节点队列的
节点及完成后 wrapper 队列，不应被描述成已取消所有 engine/async 引用。

下一段必须核对 callback 的执行域及排他区间：b387 在 callback 返回后才更新
reported，302b 也没有一次发射锁存；在未排除交错/重入前不能宣布通知只发生一次。
例如两个写入0x04/0x20的回调交错后都通过302b条件，是当前尚未排除的逻辑情形，
不是本批认定的原厂故障。还要沿6020c03c的任务/非任务分支核对 mailbox1 的真实
FIFO配置、删除/重建与 controller 顺序，不能仅凭函数名或消息值相同认定顺序。

以上推进 G1 的正常顺序与重建边界，没有关闭全部异步别名、取消与任务生命周期。
G6 的放置、冷安装、cache和总栈仍待完成，G8尚未通过。
