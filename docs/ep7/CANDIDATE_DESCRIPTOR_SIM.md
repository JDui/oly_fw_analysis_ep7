# E-P7 原厂 kind19 descriptor 填充与模拟器乘法修正

2026-11-01。候选004的同一份 queue4b 消息现已继续执行原厂 materializer，返回到
router `603dfb7d`，D0=1。没有重编译固件；本节点修正了已定位的 GNU 指令模型错误。
[执行探针](../../tools/ep7_candidate_descriptor_sim.py)复用 message_context 的实际
接收现场，不重新手写票据、runtime 或 capture registry。

## 发现与修复的模型错误

原厂 `603e06bf` 的 `f9 14 d8` 是 `udfu01 216,d0`，用于 class1、ID1 的 identity
entry。旧 GNU 模型把 imm8 符号扩展成 −40；[原厂路径失败报告](../../research/ep7/candidate-descriptor-before.json)
记录7,397条指令后试图写 `a26a07e8`，严格引擎停止。正确槽在 `a26a08e4`，保持
A5且没有把错误地址补成可写内存。

[松下原厂手册第70页](https://www.manualslib.com/manual/119167/Panasonic-Mn103001g-F01k.html?page=70)
要求 MULQIU 的 imm8/imm16 零扩展，64位结果分置 Dn 与 MDRQ。
[固定 GNU 源码](https://github.com/RTEMS/sourceware-mirror-binutils-gdb/blob/87ffb882e0f4d73401a0746177ffabb8e8bbe4ac/sim/mn10300/mn10300.igen)
的注释亦写零扩展，但两处实现误用 `EXTEND8/EXTEND16`。
独立的 [两行修正补丁](../../tools/mn103_mulqu_unsigned.patch)只移除这两个符号扩展；
寄存器乘法、signed sibling、strict stop、MAC模型和runner不变。C/V未定义策略和
flag流水线没有因此取得硅片验证。

[修复前](../../research/ep7/sim-mulqu-before.json)与
[修复后](../../research/ep7/sim-mulqu-after.json)各执行6条独立指令：真实216、
8位高位立即数128、16位32768、高/低结果字、127控制、零乘积和signed −40。
前三种在旧模型失败，新模型全部匹配；定义的N/Z标志亦一致。没有重跑广泛测试。

现有 build 目录增量更新约8秒，旧可执行文件保留，新引擎为：

`/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu`

[构建报告](../../research/ep7/sim-mulqu-build.json)记录8,845,984字节。沿用
[原构建方式](STRICT_SIM_ENGINE.md)，追加 `--unsigned-multiply-fix`；它在独立参考
文件上先应用既有strict patch，再零fuzz/零offset应用本修正，只接受原始、既有strict
或本次精确修正状态。输出新的二进制、日志和报告，旧 `ep7-mn103` 仍可复现失败。
不重新构建交叉编译器，不计算SHA。

## 原厂填充结果

[成功报告](../../research/ep7/candidate-descriptor-sim.json)记录7,413条指令，最大
新增观测深度300字节。之前消息链的6段结果在新引擎上保持一致。

- 同一16字节 command 的 kind19、metadata 指针进入 descriptor，15个候选ID字
  从 metadata+8..67复制到 descriptor+56..115；dispatch 为2001，选中ID1。
- 原厂 registry lookup `6029b9d1` 返回既有 capture19700000，写入 descriptor+28；
  descriptor+116保留ID1。原生 identity lookup的乘法结果为216/MDRQ0，八字节槽
  `a26a08e4` 被实际初始化为status0/count1。
- descriptor最后12字节仍逐字节等于已收到的 `E7T1` 票据，没有重新采样 H/L。
- 原厂数值logger执行53次、字符串logger1次、实际get_tid54次；显式trace mask为0。
  无条件的格式化调用和locale初始化各执行一次，从原厂ROM填充48字节locale结构。
  初始结构/formatter指针为A5；没有用成功stub替换这些函数。

metadata是明确的148字节只读fixture（ID1/dispatch2001，两个可辨认前缀字）；没有
执行其原生分配和全部producer构造。identity槽是独立8字节fixture，不是代际lease。
上游TCB/外围栈/独立queue backing/idle flag及resident代码假设仍保留。函数正常
返回不证明整个router/relay/worker、ACK、取消或相机ISP已完成，完整栈界仍未通过。

## 后续和复现

接下来保持同一descriptor和票据，执行4c→ab→4f下游传递、worker claim、原生分配/
构造/处理/撤销及ACK。队列需在发布前初始化，通知注册继续沿用原厂入口，不能把
未初始化的零通知表当成“通知通过”。先复用现有frame/worker/ACK研究和桥接。

```sh
python3 /repo/tools/ep7_candidate_descriptor_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

旧引擎复现时改回 `ep7-mn103` 并追加 `--expect-legacy-mulqu`。仍无固件文件写入、
更新容器或相机操作；最终封装方式继续按用户要求参考fishcu原项目。
