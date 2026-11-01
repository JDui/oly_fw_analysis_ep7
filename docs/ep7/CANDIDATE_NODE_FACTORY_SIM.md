# 完整 node factory、关联池 reset 与 fresh 登记

2026-11-01。承接新 capture ID 2 的实际分配现场，原 factory 已完成 pool 3200、
node heap 和 associated 分配，经候选 fresh 观察器返回 `602a4485`，SP 恢复
`190107b0`，A0=`61b21fc0`。新 sidecar token 为 2，尚未开始 population。

证据：[复现工具](../../tools/ep7_candidate_node_factory_sim.py)、
[执行报告](../../research/ep7/candidate-node-factory-sim.json)。复用已有
[固定 heap 布局](RAM_OWNERSHIP_AND_BUDGET.md)与[关联池分析](ASSOCIATED_POOL_LIFETIME.md)。

| 原生路径 | 结果 | 新增指令 |
|---|---|---:|
| 603db2a7..603db2ce | pool 3200 原参数构造，4 槽 | 109 |
| 6029b4b6..6029b4d8 | 原 FIFO 指针发布及完整 header 构造 | 18 |
| 继承空 associated FIFO 的独立拒绝分支 | 原诊断 25002701，fresh 未进入 | 1624 |
| 实际 6029c66f..6029c697 | 候选 reset hook，再执行完整原关联池初始化 | 16850 |
| 实际 factory 剩余路径 | 新 node/associated 分配及候选 fresh 返回 | 10711 |

合计 29312 条新指令，最大观察新栈深 348B。增加 308B store 容量，其中 272B
原来未映射、36B 来自合成保护区重叠；原只读夹具的 41B 实际 store 目的开放写入，
其余 padding/旧 payload 保留原内容与只读属性。三个 16B 旧保护区覆盖真实 free-list
及 slot 1，本次移除后，36B 供原生 store，余下 12B 恢复未映射。

pool 3200 backing=`ae866340`、stride=3087872。原分配取得 handle 3201，池余量
由 4 变 3，原四项、每项 2B 的 FIFO 首次入队，ID 2 注册表 flags 由 5 变 7。
图像 backing 未映射。node 的 56B 请求由完整 `60022700` 分配，使用 CPU0 的
128B payload、192B stride 池，取得 slot 0。只有计数 `62038118` 与 bitmap
`62039cf0` 共 8B 使用原冷 BSS 条件；二者由原代码从 0 改为 1。仅映射 node 实际
写入的 23B，其余 payload、其他槽与 64B guard 仍未映射，未证明生产中的首次分配。

原 associated 夹具的 FIFO 为空，直接继续会在 heap 分配后触发原诊断 25002701。
该拒绝分支单独保留，不把它的分配状态带入完成分支。完成分支执行原初始化调用点
的实际候选桥：先撤销旧 sidecar 登记、保留 generation/serial，再由完整 `602972aa`
清除 25 个 refcount 并入队全部 slot header。随后 factory 原生领取首槽，使 free
count 从 25 变 24、refcount 变 1，node+8 指向 `6223e164`。

fresh 观察器实际查询 ID 2 的 capture 地址 `af6037c0`，生成 token 2；五个
population 标志均为 0。旧 capture 与 ID 1 注册表未变，但旧 sidecar 已被 reset
hook 正常撤销。associated payload 的旧 backlink `19510000` 仍保留；fresh 登记
本来不读取该字段，后续必须执行真实发布路径，不能把它当作新 node 的 backlink。

原初始化片段在独立 scratch stack 上运行，恢复实际 caller 的暂停栈后继续。
这证明选定条件下的代码执行、撤销先后与真实分配，不证明运行中允许 reset 的时机，
也不证明完整启动/并发排除。下一步原 node 准备与 COLOR 两段填充。输入来源、生产
内核配置、代码/RAM 驻留及恢复继续待证；候选 004/fishcu 研究包不变、不可安装。
无 SHA、固件重编译或相机操作。
