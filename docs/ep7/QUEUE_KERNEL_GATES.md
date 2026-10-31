# Queue 删除期间的候选 I/O 准入

## 本节点完成内容

`runtime/kernel_gate.c`、`kernel_gate_bridges.s` 和共享 runtime 现有具体实现：
在原厂 queue 临界区内确认原对象，在任一选定 queue 删除前永久关闭实验 I/O。
这补上[队列重建审查](QUEUE_RECREATION.md)发现的检查与调用之间的间隙。
尚未安装，也不代表 G2/G3/G6 的全部退出、调用者和启动资格完成。

## 原厂接合位置

|用途|插入位置|已被原厂确认的对象|完整重放区间|正常续接 / 拒绝续接|
|---|---|---|---|---|
|raw receive|60036d3c|A2|60036d3c..60036d46，10字节|60036d46 / 60036e17|
|raw send|60036f93|A2|60036f93..60036f99，6字节|60036f99 / 600370a3|
|delete observer|60031072|A3|60031072..60031078，6字节|60031078|

三个位置均在原厂 `60038594` 临界区入口及非空 queue 查找之后。删除 observer
早于 backing free、两类等待者唤醒、ID 清零。仅匹配已发布的五个 pinned object；
不相关 queue 和未发布 runtime 无动作。原厂删除流程继续执行。

收发仅识别本候选桥的链接返回标签。raw receive 的 native W+32、raw send 的 W+40
分别为返回槽；named send 的两个 raw 返回点是600514f1/60051555，只有匹配后才读取
W+88，即 raw40+named48 的父返回槽。其他原厂调用保持原路径；扩展 queue 的所有
原厂 buffer 容量仍必须另做调用者闭包，不能以该白名单代替。

## 删除与等待的语义

1. 原生临界区内确认 object、ID、attributes、maximum、ring、backing 与发布实例相同，
   才让候选收发进入复制或等待注册。检查中不取私有锁、不查 task、不分配、不等待。
2. 任一选定 queue 的删除先以 atomic store 锁定 `io_closed` 并停止新 capture 准入。
   即使后来同 ID、地址和全部字段完全相同，候选 I/O 也不会重新开放。
3. 已经进入原厂等待的调用由原厂 delete 以 -51 唤醒；`600344b2` 写 TCB+64 并移除
   等待链。receive 负状态跳过长度/复制直接退出，send 返回该状态，没有重试新 queue。
4. 新候选 I/O 拒绝值 -42 经原函数错误出口、原临界区退出和原 RET 返回。named send
   仍经600514b6，保留其结果归一化及60051078通知行为。
5. unlocked preliminary queue query 若遇到删除，看到关闭标记后返回 false，避免把正常
   删除当成必须隔离的 queue mismatch。最终准入仍由临界区内的 gate 决定。

关闭是本次启动永久状态，当前不支持删除后热重启实验 pipeline。runtime slot、core、
transport、旧 job 及清理 context 保持存活；不调用 invalidate-all、不释放、不重新发布。
这允许已有清理继续，但不等于所有丢弃消息都已撤销；队列丢弃票据的最终回收与任务退出
仍须在 G2 中明确。`stop` 不是全局静止，已通过准入检查的 producer 仍可能完成冻结/发布，
其随后的原生发送必须经过 gate 并承担失败清理。

## ABI 与检查

inline 桥自有40字节，保存 D0/D1/A0/A1/D2/MDR，D3/A2/A3由 GCC callee 保存。
保存区12..35完全位于旧 W 以下，GCC return/flush区0..11独立；delete 的原frame24
保存4寄存器，不能套用会覆盖旧 W+8..23 的小型 call observer。恢复后重放完整指令，
然后跳转回原厂，不用额外 RET 改变原返回帧。后续条件判断使用原代码重新设置的 flags。

- [当前输入证据](../../research/ep7/queue-kernel-gate-current.json)：88条精确指令，无SHA。
- [主机检查](../../research/ep7/queue-kernel-gate-host.json)：strict及ASan/UBSan通过；覆盖预查
  期间删除、同址重建永久拒绝、无等待/隔离回调、保留旧 job 和 worker/ACK context。
- [目标对象检查](../../research/ep7/queue-kernel-gate-target.json)：51对象，三个返回标签、
  96条桥指令、八个长跳/调用及两条短分支 relocation。kernel C依赖限制及临界区内使用的
  runtime helpers不含调用/外部依赖；无 LIR/LAR/扩展寄存器依赖。

kernel C文本208字节，桥232字节。桥额外frame40，predicate局部12、admitted44、delete
observer16；这些是局部数据，G6仍需计入所有嵌套调用，不能当成总任务栈预算。
目标检查首次被 objdump 将绝对地址8050显示为附近符号注释挡住；仅规范化该数值内存
操作数的显示后通过，未放宽寄存器或指令序列比较。

## 仍待完成

安装器必须原子落实所有三个 kernel seam、队列尺寸、拥有者帧扩展和 I/O 桥后再发布，
并绑定五个原生续接地址。当前 pipeline 外部符号25个，其中1个捕获源接口、24个原生
地址；新增的5个均为上述确定续接地址。它们仍未链接或部署。
原厂临界区的硬件同步、全部 queue caller/task exit、metadata/descriptor 销毁、任务域、
私有锁存活、完整栈预算及可执行放置继续是 G2/G3/G6 门槛。未开始固件整体构建或刷机。
