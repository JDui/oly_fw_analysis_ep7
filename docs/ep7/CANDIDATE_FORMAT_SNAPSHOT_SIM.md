# E-P7 原生未配置格式与 getter 返回

2026-11-01。[探针](../../tools/ep7_candidate_format_snapshot_sim.py)在上游实际暂停现场
继续执行，[正式报告](../../research/ep7/candidate-format-snapshot-sim.json)两 GPIO
路径合计 14,672 条新增指令。原 6065e658 / 60556934 格式 getter 已返回到实际
60427f7d 调用点，产生 150B 记录；该记录表示未配置格式，不能用于证明实机格式。

当前快照仍未返回。它在 60427f9c 对 6229fb98 的第一项 2B 输出 store 严格停止，
MDR 60427f86。下一节点为该原厂输出对象提供经过审查的写入空间。

## 原生重置、默认数据与刷新

|阶段|每条 GPIO 路径的指令数|执行结果|
|---|---:|---|
|606a4a09 完整 reset，包含 606a4a41|1,235|两 selector 写 ffff；123B/121B 数组清零；28B 记录设置两个 −32768 与一个标志 1|
|快照继续|329|到 606d6a41 读取格式 state+295，尚未刷新|
|601f25f8 完整设备默认初始化|5,169|真实对齐指针、三个 ROM 表复制、两个 1084B 二次复制和状态 reset|
|606d47fc 完整模式刷新|563|十次实际属性查询，新增七处字段 store 均匹配真实寄存器值|
|快照继续|40|格式 getter 返回，停止在服务输出对象的首项写入|

606a4a09 的实际调用点为 6065c09a。277B 目的空间从 A5 开始，原先生成的
a2788aa4/10B 参数记录保持不变。a2788ab0、a2788ab2 都由原厂写为 ffff；不能
将其解释为活动格式，也不能用任意零值替代。

设备默认初始化的实际调用点为 601ecdb7。仅增加 3362B 原生写入目的空间；
a271ca70 与 621cf8b8 实际发布 64B 对齐的 a2682d00，另两个指针为 a268daa0 和
a268db40。以下五段复制共 3336B，全部按原始源逐字节核对：

|源|目的|字节|
|---|---|---:|
|6019cb98|a271c5e0|1084|
|6019cfd4|a271ca1c|68|
|6019d018|a271ca60|16|
|a271c5e0|a2682d04|1084|
|a271c5e0|621cfc50|1084|

只映射实际写入范围和单独状态成员，没有把整个设备对象补齐。对象 +1092/+1093
这两个通信字节在 ROM 复制之外，明确使用通信尚未开始的冷 BSS 条件。原
601f4694 从它们实际返回 1；没有提供设备响应或 API 返回 stub。

模式刷新会先读旧 state+295，再从原厂查询更新。仅这一个旧字节使用冷 BSS 条件，
其余新增九个写入字节从 A5 开始。完整函数返回，新增 +11/+12/+295/+296/+298/
+300(word)/+291 均实际写为零，已有前六个模式字段继续通过原查询重写。完整函数
执行不等于其真实任务调度已成立，设备仍处于明确的未就绪场景。

## 输出与验证边界

格式 getter 的原 150B 栈记录中，121B payload 为零、+146 halfword 状态为 2，
符合原生 ffff 未配置分支。记录字节和真实返回 PC 保存在报告，未将 getter 的正常
返回解读为有效活动帧。新增最大观测栈深 500B；上游已经观察到 676B，二者均不是
完整任务栈上界。

```sh
python3 /repo/tools/ep7_candidate_format_snapshot_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

保留[reset 后停止点](../../research/ep7/candidate-format-snapshot-frontier.json)和
[模式刷新后停止点](../../research/ep7/candidate-format-snapshot-mode-frontier.json)。新增正式
返回/150B/停止点断言与下一节点在同一次必要的运行内验证，没有重复容器大循环。

27332B partial capture 不变，独立 geometry/population 未恢复。活动格式选择、帧
参数、完整核心初始化、调用时序及代码/RAM 所有权仍待证。候选 004 与 fishcu
五组件研究容器未改动、不可安装；没有 SHA、重编译或相机操作。
