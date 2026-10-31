# 实际链接候选：启动前缀模拟

2026-11-01。S1 已完成。直接执行 `offline-candidate-002` 的真实机器码，不重新编译
目标对象，也不把之前的主机 fixture 结果当作本次执行。[探针](../../tools/ep7_candidate_startup_sim.py)
复用现有 GNU 严格引擎、`penf_emulator.execute` 和候选链接器的 ELF 检查；
[实际报告](../../research/ep7/candidate-startup-sim.json)保留执行边界。产物继续不可安装。

后续 [S2 原生创建/发布/回收](CANDIDATE_PUBLISH_SIM.md)已在明确内核 fixture 下继续
通过实际 create/delete 和 runtime 发布。下文仍保留 S1 本身停止于 create 前的边界。

## 输入与现场

实际 ELF 的两个代码段经 GNU objcopy 提取，与当前 decoded 候选对应字节相等；
符号直接读取 ELF，没有只信任旧符号 JSON。实现源、头文件和编译配方相对候选版本
`7386faa` 无变化，107 个对象不重编译，没有 SHA 校验。

候选 decoded main 显式映射为只读/可执行。私有 payload、2 KiB 栈、controller state、
TCB 和内核少量运行字段为合成内存；私有区和栈的前后各 64 字节只读，越界写会停止。
CPU ID=0、当前 TCB 的 tid=2d、entry=601912fb、stack=2 KiB、exception flag=1；
加载完成字段均为 15。这些是测试前置条件，不是已经执行过真实装载/调度的证据。

## 执行结果

|路径|实际结果|
|---|---|
|600201fe 候选 JMP → 已链接冷清零 → 60020204|16,402 条指令；16,384 字节 payload 全零；被检查寄存器保留，D0 为回放原 MOV 读得的值；栈写入限制在原 SP 以下 16 字节|
|602897d7 候选 JMP → 已链接 capture initializer → 602897dd|2,630 条指令；fresh sidecar 仅 initialized 置位，原生 state 写为 0；桥应保留的寄存器及 SP 恢复|
|七组实际安装检查|early、capture、pipeline、CPU postbuilder、input、MVC、owner 均正常返回 1；没有改写私有状态|
|600229ba 恢复旧池上界 32|仅改模拟输入；实际 early cohort 返回 0|
|一座 capture veneer 的 adapter 位移损坏|仅改模拟输入；实际 capture cohort 返回 0|
|60191371 实际候选 CALL → bootstrap → 原生 create 入口 6003057f|12,729 条指令；3 次真实 get_tid；A0 指向栈内 `{attributes=0, initial=1, maximum=1}`；runtime 尚未发布|
|TCB+48 改为 0|553 条指令后进入自有 quarantine，D0=f06；未到 create 入口，未发布 runtime|
|重复 capture 初始化|进入 quarantine，D0=e01；真实终止循环执行 6 步，关闭本核可屏蔽 IRQ，保留 reason 与 SP|

bootstrap 的 3 次 get_tid 分别来自 `ep7n_query_task` 的两次身份观察，以及
`ep7b_prepare` 在 create 前的独立观察。本探针首版错误预期为 2；完整 PC trace 与
实际 C 调用路径解释了第三次调用，修正的是探针预期，生产固件代码没有改动。

到 create 入口为止的已执行路径，SP 相对入口最低下降 **296 字节**；包含最后一条
原生 CALL 已预留的 frame。它只覆盖本次执行前缀，不替代完整 bootstrap/IRQ 栈界。

## 下一条可执行边界

本节点在 `6003057f` **执行前**主动停止；没有注入“创建成功”返回值，没有构造假
信号量冒充内核分配，也没有调用主机 API。S2 从这个实际现场继续检查原厂 create、
其分配/临界区路径、后续队列查询和 runtime 发布；遇到未知访问记录其精确地址与来源。

这里没有证明代码/RAM 归属、上游加载、缓存/其他 CPU、异步生命周期闭包、更新器或
相机运行安全。用户确认没有经过验证的备份和独立恢复手段；继续离线研究，完整目标
与剩余出口见 [刷机资格推进计划](FLASH_READINESS_PLAN.md)。

## 复现

沿用已有只读仓库 `/repo`、只读工具卷 `/work`、禁网 Linux 容器：

```sh
python3 /repo/tools/ep7_candidate_startup_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-003 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103
```

仅生成 JSON 执行报告，不修改候选或原厂输入，不执行刷机。
