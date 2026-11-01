# 新节点的原生 event4b 邮箱投递与接收

2026-11-01。已从上一阶段实际出队的新 node `61b21fc0`，执行完整选中通知回调
`602a3042`，经 mailbox1 发送 event4b、设置 flag74，再由完整 `6020c101` 收取同一
消息并归还固定消息块。这里的 flag74 是十进制 ID 74（0x4a）。

证据：[复现工具](../../tools/ep7_candidate_selected_mailbox_sim.py)、
[执行报告](../../research/ep7/candidate-selected-mailbox-sim.json)。

| 实际原生路径 | 新增指令 |
|---|---:|
| 完整 600360b5：冷内核堆初始化 | 25 |
| 完整 60032b6c：静态 mailbox 配方初始化 | 51 |
| 60032ce1..60032d1c：固定消息池1配方及完整构造/堆分配 | 476 |
| 60032ace..60032b09：flag74 配方及完整对象初始化 | 33 |
| 完整 602a3042：event4b 分配、发送、通知 | 1112 |
| 完整 6020c101：取出、复制、归还块 | 618 |
| 空 mailbox 再次 poll | 233 |

合计 2548 条新指令，最大观察新栈深 160B。新增 296B 原生写入容量及 12B 接收输出
容量，没有新增冷 BSS 值、API 成功替身或 SHA 检查。

原 root `600411a4` 给出 heap root `621a63c0`、base `6203c940`、size `b1000`。
原固定池1配方 `6003c0d4` 为 16 个 20B payload、未提供 backing；完整原 allocator
实际从堆尾分配 448B payload 和 20B header，backing 为 `620ed780`。每槽另有 8B
header，完整原初始化生成全部 16 个 free links。只映射这些 header、实际消费的
一个 20B 消息块及必要对象；其余 15 个 payload 和剩余堆保持未映射。

完整原 mailbox 配方创建 ID1 对象 `6219fb74`，选定 flag 配方 `6003a564` 创建 ID74
对象 `6219d2e8`。callback 的正常 status0 是明确输入；node 来自原 selector 返回。
原 task API `6003364a` 领取块 `620ed92c`，`60035db7` 入 mailbox，完整通知链
`6020c15c → 60051078 → 60035a5e` 设置 mask1。原接收 `60033732` 取出消息，
`60034d18` 归还块，池余量依次为 16→15→16，邮箱链表恢复为空。

payload 的有效字段为 status halfword0、event word4b、node word61b21fc0。
中间 2B padding 是原代码未定义的栈残留；检查它被原样复制，不宣称它已初始化。
空邮箱第二次读取返回 −1，输出不变，也没有重复归还块。接收后通知 flag 仍为 1；
控制器的 clear/wait 循环尚未执行。

封存 token2/H/L5/-3、两个 capture 及旧 associated backlink 保持不变。原 kernel
和 provider 锁已释放。该测试在继承的离线任务上下文中顺序调用 sender/receiver，
没有执行 generic engine completion dispatcher、真实任务切换或 selected handler。
冷堆初始化是独立选定场景的上下文构造，不代表运行中可合法重置生产内核堆；完整
内核启动、其他堆对象、动态 mailbox 删除/重建和并发顺序仍待证。

下一步执行 selected handler 到实际 backlink 发布，并继续源复制和异步消费/释放。
候选004和 fishcu 五组件研究包保持不变、不可安装；新请求来源、生命周期、代码/RAM
归属与备份恢复条件仍保留，没有固件重编译或相机操作。
