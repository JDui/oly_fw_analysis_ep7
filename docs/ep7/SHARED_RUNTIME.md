# 共享 runtime 与清理保持

2026-10-31。G3 自写实现已接入对象检查；未发布到相机。

`runtime/runtime.c` 复用已有 `ep7b` bootstrap、`ep7p` core 和私有 poll-only
semaphore，同一把锁保护新增 transport registry。`contexts.c` 已实现历史命名的六个
`*_context_unresolved` 符号，绑定 producer、materializer、descriptor 收发、worker 和 ACK。
名字保留以兼容已有桥；这些 context 函数不再是未实现的外部接口。

## 发布和生命周期

启动顺序是 bootstrap PREPARED → runtime PREPARED → 安装组资格 → 五个实际队列实例
固定 → bootstrap/runtime PUBLISHED → release-store 唯一 slot。初始化与发布由启动者
串行执行，hook 用户在发布前不能运行。重复初始化、覆盖已有发布和发布后删除私有锁
均被拒绝；没有清空 slot、移动 runtime、复位计数或 live uninstall API。

安装资格 callback 不是用户 enable 开关。G6 调用方必须先证明所有 frame/hook/queue
改动、代码数据放置、缓存可见性、任务和私有锁存活，并排除后续 I/O 期间的队列删除、
重建与改配置。当前没有提供这一安装器，也没有调用 publish 于设备。

发布时要求私有锁位于 domain0，固定下列实际 queue 对象、表地址、attributes 和 backing；
每次 I/O 准入重新查询并比较。当前原厂配置的 attributes=0，经动态 backing 分配设置128。

|handle|maximum|ring bytes|
|---|---:|---:|
|4b|148|4864|
|4c|312|10112|
|4d|300|9728|
|ab|312|10112|
|4f|312|10112|

任务视图复用实际 TCB 查询，要求完整 ID 的域为0、stack bounds 包含当前 bridge SP。
materializer 只接受 entry603df803；4c/4d receiver 接受603ef892，ab接受603ef94a，
4f/worker接受603f26a1；ACK接受command/worker。producer另由已有自有scope/call链证明
路线。descriptor send 不先拒绝未知handle，因为路由变化仍可能携带待撤销票据。

## 健康状态不撤销上下文

`ep7r_stop` 只拒绝后续捕获准入检查。此前已通过检查的 producer 可以继续完成；
它不是任务静止、队列删除许可或清空所有票据。已发布 context 在 stop/poison 后仍可取得
相同 core、transport 和 cleanup callback，防止既有 job 被误当作 stock 工作直接释放。

forwarder 的退休 owner 按值接管完整票据，并在自己的调用帧内同步完成撤销。
短暂 poll 竞争不释放 descriptor、job 或 key；使用已核对的 raw600313ef 定时delay，
输入固定1个原生单位。清理前后检查私有锁poison；当前任务若本来持有core锁，也不允许
进入delay。未使用会消耗原厂pending wakeup的tslp_tsk。

永久poison、delay非零错误、已发布清理context丢失、实际queue变化均记录fault并停止
新准入，转入自有 `break; bra` 保持循环。自写代码不执行 ACK/free/reset，debugger仅
继续到下一指令也不会落入stock清理。实际exception vector/debugger处理效果仍待G6/设备
资格，不能将此称为已验证的相机恢复机制。

worker cleanup、ACK和已确定拥有者的send布局失败现在调用此保持路径，不再直接降级
到stock ACK/free。接收前的资格失败不消费队列消息。缺少完整调用闭包仍会导致拒绝或
保守保持，因此该实现不能绕过G1/G2/G6准入。

## 定向验证和剩余工作

- [host报告](../../research/ep7/shared-runtime-host.json)：真实bootstrap、poll provider、
  core、transport、job和六个context provider；native环境回调模拟。strict与ASan/UBSan
  通过。故障回调仅在fixture中使用longjmp观察保留对象，生产代码没有longjmp或恢复清空。
- [目标对象报告](../../research/ep7/shared-runtime-target.json)：runtime文本1156字节，
  contexts910字节与4字节slot，native callbacks103字节，保持循环3字节。runtime局部栈
  最大64字节，context最大56字节；完整调用栈及原厂调用段仍需G6计算。
- 六个provider外部符号已关闭；当前集合剩余19项是捕获源接口和18个原厂地址绑定。
  尚未选择CPU postbuilder与该slot的接合，不能据此声称整个H/L执行链闭合。
- 本轮恢复了已停止的Docker引擎。首次目标检查暴露旧raw_callbacks的include路径遗漏，
  已补上provider目录并重跑目标检查通过；没有重复全仓测试、没有SHA或固件整体构建。

下一步将CPU reader接入同一runtime，然后完成捕获源、退出/删除闭包与原生UI，收敛
G6安全放置/初始化/栈预算。C atomic语义、模拟排他与对象符号闭包都不能替代硬件证明。
