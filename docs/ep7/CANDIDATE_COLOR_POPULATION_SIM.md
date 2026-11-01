# 新分配 COLOR4 capture 的完整填充与 H/L 冻结

2026-11-01。新 ID 2 / node `61b21fc0` 的两段原生 population 均完成，实际候选
观察器读取 raw mode 11、selector 4，并将 token 2 封存。第一段采样后修改当前
COLOR4 H/L，第二段 finish 仍保留原采样值，没有读取新的设置。

证据：[复现工具](../../tools/ep7_candidate_color_population_sim.py)、
[执行报告](../../research/ep7/candidate-color-population-sim.json)。只验证这一条新
分配 COLOR4 的关键路径，没有扩大成所有模式/设置组合。

| 实际路径 | 结果 | 新增指令 |
|---|---|---:|
| 原 pending-node FIFO 初始化片段 | capacity 4，每项 4B | 18 |
| 候选 H/L edit API | COLOR4 的首个 H/L 分区设为 5/-3 | 1220 |
| 原 caller、node 入队、prewrite 与模板复制 | 新 node 入队，6833 word 原样复制 | 50180 |
| 完整第一段与 sample 观察器 | 99 次原属性读取，采样一次 | 16027 |
| 候选 edit API | 当前 COLOR4 首个 H/L 分区改为 -3/2 | 1220 |
| 候选当前 profile 回读 | 确认当前值确为 -3/2 | 1033 |
| 完整第二段与 finish 观察器 | finish 返回 true，封存原 5/-3 | 19353 |

合计 89051 条新增指令，最大观察新栈深 420B。新增 27356B 原生 store/copy 容量：
FIFO 的 26B，加上新 capture 模板目标中原未映射的 27330B；其 offset 27078 原有
2B 保留后再由真实模板复制覆盖。没有新增 BSS 条件，余下 capture slot 未映射。

从真实 node factory 返回点 `602a4485` 继续，完整 `602a3204` 根据继承的
`6223e33c=1、6223dd4c=0` 条件把新 node 放入原队列。随后 `602a44a3` 的候选桥
执行 prewrite、原模板 copy、完整第一段。复制后全部 27332B 与原模板一致；
第一段结束时 capture 的 11/4 与原属性 9481/f6b1 一致，sidecar 前缀持有真实
ID 2 / associated / capture 地址，flags 为 attempted/sample/begun 已置位。

可信 edit API 接受两个明确 24 项输入，仅首个 H 分区与首个 L 分区非零。第一段
采样为 5/-3，之后实际 edit 与 capture 回读确认当前设置已变为 -3/2；两次 API
调用均执行真实私有锁。恢复原暂停栈后，实际 `602a44b5` 桥执行完整第二段，原尾部
512B 清零，核心 finish 返回 1。封存快照仍为 profile index 3 的 5/-3，finish
没有再次调用设置 capture API；最终 flags 为 `[1,0,1,1,1]`。

两次 prewrite 输入都是 `af6037c0`，两次正常返回观察器输入都是 `61b21fc0`，
顺序均为 first/post。第二段返回原 caller 的 `602a44ba`，SP 恢复 `190107b0`；
这不是包围它的整个请求函数返回。旧 capture、ID 1 注册表与原模板保持不变。

当前证明有明确边界：request/format/metadata 沿用之前最初为 ID 1 构造的离线
状态，factory 将 command ID 更新为 2，但完整新请求生产者尚未执行；固定时钟、
温度、设备不可用/格式未配置等原模型继续保留。H/L 输入是可信 API 条件，未测试
GUI 投递或 NVM。associated 的旧 backlink 仍为 `19510000`，必须由 selected
event 的原发布路径更新，才能继续按新 node 验证 source copy 和异步消费。

下一步接原队列领取、selected event/backlink 和后续 job 生命周期；生产内核启动、
代码/RAM 驻留、输入来源与备份恢复仍待证。候选 004 与 fishcu 五组件研究容器不变，
继续不可安装；无 SHA、固件重编译或相机操作。
