# 原生 node 队列领取与资源准备

2026-11-01。完整原回调 `602a2d43` 已从真实 pending-node FIFO 领取新 node
`61b21fc0`，完成两项资源分配与格式准备后出队；再次调用返回 NULL。COLOR4
已封存的 token 2 和 H/L 5/-3 保持不变。

证据：[复现工具](../../tools/ep7_candidate_node_selection_sim.py)、
[执行报告](../../research/ep7/candidate-node-selection-sim.json)。

| 原生路径 | 结果 | 新增指令 |
|---|---|---:|
| 6029d351..6029d402 | 168B engine 参数原生清零/绑定，type 7 | 228 |
| 603dc325..603dc358 | pool 5900 原参数构造 | 112 |
| 603db301..603db32b | pool 3400 原参数构造 | 110 |
| 完整 602a7ce1 | selector format 状态 reset | 5 |
| 完整 602a2d43 | 资源领取、完整格式准备、node 出队 | 2040 |
| 同回调再调用 | 空队列返回 NULL，无资源分配/pop | 20 |

合计 2515 条新指令，最大观察新栈深 208B。新增 379B 原生 store 容量，包括
168B engine、两个各 63B pool header、4B reset、79B 格式成员和 2B node 序号。
另有 24B 明确冷 BSS 条件及 1B 单竞争者硬件锁模型。

engine 参数原生保存 format 指针 `6223d60c`。pool 5900 取得 handle 5901，backing
`dd49c500`、stride 1228800，余量 9→8；pool 3400 取得 handle 3401，backing
`abdf7b40`、stride 256，余量 20→19。两项 backing 内容均未映射。pool 3400 的
对象地址来自原表 `8ff00290`，此处仅建模该对象的读写容量，不代表整块片上地址区
或总线时序已经模拟。

完整 `602a7cf1` 从原属性 18c4 查到 ROM 行 `60079980` 的格式 18，将原记录字段、
指针与资源 backing 写入 engine format。node 原生写入 handles 5901/3401、
1280×960、格式 18 与序号 1；原 pending FIFO 由 count/head/tail=1/1/0 变为
0/1/1。第二次回调只执行 20 条指令，返回 NULL，不重复消费或分配。

坐标 `6223dd5c..6223dd6b` 的生产者属于特殊 associated flag1 / event42 路径，
本场景未执行它们；16B 采用原启动 BSS 的首次使用条件。格式两个扩展 RMW flags
另有 8B 同类条件，随后被原代码置为 1/512，没有补造活动帧坐标。`8fe00010` 初始
空闲字节沿用单竞争者模型，原 BSET/BCLR 及两对 dispatch disable/enable 实际
执行并释放。任务状态/IRQ mask 恢复；保存的 PSW 条件码按本次真实调用更新，
不把此前调用遗留的条件码误当成必须逐字节保持的状态。

此处执行的是完整已注册 selector 回调和原参数初始化；generic engine workrecord
dispatcher、完整 engine 启动配置尚未执行。旧、新 capture 与封存 sidecar 不变，
associated backlink 仍指旧 node。下一步 event4b 的原生投递/接收及 selected
handler，保留新请求来源、调度互斥、驻留与恢复待证项。候选 004/fishcu 五组件
研究包不变、不可安装；无 SHA、固件重编译或相机操作。
