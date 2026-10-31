# 候选 H/L 状态、原生锁和最终参数观察器

2026-11-01。S3 的状态/参数子节点通过；捕获控制器、消息运输和 worker 的原生连接
仍继续推进。本次复用 S2 代码实际创建、发布的 runtime，不手写已初始化对象。
[探针](../../tools/ep7_candidate_state_sim.py)和[报告](../../research/ep7/candidate-state-sim.json)
记录 13 次实际候选调用，共 13,672 条指令，不包括复用的启动过程。

## 已执行结果

实际指针链为 runtime `a1dd6108` → bootstrap `a1dd60c0` → core `a1dd4d04`，
其锁 provider 是 `a1dd60e8`。原生 poll `600370af`、signal `60035b62` 和 get_tid
都执行原厂机器码；每次调用核对返回、GCC 被调用者保存寄存器和共享/本地锁释放。

- 将包含零、正负和端点值的 24 个 H/L 设置写入 COLOR3，冻结结果完全一致；
  COLOR2 仍为零。随后将 COLOR3 设置改为零，已冻结快照仍保留原值。
- 通过真实 poll 取得 ID1，使 count 从 1 变为 0。随后编辑的原生 timeout0 poll
  返回 **−50**，编辑返回 false；core、快照不变，provider 不被 poison。真实 signal
  后 count 回到 1。没有直接修改 semaphore count 或注入返回值。
- 不支持的 mode10 返回 false，既有 snapshot 不变，锁正常释放。
- 以冻结快照登记独立 job；原生区域前 15,488 字节不变，扩展的 24 字节正确复制。
  最终 `ep7_gcc_postbuilder_observer` 实际完成 cohort、runtime、登记/结构检查和
  参数写入：**20 个半字 H/L 系数**与现有 LUT/sector 排列逐项相符，976 字节输出
  的其余字节完全不变。该路径 2,490 条指令。
- 真实 `ep7p_release_job` 撤销登记后取消整个 job 的内存映射，再调最终 observer：
  1,298 条指令正常返回，没有访问旧 job，输出保持中性不变。

本次调用相对模拟 GCC caller SP 的最大观测深度 **292 字节**；输入、快照、token、
job、setup、输出均有只读边界 guard。此深度不替代原生任务/IRQ 的完整栈上界。

## 边界与开发中发现

复用现有 `test_direct.c` 的 job/schema fixture，没有重写另一套算法或全量重跑主机
测试。最终核心/observer 的 ABI、锁与值传播得到执行证据，但 job 分配来源、controller
采样时序、队列传输、worker 生命周期仍需其原生路径证据。LUT 沿用比较研究结果，
不表示已完成 E-P7 像素标定、图像质量或实际 ISP 验收。

探针首次调用因第三参数放错在 caller SP+8 而严格停止于 `600c9348` 的未映射读取。
实际 GCC `CALL [],0` 不改变 SP，第三参数位于 caller/entry **SP+12**；按已有目标
ABI 和最终反汇编修正调用 fixture 后通过。没有为此修改生产实现或模拟器。

共享 S2 初始化代码提取为可复用 helper 后，S2 报告重跑与已提交报告完全一致。
本次无 API stub、SHA、生产对象重编译、固件文件修改、更新包或相机操作。
仍需原生生命周期排除旧裸 request 在地址复用后被延迟调用；撤销测试不冒充解决 ABA。

## 复现与后续

沿用禁网、只读仓库/工具卷中的现有引擎：

```sh
python3 /repo/tools/ep7_candidate_state_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-002 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103
```

下一步沿实际 controller/source adapter 和消息/worker 边界推进，明确补充每个新增
现场的来源。S3 尚未整体完成，S4–S6 的加载、归属、完整栈、更新器和恢复条件保留；
候选仍不可安装。
