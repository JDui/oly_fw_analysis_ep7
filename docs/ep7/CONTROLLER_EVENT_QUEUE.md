# event42 与 mailbox1：两条独立的 controller 输入

2026-10-31。延续[冻结前读取责任](CAPTURE_READ_OBLIGATIONS.md)。本批接通的是
producer自投event42的队列，不把它并入之前已经审查的mailbox1。

|通道|已识别事件|启动配置/通知|controller接收与分派|
|---|---|---|---|
|mailbox1|engine的event4b/4c|60040cdc=1；event flag74的bit1|602898ad→6020c101；6028992b调用事件handler|
|message queue0x67|producer的event42、kind19 ACK的event44|60040daa=103；最大12字节、ring256；event flag74的bit4|60289b1f→6020bf7a；60289b97调用事件handler|

queue0x67的原厂配置行6003b638为`{103,0,12,256,0}`。初始化602897bf..97cf将
该queue与flag74/bit4交给600515de；600515de把通知ID/mask写入每项+4/+8。
其中仍有udfu01索引指令，本批记录其实际操作数，没有模拟该指令或声称读取了实机对象。

两个通道都由60289852的循环接收，但不是同一个FIFO。mailbox的发送成功顺序不能
跨通道排序event42；任务还处理bit2对应的第三通道，不能只按消息编号推导全局顺序。

## event42先入队，source在当前handler内继续

state33 event4b对应602a281a。其602a2903先写associated+8=node；普通flag0分支
经602a291e→602ac141→602ac1e1继续，A2保留associated。

在两条前置list都有元素且匹配检查通过的分支，602ac2e4..2e8把event66/0x42和
associated交给602ad656。后者构造12字节栈记录：status半字在+0，event在+4，
associated指针在+8；调用6020beb4发送到queue0x67。另一分支先进入独立等待list，
不能描述成所有图像立即发送event42。

6020beb4调用named send600514b6。本地路径保留raw60036ede、错误归一化及
60051078通知；本地通知调用60035a5e事件标志服务，没有直接调用event42 handler。
这些原厂API的调度、等待及异常行为仍是显式callee边界。

发送返回后，602ac1e1根据原厂状态选择602ac3de立即source、602ac3f6等待入队，
或原厂清理等分支。在同一个controller的正常返回调用栈中，只有当前事件handler
返回后，主循环才会再次接收并在60289b97分派queue0x67消息。**“已发送event42”
不等于“它的释放handler已在当前调用内执行”**。

event42的state33表项6042d2ac指向602a2937。该handler从packet+8取associated，
再读associated+8取node；正常条件分支于602a2a00释放node，602a2a0f归还associated。
两处已有候选撤销接合。归还CALL实际frame为56；本次首次检查发现探针录入为36，
按当前反汇编改正后通过，没有改变生产桥或放宽核对。

## 本批能关闭与不能关闭的疑问

已明确event42的真实载体、接收者和handler位置；排除把它当成mailbox1同FIFO事件，
以及把普通send调用本身当成直接执行释放的依据。当前函数调用的局部顺序已接通。

这仍不证明队列永不删除、只有一个可能的receiver、外来直接调用不发生、RTOS异常不
重入或所有别名都被覆盖。已接合的销毁在新增C busy区间必须撤销或隔离；未接合free、
profile/identity写入以及实际associated归属仍按G1清单审查。不能据此关闭G1/G8。

[探针](../../tools/ep7_controller_event_queue.py)核对121条精确指令、8项数据，保存
controller、producer、packet sender、通知注册器的有限CFG及外部边界。
[结果](../../research/ep7/controller-event-queue.json)不包含原生执行或调度模拟。
无SHA、生产代码变化、对象重编译、固件改写或相机操作。
