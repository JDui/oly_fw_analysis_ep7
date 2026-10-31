# 候选 bootstrap：原生信号量与 runtime 发布

2026-11-01。S2 的有条件创建/查询/发布与失败回收模拟已通过。
[探针](../../tools/ep7_candidate_publish_sim.py)从 S1 的真实 create 入口继续执行，
原厂 `6003057f`、槽分配器 `60034f31`、初始化/临界区、delete `60031107` 及相关 helper
均为候选中的原生机器码，没有替换 API 函数体或注入成功返回值。
[实际报告](../../research/ep7/candidate-publish-sim.json)记录三个场景。

## 正常路径

- 原生 create 执行 **316 条指令**，实际分配 ID1，对象 `62199fd0` 来自未修改的
  ROM 表 `6003df9c`。检查 attributes/initial/maximum/count 为 `0/1/1/1`，原生
  等待链表为空，分配计数为 1；共享/本地锁恢复为空闲。
- 候选随后实际执行 core/provider 准备、五队列双读查询和单次发布。自 `60191371`
  候选 CALL 至原厂入口 `6011f620` 共 **52,820 条指令**，runtime 发布到 `a1dd6108`。
- 实际 `ep7r_get` 返回该地址，`ep7r_accepting` 和 `ep7r_io_open` 均返回 1。
  桥恢复原 D0/D1/D2/D3/A0/A1/A2/A3、PSW、原 CALL 的 MDR=`60191378` 和 SP−4，
  然后尾转原厂入口。原厂 initializer 本身尚未执行。
- 本次正常路径相对候选 hook 入口 SP 的观测最大深度为 **356 字节**。没有把它
  当作真实任务栈顶到最低点的完整上界，也没有覆盖 IRQ/其他任务切换。

原生 create 的实际 SETLB 循环会改变 LIR/LAR。此前已核对 Usr3 前缀没有活跃的原生
loop-register 依赖；本次没有添加虚假的 LIR/LAR 保留断言，其他原入口契约明确检查。

## 两条关键失败路径

|场景|原生执行和候选结果|
|---|---|
|自动 ID 分配计数达到 255，所有 semaphore 对象不映射|原生 create 233 条指令后返回 −34，没有读取任何对象；候选继续 15 条指令进入 f04 隔离，未 delete/retry，未发布 runtime|
|队列 4c 的 maximum 为旧值 300，而候选需要 312|先实际创建自己的 ID1；发布拒绝后到达原生 delete，D0=1；delete **384 条指令**正常返回 0，清 ID、分配计数回到 0、释放锁；候选进入 f05 隔离，runtime 从未发布|

失败路径执行的是原生分配/删除和候选回滚，不是提前返回一个模拟错误码。上述路径
没有进入 context-switch 或任务异常 callback。正常与两条失败路径均保留严格未映射访问停止。

## 明确提供的模拟现场

沿用 S1 的 TCB/CPU ID/加载标志/私有 RAM 与栈。新增数据仅包括：

1. `8fe00000` 的单竞争者可读写锁字节。执行原生 BSET/BCLR；不模拟真实总线原子性、
   其他核竞争或硬件 IRQ 时序。
2. 三个 root cell、各 root 的空待处理列表首项 `ffffffff`。三个 root 地址在实际
   初始化器 `60032613`、`60033506`、`600335b6` 的 MOV 指令逐字节核对；对应
   root+332 的列表地址和 root+380 的三核数量也核对。初始化器本身未执行。
3. 分配计数与一个空闲 semaphore slot；slot 地址来自原始 ROM 指针表，原厂代码
   完成 ID 与 spec/计数/链表的写入。
4. 调度未禁用、只有当前任务的一条就绪链：原 root+64=`62192400`、root+68 指向
   `621a63ac`；就绪表头和 TCB 互相链接。delete 后真实调度检查选择原任务，无切换。
5. 五个已经初始化的 queue header，地址读取未修改的 ROM 表 `6003e99c`，属性/尺寸
   取现有 pipeline 契约。其 backing 地址为合成值且**没有映射缓冲区**，证明本批
   没有执行 queue I/O；不表示已经执行真实队列创建、搬运或取消。

探针开发期间严格模型如实停止在三个缺失现场：create 的 `60038582` 访问
`8fe00000`；delete 的 `60031b35` 读取其他核 root cell `8ff00008`；delete 的
`60035965` 读取调度状态 `621a6320`。补充的是上面列明的模型前置条件，不是生产代码
修复或跳过原生指令。其他未知内存仍会停止。

## 当前资格与下一步

这关闭了“整体链接成功，但原生创建 ABI/失败回收和 runtime 发布尚未执行”的空缺。
没有执行完整 boot、真实队列初始化、其他核、捕获/worker 链或物理相机。
代码/RAM 归属、实际启动现场、完整栈、更新器接受性和恢复条件仍未通过，候选仍不可安装。

下一步 S3 复用这个已由真实候选发布的 runtime，首先执行原生 poll/signal 下的 H/L
状态修改与冻结，再接 capture/queue/worker/CPU 消费；不手工写一个假“已发布”对象。
若 S3 需要新增 fixture，必须按实际访问和已知结构明确列出，不扩大为自动零填充内存。

## 复现

复用现有禁网容器、只读仓库与只读工具卷：

```sh
python3 /repo/tools/ep7_candidate_publish_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-003 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103
```

无 SHA、目标对象重编译、候选文件修改、更新包或相机操作。
