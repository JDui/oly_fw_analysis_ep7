# 一次性bootstrap：调用图与已知栈段

2026-10-31。把Usr3启动路径的栈调查从单函数`.su`推进到固定回调组合的调用图。
**已知路径累计400字节，不是完整任务栈上界，不能据此宣称2 KiB足够。**

后续[原厂栈节点](NATIVE_BOOTSTRAP_STACK.md)已补充create/delete及任务初始帧：
当前合并的已知部分为**栈顶以下416字节**，仍有异常callback和BREAK/IRQ未知量。
本页保留生成该C对象调用图时的400字节结果，其基准是Usr3入口SP。

## 复用编译器资料

[检查器](../../tools/ep7_bootstrap_stack.py)使用已有GCC13.4的
[`-fcallgraph-info=su`](https://gcc.gnu.org/onlinedocs/gcc-13.4.0/gcc/Developer-Options.html)，
按可达调用逐个取得对象VCG图及静态栈帧。只重新生成18个实际需要的C对象元数据，
每个对象的尺寸及每函数栈记录均与本轮[107对象清单](INSTALLATION_MANIFEST.md)相符。
没有为此重跑host业务/ASan全集，也没有链接固件。

结果为42个可达函数；29条间接调用边由**当前一次性bootstrap的具体组合**解析：

- `ep7b_unresolved_native()`中的create/drop和raw get_tid回调；
- `ep7r_native_environment(NULL,installed)`中的安装组与queue查询；
- `native_ops`中的get_tid、read32和read16。

脚本核对上述实际赋值片段；不把这些绑定外推到其他可复用接口的任意调用者。
GCC自动生成的结构体`memcpy`边也保留。静态函数优化clone名称与`.su`名称做明确归一。
未解析callee、未解析callback、动态帧或可达递归均会拒绝计算，而不是按零计入。

## 最深已知路径

|当前对象调用链|本层静态帧/字节|
|---|---:|
|ep7r_bootstrap_initialize|96|
|ep7r_publish|40|
|native_context.c:queue|12|
|ep7n_native_queue|16|
|ep7n_query_queue|104|
|queue_context.c:read_view|44|
|task_context_native.c:read_word|0|
|合计|312|

这是对当前调用图的保守逐层相加；顺序调用取最大值，不累加不同时存在的子调用。
没有利用tail-call回收来降低数字，因此不因尾调用优化而低估已知部分。
再计入原厂Usr3 prologue44、原CALL帧4、cold bridge40，得到相对Usr3入口SP以下
**400字节的已知部分**。它不包含任务初始kernel context或IRQ异常保存区。

本次另完整检查原厂`600317ac..600317f0`的30条get_tid指令：没有额外SP调整、调用
或区间外分支，末尾`retf [a2],4`。其适配桥16加原厂CALL4共20计入图中。
这是栈效应检查，不是重新验证全部TCB/任务存活语义，也没有执行原厂函数。

## 尚未定界的原厂分支

[结构化结果](../../research/ep7/bootstrap-stack.json)对这些分支保留unknown，完整上界
与剩余容量字段都为null：

|边界|从C bootstrap入口至边界的已知累计/字节|尚缺|
|---|---:|---|
|raw semaphore create|252|进入原厂6003057f之后的嵌套/临界区/调度路径|
|prepare失败后的raw delete|276|进入60031107之后的嵌套/唤醒/调度路径|
|发布失败后的raw delete|164|同上，调用层数较少|
|quarantine BREAK|96|实际异常入口与保存栈，不能按leaf0推定完整异常成本|

表中create/delete已计入适配桥16和各自原厂CALL的16/20，不能再重复加这两段。
原厂critical入口60038594还会自行保存寄存器、分配局部栈并继续调用RTOS服务；
因此不能将raw create的16字节CALL帧误当完整callee成本。

这收敛了下一项审查：原厂信号量创建/失败删除的RTOS嵌套、任务上下文切换和IRQ栈。
当前仍没有把2048减400写成“剩余可用栈”，也没有为掩盖未知量擅自扩大Usr3任务配置。
其余capture、pipeline、UI路径仍须分别完成总栈审查；代码/RAM和启动前缀资格不受本结果替代。

## 执行边界

本批只有18个目标C对象的元数据生成和get_tid的只读反汇编；没有目标执行、固件
整体链接、改写输入、相机操作或SHA校验。工具链、sources.txt及原厂绑定均复用现有内容。
G8继续保持未通过。
