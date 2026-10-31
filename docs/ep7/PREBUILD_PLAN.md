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

**未就绪**：G1 原生捕获/释放闭包、G2/G3 退出与queue/task存活、G4 原生资源、
G6 放置/安装仍未闭合。generation-bearing handoff、共享runtime发布和CPU reader已有
实现；具体证据见本页末尾更新。继续离线研究，没有可承诺的安全试刷时间。

最新实际进展：[当前工具链](CURRENT_TOOLCHAIN.md)、[异步别名接合](ASYNC_NODE_ALIASES.md)、
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
