# Runtime 的启动接续与分阶段安装检查

2026-10-31。候选发布位置收敛到 **60191371**，在原厂 Usr3 初始化任务内、
流水线任务启动之前。它仍待具体 bootstrap、安装组、栈与放置资格，不能直接安装。

## 已核对的入口

|项|原厂事实|
|---|---|
|任务配置行|60038ebc：ID002d、attributes0、parameter0、entry601912fb、priority55、stack2048、pointer0|
|原 CALL|60191371 → 6011f620，7字节，save mask0，caller frame4|
|原接续|60191378|
|局部前序|等待a272e3e8的0x1000，再调用第3、4段初始化器6004586c|
|调用者前序|Usr2在60190eee调用controller initializer602897a8；601911e9启动ID002d|

bootstrap 应先验证实际当前TCB的 domain0、entry601912fb、ID002d和栈边界；
表中的2048不能代替实际栈查询或完整峰值预算。原CALL可以同宽重定向到一个保存输入状态、
调用初始化函数、恢复状态后tail-JMP6011f620的桥；原4字节调用帧及返回地址保持原位。
本批只记录该契约，尚未实现桥或生成固件补丁。

## 为何排除更晚的发布点

Usr3的原厂顺序包含下列任务启动调用；这些是相邻MOVHU/EXTH/CALL及实际ID字段，
不是根据日志字符串推测：

|启动CALL|任务ID|entry|用途|
|---|---|---|---|
|6019155b|0021|603ef892|4c/4d receiver|
|60191591|0057|603ef94a|kind19 relay|
|60191618|006c|603f26a1|kind19 worker|
|60191684|0020|603df803|command materializer|
|6019190e|0073|60289852|capture controller|
|60191a1f|002c|60191a7f|Usr4，第5/6段初始化|
|60191a47|002a|60191b74|Usr5，第7/8/9段初始化|

因此，Usr5的60191bd5虽然位于第9段初始化返回后，却已经晚于流水线的启动。
当前materializer/descriptor接收provider在未发布runtime时拒绝工作；不能把晚发布
当作无害的默认降级，也不能直接增加等待循环而不核对初始化依赖。

另一个看似方便的位置600451f2属于ID2015的domain2加载任务，且仅512字节栈，
不符合现有单domain0私有锁/runtime。domain0的加载协调任务ID002e也只有512字节栈。
这两类加载任务不再作为bootstrap的首选。

## 任务与队列确实怎样进入kernel对象

root0配置600411a4的+124指向任务表600389d0，+156指向队列表6003ad78。
kernel初始化600326c5调用60032945；后者先调用任务配置consumer60032998，
再在60032968调用queue consumer60032c6b，然后才返回后续调度初始化。

60032998按当前8050选择root和TCB指针表，写入TCB+16任务ID，将配置行+4..+24
的六个word复制到TCB+68..+88；所以entry、priority、stack size、stack pointer
分别进入+76、+80、+84、+88，再调用60030afa。queue consumer将配置的四个word
复制到对象+20..+32并调用60030c4c。实际分配结果仍由现有runtime的live queue查询验证。

此前TASK_DOMAINS中的6005b447只是一段遍历/查询表的证据，不能作为实际创建链证明。
本次用kernel consumer补上这个缺口，仍不推断任务永不迁移、删除或复用。

## 发布与UI资格要分阶段

冷清零必须早于所有访问私有BSS的hook。Usr3发布时需核对早期kernel、controller、
pipeline及CPU COLOR的完整安装组；相关代码位于早期kernel和第2段，发布点位于第1段。
第3/4段的本地初始化返回可作为该入口顺序事实，加载标志本身不证明传输或cache成功。

UI owner、MVC/content、selector和input表/代码位于第6段，Usr4还在后续启动链中。
**早期发布不得读取尚未驻留的UI表，更不能等待Usr4/Usr5完成而堵住启动它们的Usr3。**
UI资格需在自身已经驻留的入口检查，复用现有owner/MVC/input cohort，并补齐selector
和完整安装依赖。所有UI字节仍必须由离线完整安装清单覆盖；分阶段检查不免除该要求。
runtime发布本身不授予renderer_ready，初始H/L值仍为零。

下一步：实现早期inline/启动组检查与一次性bootstrap，明确失败时不继续启动已改造
的接收任务；完成桥的输入状态保存和实际栈预算，再回到代码/RAM、cache及生命周期准入。
不得把当前候选入口标作完整CFG、全部任务启动者或所有转移路径已经闭合。

[静态脚本](../../tools/ep7_bootstrap_entry.py)与[报告](../../research/ep7/bootstrap-entry.json)：
85条精确指令、10条完整任务配置、7个启动ID字段和两个root指针通过；未做SHA、
未重跑既有host全集、未编译整体固件或操作相机。
