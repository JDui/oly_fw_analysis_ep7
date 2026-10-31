# Associated 固定对象池：来源、归还与重新初始化

本批补上独立于 node free 的生命周期边界。event42 的602a29f0分支可以跳过 node
释放602a2a00，却仍在2a0f归还 associated；state34 的2ca9/2cc7也有对应结构。
因此“节点尚未free”不能证明 node+8所指关联记录仍属于该图像。

## 实际池布局

6029c66f..c692将常量池地址写入global6223e0d8，调用通用初始化器602972aa：

|项目|实际值|
|---|---|
|pool对象|6223e0dc，32字节|
|free-list对象|pool+4，即6223e0e0|
|free-list backing|6223e0fc，25个4字节指针|
|slot backing|6223e160，25个16字节slot，止于6223e2f0|
|slot header|前4字节引用计数|
|associated payload|header+4，12字节；有效地址6223e164..6223e2e4，步长16|

初始化器保存stride至pool+24、backing至pool+28，清每个slot header并将其入空闲
list。list初始化器6020b949明确保存capacity、element-size和backing。分配器
602972e3从该list pop header，设置refcount=1，返回header+4。fresh3116在3189加载
同一pool，318f分配，3196写capture ID，3198写flag0，319b存为node+8。

原生C现在在fresh登记、population prefix和source backlink读取前要求实际pool
指针/容量/两种stride/backing一致，associated处于上述槽位且refcount非零。检查
固定RAM布局，不读取任意指针之前的未知内存，也不把12字节payload误当16字节。
这是分配来源与当前计数检查，仍不等于取得跨任务内存锁。

## 归零后的真正归还边界

60297328并非每次都回收：A0=pool、A1=payload；A3保留pool，A2=payload-4。
它在97386减计数并存回；计数仍非零则9738a直接到return。归零后还检查free-list
未满，只有973b8..973bc把header放回list。因此hook选在 **602973bc** 原调用
`6020b98b,[],8` 前，而不是每个调用60297328的地点。

新桥将A3 pool、A2 header交给observer，保存/恢复原生寄存器与MDR后尾跳原enqueue。
只有pool==6223e0dc才进入capture事务；通用函数还服务其他池，其他pool不查询
capture runtime/task，也不读取其header。匹配池必须是有效header且计数为0，然后
按associated标签清除所有匹配sidecar项，才允许原厂入池。

撤销不依赖node或capture已释放；旧node前缀仍可存在。token serial不回退，后续
真实fresh登记得到新token。已交给下游job的按值H/L继续独立存在。

完整main有限CALL扫描得到11处60297328调用：7处加载6223e0d8，4处加载其他pool
全局。它不是对计算调用/跳入函数内部的全控制流证明；共同归还seam覆盖正常入口。

## 初始化也必须先撤销

固定pool的初始化CALL **6029c692** 也进入同一检查组。observer在原厂清计数/重建
空闲list之前撤销这25个slot的登记，保留sidecar代际和单调token serial。已封存
与尚未完成population的项都不能跨越pool reset继续使用。

该调用是5字节短CALL，原tuple为`[d2,d3,a2,a3],28`。602972aa读取sp+32/+36的
incoming参数，所以新桥在自有40字节frame中调用C，恢复后**尾跳**原initializer，
没有在新一层原厂frame中重复调用。其近桥入口允许区间60294692..602a4691仅是
编码约束，仍需G6合法放置。全main有限扫描得到5处initializer CALL，其中这一处
使用固定capture pool；其余四处配置其他池。

实际完整CALL检查组现为29处。新增原厂外部绑定如下：

|符号|原厂地址|用途|
|---|---|---|
|ep7_stock_associated_enqueue_unresolved|6020b98b|原free-list enqueue尾转|
|ep7_stock_associated_initialize_unresolved|602972aa|保留incoming栈参数的initializer尾转|

已有busy、永久runtime身份与controller资格继续适用；匹配池的外来/重入回收或
reset不能返回原厂继续复用。runtime stop仍保留撤销。这不证明所有异步callback
已经静止，也不能让旧队列裸指针自动携带其原图像代际。

## 当前验证与后续

- [原厂静态报告](../../research/ep7/associated-pool-native.json)：117条指令、11处
  归还/5处初始化CALL候选清单通过，复用现有无SHA容器检查与窗口反汇编。
- [原生C报告](../../research/ep7/associated-pool-host.json)：31个独立启动场景通过
  strict/ASan/UBSan，新增10个场景覆盖真实布局检查、首尾槽位、无效/未分配槽位、
  节点仍存活时归还、token/address复用、无关池、外来/重入回收、pool reset和stop。
  fixture映射自有RAM并mock原厂API，没有执行原厂指令或模拟引用计数机器码。
- [目标对象报告](../../research/ep7/associated-pool-target.json)：57对象、自有符号
  闭合和203条bridge指令检查通过；新增38条桥指令。原厂外部绑定为34个，新增2个
  地址见上表。native binding text1786/BSS696，sidecar text2928，cohort text505，
  bridges530字节；recycle/reset局部`.su`各28字节，完整任务总栈仍待G6。

未重复运行未改动的UI和整条job链；上轮整链结果保留。本轮未做SHA，未修改原厂
镜像、未安装hook。下一项仍是已登记node在engine workrecord、global6223dd54、
异步描述符与event4b/4c/4e中的顺序和释放责任，再汇入G2/G3退出及G6放置/安装/总栈。
G1完整闭包与G8整体固件构建准入尚未通过。
