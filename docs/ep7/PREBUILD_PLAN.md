# E-P7 HSL：固件编译前完整推进计划

日期：2026-10-30（Asia/Shanghai）。目标：为 E-P7 1.1 / build1100 / model1420
形成可审查的实现、放置和验证方案，再决定进入首个离线固件候选构建。
本计划不把主机测试、目标对象编译、镜像打包、刷机或实拍验收混为一件事。

## 范围与阶段出口

最终功能目标仍是四套 COLOR 的逐色 H/S/L。第一条验证链选择现有条件
kind19/0x2001、原生 CPU COLOR 分支；不把 RecView 的 kind16/0x100d 当正常拍摄。
第一阶段 H/L 易失、重启归零，这是已有原型范围；持久化另有明确关卡，不能据此
宣称完整产品已完成。未经资格验证的模式保持原厂行为，H/L 不介入。

“允许开始编译固件”指完成下面 G0–G8 的离线构建准入审查，随后可以构建一个
明确标记不可安装的离线候选。当前不生成修改固件、不安装 hook、不连接相机。
主机 C fixture 的编译与执行可继续；目标交叉工具链建设归环境路线。
实机恢复与画质验证是更晚的安装关卡，不以主机通过代替，也不假装能在编译前完成。

## 依赖与执行顺序

主线：G0 → G1 → G2 → G3 → G6 → G8。
并行准备：虚拟机环境 E；G4（UI）、G5（持久化）、G7（更新/恢复研究）。
G6 依赖 E 的工具链设计和 G1–G4 的候选接口；G8 汇合全部结果。
优先关闭真实阻塞，不以新增测试数量衡量进展。

|阶段|要做的工作与交付物|通过条件 / 当前情况|
|---|---|---|
|G0 输入与证据台账|固定支持版本；确认本地原厂输入、解码文件、工具链是否存在；区分历史报告与本次重跑；清点未提交改动|已建立本地输入/工具目录；原厂整包五组件结构/加法和/回转检查通过，binutils2.45/GCC13.4已本地构建并用于静态/对象检查。历史静态报告不能声称本次重验。使用来源、头字段、长度、精确指令及必要字节比较；不做 SHA 校验，不删除旧工具保护来伪装通过|
|G1 节点身份与释放闭包|列出新建、提前入队、population、选择、别名、释放、状态切换和初始化；逐项绑定原生寄存器/栈与排他区间|13 个已知节点 free + 两个状态服务 seam 已整理；原生覆盖尚未闭合。必须证明新建资格、先准入再读前缀、每个支持的 free 前撤销、33→33 失效，明确未支持分支|
|G2 图像快照输送|原始节点→associated→metadata→300-byte descriptor→fresh job 的身份、extent、代际与所有权表；正常/失败/重复/取消/ACK 路线|不能靠裸 metadata 地址查当前 token，也不能读未证明分配的尾部。选定显式携带 capability 的路线或证明受限单所有者路线；缺失资格永久中性，禁止晚读当前 UI 补填|
|G3 任务域与启动同步|GUI、捕获 producer、kind19 worker、CPU reader 域；私有锁创建/发布/失败回收、重入、可见性和 shutdown 策略|复用 poll-only provider 与 bootstrap；同域没有证据就不能启用。跨域时使用有所有权的值复制与显式发布协议；保留硬件可见性待测项|
|G4 原生 UI 与文本资源|E-P7 自身输入路由、焦点、完整拨轮计数；H/L category 创建/挂接/失败清理；字体布局、销毁与恢复 S 行为|复用 raw/UI router、text formatter、rollback；落实 allocator context 和初始化成功条件。未闭合前 renderer_ready 保持 false；Delete 的路由资格不能凭逻辑事件名假定|
|G5 H/L 持久化决策|研究设置存储/reset/recall 的真实所有权，制定四 profile 保存、恢复、升级兼容、断电语义|未证明可用字段就不得写 NVM。首个易失候选可以显式排除持久化；完整 HSL 产品仍保留此任务，不借用 PEN-F 偏移或任意 padding|
|G6 代码/数据放置与 ABI|ROM/RAM 使用与启动生命周期；每个 hook 的完整被替换指令、短跳距离、trampoline/重定位、寄存器/flags/MDR、cache、栈最坏路径、runtime 分配与安装顺序|输出放置图、符号/外部依赖清单与尺寸/栈预算。全零/FF 不等于空闲，不能仅凭链接成功认定安全。工具链就绪后仅做必要对象级检查，固件整体构建仍留在 G8 后|
|G7 更新器与恢复准备|整理 E-P7 model/build/component/length/checksum/验证与写入路径；设计无写入的验收 harness；记录恢复入口证据、失败域与台架计划|复用现有容器工具；不重造 packer。离线构建前须明确支持/未知项与禁安装标记；真实独立恢复证据和用户授权是之后安装的额外硬门槛|
|G8 编译前审查|冻结首候选支持矩阵、所有 ABI/生命周期接口、实现状态、构建清单、最小验证矩阵与未决项；检查每条接入是否有证据|没有未解析的必需符号、虚构锁/生命周期保证或未资格化的可执行区域；首次候选仍不得标为可刷。产物计划只描述版本/路径/内容，不生成升级文件|

## G1 当前可执行批次

1. 汇总三组既有探针中的 13 个节点释放 call，明确 wrapper/metadata 非节点释放。
2. 用源文件 AST 读取现有指令 witness，不导入/执行会校验固件哈希的探针。
   清单核对只证明本地证据引用一致，不证明固件字节或整个控制流闭包。
3. 按支持的 state33 producer 逐条追踪节点别名与释放；条件分支没有排除证明就保留待审。
4. state34 两处释放只有在所有离开33的状态提交已同步撤销后才能不再安装节点 hook；
   目前不得直接标作“不需要”。state33 重入同样撤销，255 不提交。
5. 下一段重点：event4c 的 wrapper queue、global6223dd54、async descriptor6223df64，
   以及 deferred service/secondary cancel 的重入与排他契约。

本轮交付：[生命周期清单](LIFECYCLE_HOOK_INVENTORY.md)、
[结构化清单](../../research/ep7/lifecycle-hook-inventory.json)、
[核对脚本](../../tools/ep7_lifecycle_inventory.py)。

## G2 需要定案的路线

当前两条正常 metadata 路径均已有候选接合：立即 `602ac3de` 使用本次 scope，
忙碌入队 `602ac3f6` →出队 `602ac5e8` →`602ac60e` 使用按 ring 位置保存并移交
的冻结值。见[等待队列承载](DEFERRED_PRODUCER_CARRIAGE.md)。这关闭了正常 deferred
路径的代码缺口，没有关闭 controller 排他、间接别名、放置与安装准入。

优先复用已实现 controller sidecar、按值 snapshot、direct reader 和 fresh-job 生命周期。
元数据是否扩展必须以分配 provenance、存活和传递能力决定；148→192 只是曾审查的
分配候选，不是默认已获批准的布局。拒绝两个捷径：裸指针重新绑定当前 generation；
根据 kind19/tag 先读取不明 tail。所有权表要包括 send 失败不擅自 free、early callback
排除/覆盖、正常 ACK 前 job cleanup、重复/取消与地址复用。

## 环境并行分工

独立聊天“EP7 固件研究虚拟机环境设计”使用 gpt-6.1-terra / max，负责
`docs/ep7/VM_ENVIRONMENT_PLAN.md` 和独立环境记录。它与本聊天共享工作区，
不修改生命周期代码和本计划。首轮只设计和只读调查，不安装大型组件。
主聊天负责路线收敛与 G1/G2；环境设计完成后将工具链/模拟边界接入 G6。

## 最小验证策略

- 本轮只运行生命周期证据清单核对，已有 sidecar strict/ASan 结果保留为上轮证据。
- 若改动捕获输送代码，只跑该链路：四 profile、早期发布、一次 seal、复制冻结、
  撤销/复用、失败/取消；不重跑全部数百项测试。
- 原生静态重验仅选新结论涉及的窗口和精确指令；输入不匹配立即拒绝。
- 模拟器仅覆盖已建模 CPU/内存/API 契约；像素/ISP、硬件时序、cache 和恢复不能虚报。
- 每个报告记录执行范围、实际通过与未执行项。所有 SHA 校验本轮省略。

## 当前编译准入结论

[event42独立队列](CONTROLLER_EVENT_QUEUE.md)已确认queue0x67、12字节消息、flag74/bit4
通知和controller的60289b97分派点，与engine的mailbox1/bit1输入分开。121条指令、
8项数据及有限CFG核对通过；当前handler正常返回后，循环才再次接收event42。此结论
不覆盖外来直接调用/异常重入，也不把两通道当作同一FIFO；G1完整释放闭包仍待完成。

[两个回调写入范围](CAPTURE_WRITE_WINDOWS.md)已用完整原生callback/坐标helper执行
137+41条指令，所选路径只改node坐标和完成标志，ID+0与associated指针+8保持原值。
这排除了两个具体直接写入与新增身份读取的重叠；没有证明事件驱动的释放或冻结区间
存活。继续核对source上游event42→立即copy/等待入队的顺序及对应释放边，无生产对象重编译。

[TOP触发与完成链](TYPE7_COMPLETION.md)已接通条件下的lower92→sensor71→lower85→
upper135路线，以及136字节描述符保存原engine、完成时读取engine+64的关系。
150条指令和4项分派表核对通过。优先级阈值2的入口包围不等于全部回调互斥，
资源释放/取消未闭合。后续按[新增读取责任表](CAPTURE_READ_OBLIGATIONS.md)聚焦
associated/backlink、node前缀及capture profile的实际读取区间，避免扩大为无关
原厂字段恒定的证明；原G1/G2/G3/G6/G8门槛不变，整体编译尚未开始。

[type7 TOP工作队列](TYPE7_WORK_QUEUE.md)已接通普通提交的三字载体、type135/type149
消费者和engine+64完成分派。两次原生入队/出队执行共167条指令，发送缓冲覆盖后仍
保持原值；engine指针目标全程未映射，不能解释为深复制或生命周期租约。普通submit
丢弃入队状态；继续审查消费者调用域、60120d73及取消，未以零返回推定完成或放行G8。

[type39首阶段IRQ入口](ASYNC_IRQ_DOMAIN.md)已接通domain0的初始化注册、ROM类表、
kernel分派与队列consumer，确认class5/source29路径。92条指令、3项配置和一次
18指令原生片段执行通过；handler在consumer之前重开IE，不能假定回调都在controller
任务内串行。第二阶段与type7工作队列消费者继续待审，未据此启用跨上下文共享或放行G8。

[mailbox管理槽来源](MAILBOX_REGISTRY_LIFETIME.md)已确认正常+4句柄来自内核create，
外部注册表ID不是原始mailbox ID。原生片段执行同时证实reserve提前设置active、
release保留旧句柄，delete前缀可读取该旧值。71条witness及四次短执行通过；这是局部
发布窗口，不是已观测的并发事故。全别名与mailbox1永久存活仍未证明；下一项回到
type7/type39实际完成域和取消汇合，不能用管理槽active代替生命周期资格。

[次核等待前调用闭包](SECONDARY_PREBARRIER.md)已确认60054a7a仅调用UART输出和可选诊断
ring写入，无allocator调用。两条实际入口在明确冷现场下各执行81条指令到等待点，
release的零/非零分支通过；未访问堆。诊断启用时仍有指针写入，实际清零/硬件启动与
跨核可见性未证明，不能提升为全核静止、RAM独占或完整启动通过。

[早期装载执行](EARLY_LOAD_EXECUTION.md)已确认657,408字节实际拆为三次底层读取；
显式成功存储模型下，两处RAM哨兵加载、执行与重载通过。失败注入同时证明：底层不搬运且
返回ffffffff时，原厂包装器仍返回0。因此到达600201fe不能独立证明新增代码驻留。
底层NAND/DMA、启动前缀上游加载和区域所有权仍未闭合，未据此放行代码区或开始整包编译。

[大块池边界原生执行](POOL_RESERVATION_EXECUTION.md)完成7次定向调用：缩为31槽后的
新分配、释放和有效回收符合预期；旧回收栈中的槽31仍可返回待保留地址。因而两处池上界
必须在首次分配前生效，晚安装明确不可用。耗尽和非法释放只执行到诊断入口，未假定返回。
启动前缀加载、真实池初始化/guard责任及容量资格仍待闭合，私有RAM仍未获得放置准入。

[严格指令环境](STRICT_SIM_ENGINE.md)已构建并执行六个定向场景：未知取指/syscall停止，
原厂MAC helper的两种MCVF回转和任务异常查询的两条分支通过。复用已有GNU核心与
wrapper，无SHA、无新CPU实现。后续据此推进原生加载/所有权片段；工具构建及合成
现场回放不能替代G6/G8的启动前缀、放置和生命周期准入，未开始新固件整体编译。

[冷启动现场准入](COLD_CONTEXT.md)已实现：创建锁前观察TCB+48、内核嵌套/锁状态及
关键回调配置，失败不改写内核资格、不创建锁。自有quarantine已移除BREAK，改为
6字节、body栈0的本核终止循环；3个变化对象及最小host/GNU语义检查通过。
原厂BREAK、资格有效期及IRQ/context等余项仍未通过，未开始整包固件编译。

[bootstrap C栈图](BOOTSTRAP_STACK.md)现有43函数和29条固定callback，增量重生成2个
变化单元并复用16个未变单元；后续
[原厂栈节点](NATIVE_BOOTSTRAP_STACK.md)核对27个函数及997条不同地址指令，明确
固定回调、保存/替换SP和任务入口4字节开销。当前合并已知部分为栈顶以下416字节；
任务异常callback及BREAK/IRQ仍未定界，完整上界保留null。这不是2 KiB栈通过证明。

[IRQ栈切换](IRQ_STACK_TRANSFER.md)现已核对117条witness和14个返回后可达函数：
独立8 KiB IRQ栈有明确保存/恢复点；单次显式软件部分56+40字节，GNU入口模型另8字节。
五个UDF已有手册对应，0800退出mask会屏蔽普通IRQ；TCB+48在查询时为1的条件路径
已知96字节，原通用104不变。条件有效期、context恢复和故障仍未闭合，完整上界保留null。

[统一安装清单](INSTALLATION_MANIFEST.md)已汇合101项、546字节；107个生产对象统一
首次统一编译通过，当前增量刷新后345全局定义无重复，84个安装目标存在。109外部依赖均已分类，108有既有
原厂地址，私有RAM符号仍无最终值。3处启动前缀修改的上游装载路径仍未资格化，
完整栈、代码/RAM放置及生命周期关卡未通过；未开始整体固件编译。

[一次性bootstrap](COLD_BOOTSTRAP.md)已实现：早期安装组→私有锁/core/runtime→单次发布，
失败不继续启动改造后的接收任务。15个定向host场景、48项安装组负检查及桥语义通过。
当前永久存储计入后静态8,084、text46,800；全栈及放置/生命周期资格仍未完成。

启动入口已收敛到[Usr3的60191371](BOOTSTRAP_ENTRY.md)，位于接收任务启动前。
须分离早期pipeline/kernel安装资格与后续第6段UI资格；等待全部段才发布会产生启动依赖。
85条指令和10条任务配置已核对，具体bootstrap已在后续节点实现，完整栈与放置尚待完成。

**未就绪**：G1 原生捕获/释放闭包、G2/G3 退出与queue/task存活、G4 GUI串行所有权/旁路、
G6 放置/安装仍未闭合。G4的资源、内容对象、输入与COLOR gating已有软件接合；
generation-bearing handoff、共享runtime发布和CPU reader已有
实现；具体证据见本页末尾更新。继续离线研究，没有可承诺的安全试刷时间。

以下为各节点当时的进展与后续项，保留作证据索引；当前待办和数值以上述准入结论为准，
不把已经完成的旧“下一项”再次当作未做工作。

过程记录：[当前工具链](CURRENT_TOOLCHAIN.md)、[异步别名接合](ASYNC_NODE_ALIASES.md)、
[异步调度生命周期](ASYNC_DISPATCH_LIFETIME.md)。G2已实现
[一次消费快照票据](../../prototypes/ep7_volatile_hl/snapshot_transport/README.md)，
并接入实际主机处理链。不在异步回调中重新查询controller sidecar。
[承载路线](QUEUE_TICKET_CARRIAGE.md)已选定：独立缓冲区编码28/312字节消息，
原生前缀保持16/300字节；三个队列的配置与所有接收适配须一起闭合。
154条指令及9项配置数据已核对；wire编解码strict/ASan/UBSan和目标对象检查通过。
下一项为raw receive实际长度ABI、所有受影响接收点及精确seam的显式上下文绑定；
原始receive不接受容量参数，不能直接让旧stock buffer接收扩展消息。

本地raw队列ABI及pipeline票据撤销已实现；[五个descriptor栈对象的扩展计划](DESCRIPTOR_FRAME_PLAN.md)
核对通过（53指令、4任务行、9个同宽指令片段）。下一项为command独立scratch与
owned descriptor receive适配，随后落实三个materializer调用链的寄存器/栈ABI。

owned I/O已经实现并通过定向strict/ASan/UBSan及目标对象检查，见
[主机报告](../../research/ep7/owned-queue-integration-host.json)。command使用148字节独立scratch，
descriptor要求真实312字节拥有权；发送先消费票据，失败/legacy路径保留清理义务。
首次sanitizer超时未复现，原因未定位；报告保留此记录。下一项是materializer三调用链
的具体栈资格和桥接，原生backend、安装/任务域仍未绑定。

[materializer接收桥](MATERIALIZER_RECEIVE_BINDING.md)已实现，包含三种调用链的有界
栈映射和本地raw receive接合；strict/ASan/UBSan及目标对象检查通过。context provider
仍作为未解析符号等待G3/G6，未绕过资格条件。其余relay/worker收发与claim/retire继续推进。

[descriptor接收桥](DESCRIPTOR_RECEIVE_BINDING.md)已覆盖四处直接接收及两条共享helper
调用链；共享范围检查复用于materializer。未知非扩展队列按原ABI恢复原厂接收；
扩展队列未知消费者拒绝，等待完整闭包。下一项为发送桥及消费/清理接合。

[descriptor发送桥](DESCRIPTOR_SEND_BINDING.md)已实现：三种拥有者布局、旧格式回退、
失败/route变化票据清理接管，host和目标对象检查通过。G2剩余producer command、
worker claim/retire、drain/失败路径接合；G3/G6仍须实现真实context provider和安装组。

[producer scope](PRODUCER_SCOPE_BINDING.md)已实现并通过host/目标对象检查，metadata仍148。
发送路径发现并修正raw发送绕过原厂通知的问题，改为调用600514b6；没有原生部署。
G2尾端仍有worker claim/retire和drain/失败处理，snapshot来源与任务/安装provider尚未绑定。

[owned consumer](OWNED_CONSUMER.md)已实现一次领取和幂等撤销，host16-job链及目标对象检查
通过。失败锁保留清理责任并禁止后续claim；原生worker job/cleanup、ACK/drain与失败保持
策略是下一接合点，不能把portable完成结果等同于原生free前已撤销。

[worker allocation/process/cleanup桥](WORKER_JOB_BINDING.md)已按原厂seam实现，自有scope
跨越原job函数；host与目标对象检查通过。实际等待/稳定context仍未绑定，不能将重试循环
视为已验证RTOS策略。下一项为ACK/drain撤销与G3运行时供应，随后集中关闭未解析provider。

[三处ACK/drain接合](ACK_DRAIN_BINDING.md)已实现并定向验证，保留原厂通知与返回行为。
G2的主干代码已有producer/relay/worker/ACK，原生闭包和provider稳定性仍待审；下一批
集中处理G3真实task stack/domain、runtime发布及poison/等待策略，不把未解析契约当完成。

G3已取得并实现[原厂当前TCB栈边界](CURRENT_TASK_STACK.md)，复用get_tid桥且完成定向检查。
下一步用该只读事实构造共享provider；安装标记、私有锁稳定生命周期和永久poison处置
必须独立绑定，不能因能读到TCB就自动开放捕获或释放路径。

G3的[定时delay与清理进度约束](CLEANUP_PROGRESS.md)已核对并提供可调用ABI桥，排除会消费
既有唤醒计数的tslp_tsk。共享provider实现须分离永久发布/停止新准入，保留poison后旧工作
的context；等待/隔离策略未绑定前，worker和ACK中的待清理循环仍不可安装。

[实际队列视图](RUNTIME_QUEUE_CONTEXT.md)已实现并通过最小定向检查，查询实际对象与backing，
不再将ROM配置值等同于运行时容量。下一项共享runtime发布/清理策略；queue删除重建的
排他期依然必须由安装与退出闭包提供，不能用两次相同读取替代。

[共享runtime](SHARED_RUNTIME.md)已接入六条context provider：单次发布、五个queue实例
固定、停止新准入但保留旧context、清理等待/poison保持均有具体实现与定向检查。
这关闭了接口空缺，没有关闭安装资格；下一项CPU reader共用该runtime，随后退出闭包、
捕获源/UI和安全放置必须继续完成。不能因符号数变化把G3/G6整体标记通过。

[CPU reader](RUNTIME_READER.md)现经同一发布slot使用worker core；定向host与49对象检查
通过。下一步不再新增context接口，集中审查退出/queue删除和捕获源身份/排他，再推进
G4资源与G6完整stack/放置/启动，直到满足G8后开始整体固件编译。

[queue重建审查](QUEUE_RECREATION.md)确认当前自动ID池1–255包含全部pipeline编号。
删除清ID后可用新spec重新分配；双读queue view仍不构成I/O存活锁。下一步明确删除调用者
和正常/失败退出，落实不可重建的实例保留或完整静止协议，然后才能放行G6发布。

[临界区内queue gate](QUEUE_KERNEL_GATES.md)已实现：候选I/O复制/等待前核对发布实例，
删除前永久关闭候选I/O，保留原厂删除和-51唤醒；同址同配置重建不能重新准入。
88条原厂指令、96条桥指令、51对象及定向host检查通过。尚未安装，不能因此宣布
退出全闭合；下一项继续捕获源身份/释放、队列丢弃票据回收及G4/G6绑定。

[捕获两阶段流程](CAPTURE_POPULATION_ENVELOPE.md)已落实到现有sidecar：第一段sample，
第二段finish才允许输送；早期copyout永久中性。实际16-job软件链验证两阶段间UI修改
不改变原快照，producer任务限定到实际controller entry60289852。83指令/任务行核对
包含13个已列node free；下一项将真实node/prefix/token接入这些原生边界及初始化/释放。

[原生capture source候选](CAPTURE_NATIVE_BINDING.md)已提供实际provider和初始化/登记/
population/free/pool-release桥。56对象中自写provider符号已闭合，32个剩余外部符号均为
原厂地址；118指令、123条新桥指令及定向host通过。代码绑定不替代controller排他和
全部retirement/repopulation闭包；G4资源、G6放置/短CALL重定位/启动/总栈仍为准入门槛。

[UI 分配器上下文](UI_CONTEXT_BINDING.md)已绑定实际 service getter 和两字节选择方法，
复用原有 fresh-text rollback，销毁后可恢复先前选择而不读取已释放对象。
59 条原厂指令、9 个目标对象及定向 strict/ASan/UBSan 检查通过；仅关闭上下文回调的
实现空缺。GUI 串行所有权、文本资源/初始化、category4/5 创建/挂接仍须完成，
`renderer_ready` 保持 false，整体固件编译准入仍未通过。

[UI 资源来源](UI_RESOURCE_ORIGIN.md)已将启动初始化数据段连接到 `61fb7070` 资源表
和 `61fc3874` 父回调表，定位四个原厂文本描述符及两组实际布局。搬运参数和关键字段
已在当前输入核对；硬件 cache/启动成功与后续表改写未验证。下一项保留原厂工厂的
初始化返回值、保存/恢复 allocator context，再完成实际挂接/失败清理和 H/L viewer。

[原厂 text factory result](TEXT_FACTORY_RESULT.md)现已通过 GCC veneer 同时返回 child
与原生初始化状态，并在正常返回时恢复先前 allocator selection。115 条原厂指令、
28 条新桥指令和 12 个目标对象通过定向检查；失败且非空的 child 明确保留回滚义务。
下一项实际生命周期回调/资源副本/parent attach 与 H/L viewer 接合，G4 尚未整体通过。

[原生文本生命周期](TEXT_NATIVE_LIFECYCLE.md)已把 factory/attach/bind/set/rollback 接入
现有 C 流程。确认精确 parent 的正常 bind 返回 -1；按 parent 字段和事件结果正确
归一，attach 成功后不再独立 free，cleanup 拒绝则保留待清理对象。96 指令/7 vtable、
定向 strict/ASan/UBSan 和 15 个目标对象通过。真实 owner 入口/退出、descriptor+12
及独立 ID/资源副本、H/L viewer 仍待接合，未安装或启用 renderer_ready。

[显示 owner 生命周期](UI_OWNER_LIFECYCLE.md)已确认 descriptor+12 的空导航表分支、
bind 时填充子控件、bulk cleanup 与析构的不同责任；纯析构只清列表节点。文本创建
现查询实际 child ID 冲突，桥保存/恢复 owner+108 共享遍历游标。124条原厂指令、
12项数据、16个定向host场景和16个对象通过。下一项具体 owner 捕获/撤销 hook、
独立资源副本及 H/L viewer；没有将已知调用位置等同于已安装的生命周期闭包。

[request278 显示切换](UI_SCREEN_ACTIVATION.md)已定位 service+784 的实际 manager、
type6111 描述符和 service+416 发布顺序：新 owner bind/draw 后才回收旧 owner。
新增112字节专用文本资源，复制原厂index53，仅改独立ID和自有layout指针，保留空
导航表。目标对象构造器72字节，17对象通过；未重复跑未改动host测试。下一项在完整
manager前后接捕获/撤销，并覆盖bulk cleanup/析构，再汇入 H/L viewer。

[显示 owner 接合](UI_OWNER_BINDING.md)已实现完整manager前后桥、匹配owner的
cleanup/bulk/析构撤销、实际四表项cohort及真实来源qualifier，复用已有text生命周期。
30条新增原厂指令、4表项、12组strict/ASan/UBSan和21对象通过；bare destructor与
重入销毁不会静默丢掉child。fresh保留仍要求原生allocator存活证明，四表项匹配也
不代表安装/排他/旁路闭包。下一项MVC parent/session、category4/5与实际输入资格，
`renderer_ready`继续关闭，G4/G6/G8尚未整体通过。

[selector 六项存储](UI_SELECTOR_STORAGE.md)现复用原厂 ID193 initializer 与数组分配/
释放方法，在成功初始化后建立真实6值/12字节mask；新增分配失败保持完整原4项。
81条原厂指令、5数据项、4组strict/ASan/UBSan及7对象通过。H/L两项默认禁用，
原厂自身的mask分配失败缺口未在本批修复。下一项MVC内容对象与viewer生命周期，
随后绑定COLOR gating/输入/显示再开放新类别，不把存储扩展当作H/L界面完成。

[MVC 生命周期](UI_MVC_LIFETIME.md)已把完整GUI041d创建/发布与exit、parent/viewer
析构接入实际登记。确认首次draw早于全局发布、退出时parent先于viewer；关系变化
锁存失效，同址恢复不能复活旧代。98条指令、8数据项、6组host和11对象通过。
下一项在此来源内接H/L内容对象/重建、viewer和UI session，再关闭实际输入provider；
当前没有把登记成功等同于renderer_ready或原生安装闭包。

[独立H/L内容重建](UI_CONTENT_REBUILD.md)已实现56字节私有child、18槽vtable和
原生析构；分配失败保留旧内容并恢复两处类别索引，H/L切换复用已拥有对象。
全main引用扫描补出第四处重建调用60e269f0，四处CALL全部加入实际cohort检查；
96条原厂指令、6组新增+6组复用host场景和13对象通过。H/L mask仍禁用，没有
开启renderer_ready。下一项将UI session/同一runtime core接入这些对象，再汇入
viewer/显示owner和真实输入资格；G4/G6/G8仍未整体通过。

[共享core与显示接合](UI_VIEWER_JOIN.md)现复用已发布runtime的同一core和portable UI，
使用独立session serial，连接完整viewer返回及request278 owner完成两个时点。
文本更新在MVC/text双重busy保护内，失败锁存owner不可显示，撤销不清图像快照。
115条原厂指令、7组新增+12组复用host和41目标对象通过。H/L mask仍禁用；下一项
落实实际事件域/完整拨轮delta、input provider和COLOR gating/禁用归一，再关闭
G1/G2/G3退出及G6放置/安装/总栈。整体固件编译仍等待G8准入。

[实际输入接合](UI_INPUT_BINDING.md)已实现完整preprocess/engine scope、五处完整拨轮
计数来源、container返回PC资格和一次消费；MVC与显示owner持有覆盖整个raw dispatch。
INFO独立分支也要求实际input gate为0，并复用原厂队列去重。178条原厂指令、8组新增
与19组复用host和47目标对象通过，admission软件接口空缺已关闭。H/L仍默认禁用；
下一项COLOR gating、失效归一和相关计时/重建状态，然后继续G1/G2/G3/G6关卡。
这些对象检查不是整体固件编译，尚未达到G8。

[COLOR资格与失效恢复](UI_COLOR_GATING.md)现已接入真实mode/runtime/selector/input/owner
条件，运行时只写H/L两项mask；失效撤销并恢复仍可用原厂类别。针对通用工厂的NULL
后写缺口，复用原三个完整创建器，在有效对象就绪后才销毁H/L；失败保留现有所有权。
同一engine事件归一后不能再送入原厂S，跨类切换清理相关计时/pending状态。
135条原厂指令/7组数据、8组gate host及受影响输入回归、51目标对象通过；没有SHA。
G4的COLOR启用/退出软件空缺已关闭，尚未安装或做LCD验收。下一批回到G1/G2/G3
的捕获排他/完整别名释放与退出存活，随后完成G6放置、完整安装和总栈，再审G8；
尚未开始整体固件编译，不把对象检查当作终点。

[捕获事务与补充节点](CAPTURE_TRANSACTION_GUARD.md)已核对并接入31c7/440a/4480三组
同形分配/两段填充，新增实际25处CALL完整匹配。原生capture C持有覆盖额外prefix/
lookup/core采样，重入free/pool release/state observer不会继续原厂销毁；runtime身份
固定、重复初始化和销毁任务失配均隔离。91条指令/3组数据、12个直接native C host
场景及57目标对象通过，没有SHA。其他分配/重填充、异步别名和完整释放闭包仍须审查；
下一项据本批有限入口清单继续关闭G1，再汇入G2/G3退出与G6放置/安装/总栈。G8未就绪。

[捕获重填充守卫](CAPTURE_REPOPULATION_GUARD.md)已在7ea0/8dbd公共lookup返回、首次
capture写入前接入撤销，覆盖这两个函数的全部正常入口调用；重复、倒序或漏通知
不能继续使用旧sealed快照。实际CALL组扩为27处，三条新建路线保持现有准入范围。
123条指令/3项数据、21个native C host场景、portable sidecar、既有16-job整链和57个
目标对象通过；整链fixture同步到当前UI transaction mock接口，没有SHA。其余图像
重用/写入入口、异步别名和完整释放闭包仍待审，下一项继续G1对象责任追踪，然后
G2/G3退出与G6合法放置/安装/总栈；尚未达到整体固件编译准入。

[associated对象池生命周期](ASSOCIATED_POOL_LIFETIME.md)已证明并绑定固定25槽布局，
补上“关联记录已归还、node尚未free”的独立撤销路径。归零入池前与pool初始化前
均撤销旧sidecar；source先验证真实槽位/计数再读回链，通用allocator的其他pool保持
原路径。CALL组扩为29处，117条指令、31个native C host场景及57目标对象通过；
新增两座桥保留原frame/参数，initializer采用尾转。没有SHA，未重跑无关测试。
下一项继续engine workrecord及event/异步别名顺序，G1仍须完成全部节点责任闭包；
随后G2/G3退出、G6放置/安装/总栈，再审G8并开始整体固件编译。

[忙碌等待队列承载](DEFERRED_PRODUCER_CARRIAGE.md)现补齐第二条正常metadata路径：
入队时保存已冻结值，按25槽FIFO位置追踪，正常出队复制至service独立栈scope，
取消/重置/associated回收/capture重写和状态提交均撤销对应等待值。复用原票据发送，
不在延迟入口晚查node。新增7个实际CALL检查，总组36处；113条原厂指令、45个native
C host场景（14个新增）、58目标对象通过。新增桥214字节/83指令，没有SHA。
下一项回到engine workrecord：核对b387选中回调、aef8全完成回调及异步bit4的串行
事件顺序，再覆盖取消/重复完成和任务排他；不能用正常顺序代替全部别名存活闭包。
G1/G2/G3总体退出审查与G6放置/冷安装/总栈仍待完成，G8尚未准入。

[engine 工作记录代际](ENGINE_WORKRECORD_EPOCH.md)已核对正常串行周期的选中→全完成
顺序，并在两处callback注册及一处workrecord pool重建前撤销capture/等待快照。
实际17项callback/mask与required mask参与每次捕获事务资格，恢复同表不能复活旧代。
250条原厂指令、50个native C host场景（5个新增）和59目标对象通过；CALL组为39处。
下一项是callback执行域/重入与mailbox1的实际顺序和存活，不能把串行条件推导当成
并发证明；同时汇总G6所需的固定放置、冷启动和完整栈依赖。尚未开始整体固件编译。

[mailbox1顺序](CONTROLLER_MAILBOX_ORDER.md)已确认启动属性0、两类send尾入队和poll
receive头出队，以及12字节事件按值复制；189条指令、8项数据及有限CALL清单通过。
engine type7实际走6011f863，不能套用通用callback queue。邮箱删除重建及回调互斥
仍待闭合；G6已转入E-P7自身分段加载/驻留和后续覆盖范围研究，不再仅按平坦解码地址放置。

[加载与放置约束](LOAD_REGIONS_AND_PLACEMENT.md)已核对9段原生表、5组早期搬运、
段9之外的6144字节helper占用，以及加载/初始化两类标志。现有39项capture CALL映射到
段2，8组短跳区间至少需要2个数值落点；不是可用code cave证明。138条指令、10项数据
和39项CALL形状通过。下一批查BSS/allocator保留范围、早期bootstrap及首次使用时点，
然后才能定案近跳/重定位与全栈；G1/G2/G3残余闭包仍保留，未开始整体固件编译。

[RAM所有权和预算](RAM_OWNERSHIP_AND_BUDGET.md)已核对两处启动清零、初始化数据、
三个kernel arena、9个domain缓存池和4个非缓存池。提出保留CPU2大块池末槽payload的
16 KiB方案，列出分配/释放两条同宽上界修改，保留64字节原厂守卫；尚未应用或准入。
134条指令/13项数据通过；复用95个实现源的历史尺寸，仅新编1个sizeof探针，补齐
5,704字节core/bootstrap/runtime，私有存储粗计8,080字节。下一项早期代码承载、
近跳和清零/发布顺序，再完成链接对齐及全栈；没有重跑无关测试或开始整体固件编译。

[五字节远跳桥](FAR_CALL_VENEERS.md)已取代捕获侧18处短CALL的近距放置要求：JMP32进入
30字节桥，真实CALL按原tuple建帧，同时修复栈返回槽/MDR，再进入原adapter；额外暂用
4字节栈。实际cohort核对每个已知桥的完整形状和目标。复用GNU指令函数体的9种tuple、
RET/RETF共18路径及负控制通过，61个目标对象自有符号闭合；新增text1,011字节、无新BSS。
没有改写镜像。下一项UI等剩余短调用及早期代码承载/冷安装，再做全栈与G8汇合审查。

[UI与CPU远跳接合](REMAINING_FAR_CALLS.md)已复用同一30字节宏接入另外10处短CALL，
当前已列出的28处均保留原5字节宽度/返回PC/MDR/帧。新增CPU实际cohort在setup读取前
拒绝错误安装，旧capture/UI主机夹具同步到当前编码。10处解码原厂CALL、10种tuple的
20条返回路径、strict/ASan/UBSan定向cohort及63/54目标对象通过；未重跑完整生命周期。
最新101实现源text44,793、静态存储8,080字节。下一项早期代码承载、冷安装/清零与
后续加载覆盖及全栈；G1/G2/G3与GUI旁路余项仍保留，G8未就绪，未开始整体固件编译。

[早期承载审查](EARLY_CODE_SPACE.md)已核对两个32,640字节内部候选及原生早期复制，
合计65,280字节；23个相对转移原始命中均在已审局部指令内部。10个优先字面量中9个
跨指令编码、1个进入参数记录仍待解释，其余5,304个及其他组件尚未分类。61条指令
通过；定位600201fe完整6字节冷初始化候选接续，但没有实现bootstrap或批准空闲区。
下一批须补齐引用/所有权与其他CPU首次使用顺序，随后绑定RAM保留、清零和完整安装。
未重跑host/对象测试，没有SHA或固件改写，G6/G8继续保留。

[冷启动顺序与清零桥](COLD_START_CLEAR.md)现已落实53字节无C/RTOS依赖的完整16 KiB
清零候选，暂用16字节栈，恢复PSW/寄存器并回放原MOV。79条原厂指令及合成地址下
两组状态检查、三个负控制通过；复用GNU指令函数体，没有完整libsim或相机执行。
同时纠正池上界属于60022xxx启动前缀、并非kernel复制内容；次核等待前存在原厂调用，
没有把等待循环当全核静止证明。下一项启动前缀加载/保留区责任及完整安装/全栈，
G1/G2/G3和GUI旁路仍待审；未批准放置、改写固件或开始整体固件编译。

[流水线安装组](PIPELINE_INSTALLATION_COHORT.md)汇总时发现旧28处清单漏了消息链8处短CALL，
已复用原宏补齐到36座。新增实际cohort核对16个调用、9条帧调整、6个容量字段；严格host
拒绝缺项/损坏，14种tuple的28条返回路径通过。只新编2个目标实现并复用旧对象定义，
当前104实现源text45,733、静态存储粗计8,080。新cohort尚待接入完整冷启动发布回调；
下一项剩余inline/table清单、原生bootstrap/安装、代码/RAM资格与全栈，G8尚未准入。
