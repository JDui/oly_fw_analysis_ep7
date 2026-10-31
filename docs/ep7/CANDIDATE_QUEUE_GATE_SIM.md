# 实际发送 CALL 揭示并修复队列 gate 漏检

2026-11-01。接入 S3 消息发送时发现并修复一个生产实现错误。当前后续候选改为
`generated/ep7/offline-candidate-003/`，仍不可安装。

## 错误与复现

`runtime/kernel_gate.c` 原先把 named send 内两处 raw CALL 的返回地址写为
`600514f1` / `60051555`。原厂 `600514ec`、`60051550` 的指令实际为七字节
**DD CALL32**，正确返回点为 **600514f3 / 60051557**。错误常量导致它们被当成
普通原厂调用，候选的队列归属/I/O 关闭检查没有执行。

[修复前报告](../../research/ep7/candidate-queue-gate-before.json)直接执行候选002里的
这两条 CALL、原生 critical entry/lookup 和最终 gate，使用真实 CALL 建立的40字节
frame；外层 named-wrapper 返回标签是明确 fixture。两种异常各走两条分支，
**四次都错误放行**：maximum 从148变144，或候选通过真实 delete observer 关闭 I/O。
没有继续执行被错误放行的 I/O；backing 不映射，候选原文件不修改。

## 修复和最小验证

生产代码只改两个返回常量。静态工具现在按原厂 CALL32 字节、target、mask/frame
推导返回地址，避免复用同一错误列表。原厂88条指令核对通过。

[最终机器码回归](../../research/ep7/candidate-queue-gate-after.json)：

|实际 raw CALL|正常队列|maximum变化|I/O已关闭|
|---|---|---|---|
|600514ec → 返回600514f3|到达正常续接60036f99|拒绝，原厂出口返回−42|拒绝，原厂出口返回−42|
|60051550 → 返回60051557|到达正常续接60036f99|拒绝，原厂出口返回−42|拒绝，原厂出口返回−42|

每条路径先实际执行254条原生指令到gate；四次拒绝均继续执行58条原厂 error epilogue，
SP恢复、共享/本地锁释放。gate内部不调用get_tid、private poll或signal。
两个正常场景停在复制前的正常续接；尚未验证完整消息发送、post-send通知或worker。

## 候选003

[增量构建报告](../../research/ep7/offline-candidate-003.json)来自源码 `296e721`。
复用现有 partial-object compiler，只重编译 `runtime/kernel_gate.c`，其余106个对象
复用；源文件顺序、编译器、全部header/汇编宏/编译配方无变化才允许复用。若共享输入
变化则拒绝增量复用，要求完整编译。

整体链接、101项合成、最终分支/veneer及字节边界检查通过，两个代码区和BSS大小
均不变，全部符号地址不变。与候选002的26,214,336字节镜像逐字节比较，只有：

- `600ca1fc`：f1 → f3；
- `600ca204`：55 → 57。

没有哈希校验、工具链重建、广泛主机测试或相机操作。此前S1/S2/状态/controller报告
保留候选002的历史来源；两处变化不在它们已执行的路径中。本次新探针重新实际发布
runtime后测试gate，没有把此前子节点通过视为整个S3已通过。

## 复现与下一步

```sh
python3 /repo/tools/ep7_candidate_queue_gate_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-003 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103
```

旧失败报告需在生产源尚匹配候选002的版本复现，并使用 `--expect-legacy-bypass`；
该参数是缺陷证据模式，不是准入通过。当前源码检查会拒绝把002冒充最新实现。

下一步从真实冻结scope继续queue4b的完整发送/接收，执行现有通知包装函数、
materializer和worker。关键待证项以及无独立备份/恢复条件保持不变。
