# 捕获事务、三组补充节点接合与实际 CALL 检查

本批回到 G1。现有原生 capture provider 虽然检查 controller 任务，却没有在额外的
prefix 读取、lookup 或 core poll 回调期间阻止重入释放：仅关闭后续准入后返回，会让
原 free bridge 继续执行原厂释放。现在这些原生 C 操作具有明确的 busy 区间，重入
销毁/状态观察在原厂 free 或 state commit 前进入现有不返回的 quarantine。
这不是新增全局 heap hook，也不是完成整个原生异步生命周期的证明。

## 同一原厂流程的三组接合

完整 main 的有限 CALL 编码候选扫描找出3116创建器的四处直接引用。三条路径具有
相同且已核对的“创建 → queue publish → 第一段填充 → 第二段填充”序列：

|调用者路径|fresh3116|sample7ea0|finish8dbd|
|---|---|---|---|
|31bb 补充循环|602a31c7|602a31ea|602a31f7|
|state33 event4e / 433c|602a440a|602a442c|602a443e|
|state33 event4c → helper446d|602a4480|602a44a3|602a44b5|

三条 fresh 的 caller mask/frame 都为 `[d2,a2],28`；sample 为 f0/20、finish 为 f0/48。
返回新 node 保存到 caller A2，两段原厂调用恢复该 A2，因此可直接复用已有三座桥。
后两条调用者另用 A3 保存待完成的旧 node：不能把旧 A3 当成新分配的样本来源。
分配返回 NULL 跳过 publish/population；入队失败走31a9，并在31b1释放新 node。
旧 node 在4461/44d8的释放仍由独立 observer 覆盖。

此前接合清单只有31c7组，缺了后两组；当前 cohort要求三组同时安装。共享短CALL桥
的起始地址交集如下，仅表示编码距离条件，不表示已资格化的空闲 ROM：

|桥|允许起始地址区间|
|---|---|
|fresh|6029c480..602ab1c6|
|sample|6029c4a3..602ab1e9|
|finish|6029c4b5..602ab1f6|

第四处6029cdd0是不同流程：返回 node 在 A1，随后把 associated+6设为1并放入
queue6223e314，没有这里相邻且 A2明确承载 node 的完整填充序列。它仍未获准，不能
借用本批桥来声称覆盖。扫描同时得到7ea0的10处和8dbd的11处直接CALL候选；这些
其他填充、重复填充、状态进入路径仍需按其实际对象来源分类。扫描没有找到这四个
入口的绝对地址 word 引用，但不将这种结果等同于不存在间接/计算调用。

## 实际25处 CALL 与事务边界

`controller_sidecar/cohort.c` 核对实际 ROM 地址处的opcode、带符号PC位移、save mask、
frame 和最终桥地址：9处fresh/sample/finish、2处state service、13处已列node free、
1处capture pool release。只接受原长度5/7字节CALL，部分接合或错误frame拒绝。
新检查复用现有桥，不新增原厂地址外部符号。

同一已发布 runtime 及 controller 的 TCB、tid、domain、entry、stack被固定；不能
重新绑定到替换/撤销后的 runtime。进入原生 C 操作后持有 busy，直到完成以下流程：

- fresh 的 prefix/associated/实际 capture lookup 与登记；
- population 的 resolve → authorize → prefix → sample/finish；
- source 的 associated backlink → resolve → prefix → 冻结值copyout；
- node/capture 撤销与 state observer。

lookup/core poll 期间重入这些 observer 时，先检查到 busy，再隔离，原 free/pool
release/state commit 不能继续。非controller或TCB不匹配的非销毁输入永久关闭
新的 capture 准入；同样错误发生于销毁/状态 observer 则直接隔离，不能仅返回。
`closed` 不绕过已经进行中的 busy 检查。runtime stop 仍保留合法撤销操作；首次
初始化之后再次调用初始化 observer 也不能继续执行原生 state0 写入。

这些约束适用于实际已接合的调用边界。它们不为未覆盖的 free、跨核写入、其他
associated/capture重用或任务同址重建凭空创造排他；仍依赖G6的唯一controller启动、
永久存储、完整hook组和代码可见性。初始化inline seam还由已执行初始化及G6安装顺序
负责，不是这25处CALL检查的一部分。完整原厂填充执行本身也没有被 busy 包围；busy
保护的是新增 C 访问/取值区间，不借此宣称原厂所有异步工作已静止。

## 已运行检查

- [原厂证据](../../research/ep7/capture-transaction-native.json)：91条精确指令、3组
  任务/事件表项，以及上述四个入口的完整 main 原始CALL候选清单通过。使用现有无SHA
  结构解码入口，没有执行相机代码或修改输入。
- [原生C host报告](../../research/ep7/capture-transaction-host.json)：12个独立模拟启动
  场景 strict/ASan/UBSan通过。这次直接编译并执行 `native_binding.c` 与 `cohort.c`，
  在fixture自有低地址映射中读取state/CALL字节和真实布局prefix；lookup、任务、队列、
  semaphore边界用mock。覆盖冻结值、提前copy、capture撤销/复用、25处CALL缺失、
  lookup及core poll重入、不同TCB、关闭锁存、runtime撤销和重复初始化。
- [目标对象报告](../../research/ep7/capture-transaction-target.json)：57对象通过，32个
  原厂外部绑定不变；全部自有软件依赖闭合。原生binding的text列1370/BSS664字节，
  cohort的text列457字节，未增加桥指令。局部`.su`为enter52、fresh56、population92、
  copyout80字节；不代表4096字节controller任务的总栈已经通过。

host的指针宽度断言只在显式`EP7CN_HOST_FIXTURE`构建中豁免；目标编译仍要求32位。
每个模拟启动用独立子进程，生产代码没有为了测试增加live reset；低地址映射中只写
自有fixture数据，没有映射或执行原厂代码。未重跑未改动的整条16-job链和UI测试。

## 下一步

G1继续审查其余population/重用入口与已登记node的完整别名释放，尤其是关联队列、
event4c/event4e全局指针和异步完成回调的对象责任；原始引用扫描不能替代这些证明。
随后关闭G2/G3丢弃票据、退出/任务存活，落实G6合法ROM/RAM、初始化安装、cache与
总栈。当前尚未达到G8，也未开始整体固件编译、链接或生成安装包。
