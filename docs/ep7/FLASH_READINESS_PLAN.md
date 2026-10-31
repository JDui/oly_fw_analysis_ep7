# E-P7 HSL：从离线候选推进到可刷机包

2026-11-01。当前用户目标是继续模拟测试，最终得到真正可以刷机的固件包；每个关键
节点提交并推送。目标没有缩减为生成一个改扩展名的文件或通过容器校验。
用户确认目前没有经过验证的固件备份和独立恢复手段，先继续离线验证。
用户补充：最后参考 fishcu 原项目的方式封装刷机包。S5 优先复用仓库内继承的
`patches/hsl/pen-f/build.py` 的 `parse → replace_payload → reconstruct` 流程及
`tools/oly_container.py`，使用 E-P7 自己的组件、型号和版本证据；保留没有修改的组件。
上游 PEN-F 的两组件输出、E122 文件名和设备操作不能直接套用。沿用用户要求，
不执行上游 build.py 中的 SHA 检查，必要的原生加和校验与字节回读仍保留。

## 当前基础

当前候选 `generated/ep7/offline-candidate-004/` 在003基础上修复raw receive入口：
107个对象全部复用，重新整体链接和101项修改合成通过，仅两个重定位字节变化。
此前003修复named-send gate返回地址漏检。布局不变，仍标记不可安装。
后续直接测试其实际机器码，复用现有 GNU 严格引擎、
原生片段和容器实现；不重复建立 VM、重写 CPU 模拟器或重跑无关主机测试。
原厂输入保持只读，不做 SHA 校验，不连接或刷写相机。

## 收敛顺序与可检查出口

|节点|直接推进的工作|出口证据|
|---|---|---|
|S1 链接后启动前缀|实际冷清零、capture 初始化、安装检查、bootstrap 至原生创建入口；必要失败注入|来自实际 ELF/decoded 候选的执行报告，记录寄存器、内存范围和真实停止点|
|S2 原生初始化与发布|沿 S1 停止点执行实际内核创建、查询及 runtime 发布；复用已定位的原厂调用/任务/队列配置|正常及创建/配置失败的明确结果，区分原厂机器码执行和必要硬件模型；未知接口不能默认为成功|
|S3 候选处理链|在已建立的原生上下文内执行 H/L 编辑、捕获冻结、队列/worker/CPU 系数链及撤销；关注已有证据中最关键的生命周期空缺|最终链接代码的值传播、代际/取消及中性回退证据，实际内存访问边界|
|S4 驻留与资源|以实际最终布局审查加载、启动前缀、代码/RAM 占用、冷保留时点、缓存/次核和调用栈；有证据不足时修改布局或实现|各实际修改范围的加载/所有权证据，首次使用前就绪；完整栈未知项不能按零计算|
|S5 更新包与恢复|复用 `oly_container` 生成研究包，核对目标型号/版本、五组件、原生校验、更新器验收及写入路径；研究独立恢复|容器和更新器接受性不等于运行安全；安装资格须同时满足 S1–S4 和恢复/验收要求|
|S6 最终资格审查|逐项审查实际包、模拟覆盖和剩余硬件条件；需要真机证据时明确请求必要现场条件|只有证据支持可安装时才能撤销禁安装标记并交付可刷机包；本目标不含自动执行刷机|

S3 的功能范围沿用现有四 COLOR profile 易失 H/L 实现；持久化仍单独登记，不能写
未经证明的 NVM 字段。每个节点记录真实失败和修复；通过不相关测试不用于填补缺证。

当前已知未通过项继续以 [OFFLINE_CANDIDATE](OFFLINE_CANDIDATE.md) 的列表为准。
备份/恢复缺失不阻止继续离线工作，也不会被模拟结果自动视为解决。

## 当前进度

S1 已完成：[实际候选启动前缀](CANDIDATE_STARTUP_SIM.md)通过冷清零、capture 初始化、
七组最终安装检查和四类定向拒绝。

S2 有条件模拟已完成：[原生创建/发布/回收](CANDIDATE_PUBLISH_SIM.md)实际执行原厂
create/delete，正常路径 52,820 条指令后发布 runtime 并回到原厂入口；耗尽 −34 和
队列配置失配后的原生回收均通过。TCB/队列 header、单竞争者锁和空待处理/就绪链
是明确 fixture，真实创建这些现场及多核硬件仍归 S4。

S3 的[状态与参数子节点](CANDIDATE_STATE_SIM.md)已通过：原生 poll/signal 下修改与
冻结、busy −50 无修改、最终 observer 的 20 个系数写入，以及撤销后 unmapped job
不读/输出不变。[controller 与延迟 FIFO 子节点](CANDIDATE_CAPTURE_SIM.md)随后执行了
真实 lookup、启动 helper 搬运、FIFO 初始化/入队/出队，冻结 scope 交接与三个撤销
边界通过。下一步 queue4b 消息及 materializer/worker；原生分配与
时序尚未因独立对象 fixture 自动取得资格。不将子节点通过描述为 S3 整体完成、
整机启动通过或当前目标完成。

接入queue4b时已[复现并修复named-send gate漏检](CANDIDATE_QUEUE_GATE_SIM.md)：两处
原厂CALL为7字节，返回PC由旧f1/55改为f3/57；旧候选四次错误放行，新候选四次
原生拒绝−42并释放锁、两次正常续接。当前继续完整消息/通知/worker，不重复已完成
对象编译和无关主机测试。

[queue4b 消息子节点](CANDIDATE_MESSAGE_SIM.md)已通过实际发送/通知/接收和空轮询。
发现并修正raw receive误绑定函数中段caf为真实入口c8e；修复前−17留队，修复后
返回28、票据完整进入descriptor，空轮询−50清除旧票据。原生通知表初始化/注册和
flag-set均执行，flag等待任务和队列backing分配仍为边界。下一步实际descriptor
materialization、下游queue和worker/CPU/撤销链；S3尚未整体完成。

[原厂descriptor填充](CANDIDATE_DESCRIPTOR_SIM.md)也已通过：7,413条指令，metadata
身份、ID1/capture和同一票据保留，identity槽实际初始化。此过程发现GNU unsigned
imm8/imm16乘法的符号扩展错误，按松下手册修正模型后通过6条定向指令；固件004
未重建。后续引擎用`ep7-mn103-mulqu`。metadata来源仍为明确fixture；继续下游
队列及worker原生分配/处理/撤销/ACK，不把局部materializer通过算成S3完成。

[下游队列与worker领取](CANDIDATE_RELAY_SIM.md)随后完成12段50,621条指令：4c→ab→4f
实际原生复制/接收保留同一312字节descriptor；worker领取原先冻结值，旧有效票据
重放后第二次scope保持全零。4c/4d真实注册flag58并执行通知；ab/4f走原厂无hook分支。
尚未执行中间两段预处理、worker preflight及body；任务交接、空等待flag和独立queue
backing仍是fixture。下一步关闭这些间隔及原生分配/处理/撤销/ACK，S3仍未整体完成。

继续定位capture真实模板：60300055复制6225882c的27332字节，6030002c/60301170
初始化会查询原生属性。定向执行2367条指令后在property2b41的分发表状态a26ffa84
读取处停止；[报告](../../research/ep7/candidate-capture-template-frontier.json)明确
初始化未通过。保留未知属性内存未映射，未把半成品用于capture。

随后[原生属性与模板初始化](CANDIDATE_PROPERTY_SIM.md)在四组原厂ROM/default的1209条
记录注册后通过：原厂复制/打包/注册真实执行，模板7908条指令正常返回。A5诊断说明
初始化只写部分字段，当前正常模板显式依赖已定位的原厂BSS清零范围，DMA未执行；
未导入相机NVM或自动补未知属性。capture尚未复制/改变。下一步接通原厂模板复制与
动态population、两段relay预处理，继续worker分配/处理/撤销/ACK；S3仍未整体完成。
