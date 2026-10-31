# E-P7 候选：原生 queue4b 消息与通知

2026-11-01。沿 S2 发布和 controller/FIFO 的实际执行结果继续，不重建手写 runtime
或票据。`tools/ep7_candidate_message_sim.py` 在严格 GNU 引擎执行候选 ELF 对应的
机器码；无 API 成功替身，无 SHA 或相机操作。

## 发送与通知

在冷启动/发布前，使用原厂 `60030c4c` 初始化 queue4b 的两条等待链和环游标。
60 字节 header 的配置取自既有 ROM 绑定，4864 字节独立 backing 是显式 fixture，
不是原生堆分配的证明。随后实际创建锁、发布 runtime、冻结 COLOR2 H0=5/L0=-3、
入队并出队；出队的同一物理 32 字节 scope 交给 patched `602ac869`。

原厂 `6005134a` 初始化三个通知表，`603df7c9..603df7e0` 实际注册 queue4b →
flag203/bit1。事件 flag 对象依据 ROM 指针与 spec 建立为空等待链 fixture。
实际 named-send `600514b6`、raw send `60036ede`、通知 `60051078`、flag-set
`60035a5e` 均各执行一次；32 字节环记录包含长度28、原16字节 command 和12字节
`E7T1` 票据。flag 从0变1，producer scope 变为 consumed。没有模拟唤醒等待任务。

## 接收入口缺陷与修正

[修复前报告](../../research/ep7/candidate-message-before.json)对应候选003：其
`ep7_stock_queue_receive_local_unresolved` 误绑定 `60036caf`，这是静态队列索引检查
窗口，真正函数从 `60036c8e` 开始。遗漏的前缀保存 A0 destination 到 SP+8、D1 timeout
到 SP+4，并检查 dispatch context。现有 assembly bridge 注释与原厂调用均指向 c8e。

实际 patched materializer `603dfc9b` 返回 −1，原生 raw receive 返回 −17；command
保持 CC，descriptor 前300字节保持原样，12字节票据已清零，队列仍保留1条消息/
4832字节空闲。脚本的历史模式只认可这一具体失败，`message_carriage_passed=false`，
不能把“复现断言通过”算成接收成功。

地址绑定现改为 `60036c8e`，证据指向含函数入口/原厂 caller 的 `ep7_queue_transport`。
接下来仅重链接候选004，复用107个未变对象，执行同一场景确认原生返回28和票据回传。

## 边界与后续

TCB 从 controller 显式切到原厂 materializer 配置 ID20/entry603df803/4096栈；
caller ancestor 返回字、外层栈及 idle flag 均为 fixture。metadata 只是未映射身份，
该场景不运行原厂完整 metadata 构造、descriptor 填充、worker/堆分配和 ISP。
两个代码区驻留、私有 RAM 归属、多核/调度和恢复未因这条消息通过取得资格。

复现沿用仓库只读 `/repo`、工具卷只读 `/work`、`rust:1.96-bookworm` 与网络禁用：

```sh
python3 /repo/tools/ep7_candidate_message_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-003 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103 \
  --expect-legacy-entry
```

修复后执行004时去掉 `--expect-legacy-entry`；不覆盖历史失败报告。
