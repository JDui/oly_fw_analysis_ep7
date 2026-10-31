# 冷启动现场准入与无trap终止体

2026-10-31。bootstrap现会在创建私有锁前检查实际内核现场；自有quarantine改为
6字节、零额外栈的本核终止循环。**这关闭了自有终止体主动进入BREAK诊断的依赖，
没有宣称完整任务栈、原厂异常处理或放置资格已通过。**

## 现场检查

`ep7r_bootstrap_initialize`先复用既有当前任务查询，确认Usr3的ID、domain、entry和
2048字节实际栈，再调用`ep7r_native_cold_context(task.tcb)`。失败以0xf06进入终止体，
不检查后续安装组、不创建私有semaphore，也不继续原厂接收任务启动。

检查是只读的，覆盖：

- domain0 root和current-cell仍为已审地址，当前TCB仍与刚取得的视图一致；
- 当前TCB的ID为002d，半字+48为1；不写该字段来制造“任务异常禁用”，也不清待处理位；
- root+28的两字节上下文状态为0，shared kernel lock状态为0；
- scheduler/IRQ入口/IRQ退出/跨核通知回调仍保持已审的原厂绑定；
- critical/IRQ mask和restart配置仍与原厂分析相符；返回前再次观察current-cell。

生产函数依旧信任原厂内核对象，不能用于验证任意损坏地址。它要求同次调用中已有
有效的domain0当前任务视图；两次相同读取不构成TCB存活锁，也不排除之后的外部改写、
取消或检查之前发生的IRQ。这些有效期条件仍需由原生生命周期审查补齐。

## 失败后的实际行为

终止体现在是`and 0xf7ff,psw`后在本地BRA上永久停留。GNU的
[PSW定义](https://gnu.googlesource.com/binutils-gdb/+/cbe950e9fe8a56f788bcf985cc51733f18abb45b/sim/mn10300/mn10300_sim.h)
将IE放在bit11；该掩码清除它。终止体不调用其他函数、不触发显式trap、不改SP，
D0继续保存失败原因。

这是停止本核普通中断和任务进展的失败策略：已有资源保留，不尝试reset/free/ACK或
恢复执行。NMI、watchdog/reset及其他核的行为不在该两条指令的保证内；没有执行相机。
原厂kernel BREAK路径没有被改写，不能把本改动当成整个RTOS故障路径已定界。

## 定向验证

[检查器](../../tools/ep7_cold_context_check.py)及[报告](../../research/ep7/cold-context.json)：

- 生产比较使用的10个ROM root字段与当前原厂输入相符；任务异常跳过条件的9条指令匹配。
- 实际准入函数运行于不可执行合成页：3次可接受观察、12种拒绝现场；每次逐页比较确认
  无写入。包含待处理异常位保留、stale TCB、未映射替代root、嵌套状态、已持锁和改绑回调。
- 只重跑启动场景0和新增15：成功创建/发布一次且重入拒绝；现场拒绝时create/delete均为0。
- 实际汇编生成`fafcfff7ca00`；单对象合成链接确认BRA落在自身。复用GNU AND/BRA
  函数体，在两种PSW状态下各走6步，D0、SP、其他通用寄存器和内存保持预期，写次数为0。

检查器开发时修正了两处环境/输出适配：Linux读Windows工作树需沿用现有换行规范；
ELF反汇编会附带局部符号标签，分支验证现比较实际地址与完整机器码。未改全局Git配置，
没有放宽生产条件，也没有跳过失败检查。

## 增量对象与栈

仅重编译cold_bootstrap.c、cold_cohort.c、quarantine.s。与已编译清单00b658e比较
生产源/头文件变更集，并确认cold_bootstrap.h只有前两个生产consumer，其余104个
对象元数据复用。101项安装原字节重新核对，安装布局未变。

|对象|text|BSS|本轮关注的局部栈|
|---|---:|---:|---|
|cold_bootstrap|426|5708|bootstrap96、installed20|
|cold_cohort|584|0|新context4、early cohort12|
|quarantine|6|0|body0|

统一清单现有345个全局定义、109个外部依赖；text46,800、data0、BSS8,084。
[C调用图](BOOTSTRAP_STACK.md)只重新生成2个变化单元，复用16个未变化单元；共43个
可达函数、29条固定callback，最深已知C路径仍312字节。owned quarantine不再被列为
未知异常callee，但原厂create/delete仍有未闭合分支。合并原厂部分后的已知值仍416，
完整上界和余量仍null。

预算改为读取同一统一对象清单，避免回到旧分批尺寸；一个既有sizeof探针确认永久
runtime仍5704字节且已计入BSS。没有重跑pipeline/UI业务或sanitizer全集，没有整体
固件链接、固件改写、相机操作或SHA校验。G6/G8保持未通过。

后续[IRQ条件分析](IRQ_STACK_TRANSFER.md)已核对五个扩展指令与0800退出mask。
只有TCB+48在IRQ查询时仍为1且保持已审返回契约，才可跳过恢复原PSW及任务异常
callback；该条件路径已知栈为96字节，通用结果仍104。未把一次准入观察当成有效期证明。
