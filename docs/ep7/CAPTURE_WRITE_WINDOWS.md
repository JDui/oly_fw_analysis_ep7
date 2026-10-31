# 两个异步回调对 node 的写入范围

2026-10-31。按[新增读取责任表](CAPTURE_READ_OBLIGATIONS.md)，优先区分坐标/完成标志
写入与H/L实际读取的身份字段。复用现有严格GNU执行器、原厂CALL/CALLS与完整callee，
仅运行两个明确现场；没有重编译生产对象或运行整套测试。

## 已分类的两个写入者

|回调与来源|node写入|与新增读取的关系|
|---|---|---|
|602a334f，经state33 callback602a2f73内的602a2f76调用|8个halfword到+12..27；60555123再写4个halfword到+28..35|不与+0..3的ID、+8..11的associated指针重叠|
|type39完成6029e8f1，经6010c059间接调用|word +4完成标志；奇数sequence分支写halfword +50/+52|同样不与上述两个身份字段重叠；之后可能发送event4c|

602a334f从engine+24所指对象的+292读取8个halfword。60555123是无调用的19指令
helper，将源+164起的4个word加131072、右移18位，再写4个halfword。associated+6
为1时还把结果复制到固定全局6223dd5c..63；它没有修改associated payload。

6029e8f1由descriptor+8取得node、+12取得辅助数据。根据node+44的奇偶性，要么
更新全局6223dd6c/+6e，要么把两项相加后写node+50/+52；随后置node+4的0x04，
调用602a302b检查0x24条件，最后清busy字节6223dd51。前文已经接通的IRQ入口说明
其执行域不能简单当作controller；本批没有再次模拟IRQ投递。

## 两次原生执行的范围

- stage执行137条指令，选associated flag1，覆盖8项循环、实际60555123和全局复制。
  node只改变+12..35，其他字节完整比较不变，SP恢复。
- type39执行41条指令，选sequence1，node初始flags没有0x20；实际完成回调和302b
  均运行。只改变node+4..7、+50..53，global仅清busy，SP恢复。event4c发送分支未进入。

node是明确存活的56字节fixture，associated、engine、输入参数、descriptor和辅助
数据按实际被读范围单独提供为只读region。私有H/L、capture内容、分配器、调度器和
事件发送函数均未映射，没有用成功桩替代回调或helper。

[探针](../../tools/ep7_capture_write_windows.py)同时核对精确指令与4个有限函数CFG；
唯一外部控制边界是302b的event发送调用，报告保留该边界。
[结果](../../research/ep7/capture-write-windows.json)保存现场分支、执行计数及比较结论。
这是所选存活现场的字段写入验证，不是并发、释放或取消验证。

## 还需要保护的部分

两个回调的直接写入本身不会覆盖H/L所读的node身份字段，但event4c的接收处理仍可能
释放node。原厂producer602ac1e1也存在先经602ac2e8投递event42、后走602ac3de立即
source或602ac3f6等待入队的路线；不能因“字段不重叠”就省去消息接收、backlink和
冻结区间的存活审查。该producer顺序是本次窗口阅读所得，尚未作为本探针的执行场景。

其他callback、释放别名和capture profile写入继续按责任表处理；不把这两次执行扩称
所有原厂回调无竞争。G1和G8仍未通过。无SHA、原厂镜像改写、整体固件编译或相机执行。
