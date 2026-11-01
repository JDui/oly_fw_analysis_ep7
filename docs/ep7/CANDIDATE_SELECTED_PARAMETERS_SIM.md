# selected handler 的原生参数准备与下一处来源缺口

2026-11-01。原序列状态、场景状态及两项描述符现已由原始代码生成。实际 mailbox1
收到的新 node 进入完整 `602a281a`，第一段 `602a8877` 已返回；第二段 `602a91ee`
停在尚未生产的请求 metadata +50 读取，没有继续到 backlink 发布。

证据：[复现工具](../../tools/ep7_candidate_selected_parameters_sim.py)、
[执行报告](../../research/ep7/candidate-selected-parameters-sim.json)。

| 路径 | 结果 | 新增指令 |
|---|---|---:|
| 完整 602979f8 | 原生清除 6223ceac 的7B序列状态 | 7 |
| 6029cf81..6029cfa6 | 完整 6054b084 读取属性85c1，生成 inactive 场景状态 | 72 |
| 6029d09c..6029d0af | 实际 caller 及完整 602a6583 双描述符构造 | 361 |
| 完整 selected handler 入口到来源缺口 | 第一 helper 返回；第二 helper 停未映射输入 | 906 |

合计 1346 条新指令，最大观察新栈深 156B。84B 新容量全部对应原生 store：7B 序列
状态、1B 场景状态和 76B 描述符成员。没有增加冷 BSS 假设、硬件输入或成功替身。

`602a6583` 从实际 current-command `19c10000` 读取 capture ID2，调用完整
`602ab4ee` 和 `605558bf`。原 class10000 生成 `6223d488` 的 kind10；第二个描述符
`6223d4c0` 来自 ROM 行 `6055d290`，其字段逐项对照原记录。资源指针由原
`6029b986 → 603dba87` 依据 ID2/handle102 取得 `af43ad40`。只提供被实际写入的成员
容量，padding 与 backing 图像未映射。此构造不等于 engine 或 sensor 已完成。

随后完整 selected handler 入口消费原 mailbox 输出 `19c11000`，第一次 helper
`602a8877` 使用 ID2 并实际返回 `602a2838`。第二次 helper 已通过真实请求 ID 与
metadata 指针，最终在 `602a92df` 读取 `6223e482`（metadata+50）时停止。
该位置接下来还要读同一记录的 +48/+52，原先 metadata 初始化只生成了其他成员。
当前保留现场的原 SP/寄存器；没有为这三个未知字段补零或跳过读取。

到此新 capture 发生了 8 个实际字节变化，位于参数/标志字段；报告记录全部 offset
及前后值。封存 sidecar/token2/H/L5/-3、旧 capture 与旧 associated backlink 均
保持不变。完整 selected handler、第二 helper、`602a2903` 的 backlink 发布以及
后续 producer 均未完成，不能将部分写入当作输出完成。

序列 reset 和两个 caller suffix 属于明确选定的原生上下文准备；完整控制器启动、
请求 callback 及这些调用的实际时序合法性仍待证明。metadata 槽仍继承此前的原生
领取记录，完整新请求来源没有因此闭合。下一步追踪其 +48/+50/+52 的原厂写入者，
再恢复当前 selected handler。候选004/fishcu 五组件研究包不变、不可安装；没有
SHA、固件重编译或相机操作，生命周期、代码/RAM 归属和恢复条件继续保留。
