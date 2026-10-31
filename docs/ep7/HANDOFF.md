# E-P7 研究检查点 / 恢复研究

## 2026-11-01 当前目标与节点

当前目标已扩展为继续离线候选模拟，最终得到真正可以刷机的固件包；每个关键节点
提交推送。用户确认没有经过验证的固件备份和独立恢复手段，先继续离线验证。
[推进计划](FLASH_READINESS_PLAN.md)保留完整目标；下面 10 月 31 日的“编译阶段完成”
不表示当前目标完成。

最新：[原生创建与发布模拟](CANDIDATE_PUBLISH_SIM.md)已完成 S2 的有条件场景。
原厂 create 316 指令取得 ID1，正常 bootstrap 共 52,820 指令后发布 a1dd6108，并
恢复原调用现场尾转 6011f620。原厂耗尽返回 −34 后候选 f04 隔离；queue4c 失配后
真实 delete 384 指令清除 ID/计数并释放锁，再 f05 隔离。没有 API 成功 stub。
其他核空 pending list、单节点 ready list、原生锁字节及预初始化 queue header 都是
明确 fixture；真实初始化、多核、加载/占用、完整栈和恢复仍未通过。下一步 S3 复用
这个由候选代码实际发布的 runtime，执行原生 poll/signal 下的 H/L 修改/冻结及后续
capture/queue/worker/CPU 链；不要手写已发布 runtime 或自动填充未知内存。

此前：[实际链接候选启动模拟](CANDIDATE_STARTUP_SIM.md)已完成 S1。直接执行候选 ELF
对应机器码：16 KiB 清零、capture 初始化、七组 cohort、损坏补丁/错误 TCB/重复初始化
拒绝均通过。bootstrap 的三次原生 get_tid 完成，12,729 条指令后到达 6003057f，
A0 指向正确 0/1/1 semaphore spec，尚未执行 create，也未发布 runtime。
前缀观测栈深 296 字节，不是完整栈界。无对象重编译、SHA、固件文件修改或相机操作。
S2 已沿此现场推进；复用候选与严格引擎，不再重做已完成的工具链和对象清单。

恢复日期：2026-10-30（Asia/Shanghai）。用户已要求继续推进研究测试。
**本轮已完成首个不可安装离线候选的整体编译、链接与合成；未进行刷机或相机操作。**

## 2026-10-31 当前节点

当前交接：[离线候选构建与结果](OFFLINE_CANDIDATE.md)、
[实际报告](../../research/ep7/offline-candidate.json)。用户明确允许先编译不可安装候选，
保留未通过项；G8 的离线标准已更新，不能继续按旧 G8 无限阻止整体编译。
`generated/ep7/offline-candidate-002/` 已有 ELF、map、链接脚本、对象和 decoded main。
107 源实际编译；首轮空 `.text` 孤立段错误修复后复用全部对象成功链接。
两代码区合计 46,815 字节、BSS 8,084；101 修改、36 veneer、73 最终分支检查通过。

“推进到开始编译新固件”的阶段目标已经达到。后续若继续安装研究，应基于这个实际
布局关闭代码/RAM 归属、启动加载、完整栈及生命周期剩余项；不要把链接成功当作通过，
也不要再次重做已完成的对象清单、工具链、VM 设计或整套主机测试。
正式 RAM 地址表仍保留未解析值；只在离线链接脚本内采用 a1dd4d00 候选。
产物不可安装，无更新容器、实机 HSL 或恢复验收。

以下为此前节点的历史记录；旧“未整体编译/G8 未通过”不覆盖上面的最新离线结果。

最新：[严格引擎](STRICT_SIM_ENGINE.md)已在现有volume构建，最终路径
`/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103`。复用GNU strict patch和runner，
新增显式无SHA构建/执行入口；旧默认hash入口保留。39条witness、六个定向场景通过：
未知取指/syscall停止，原厂MAC helper两种MCVF回转、任务异常query的flag1/0分支。
八次短调用的原厂代码运行在GNU模型，TCB/CPU ID等为fixture；没有完整boot或相机执行。
下一步优先复用此引擎及上游load/execute/reload方法，审查E-P7启动加载与代码/RAM
所有权；遇到未知外设/回调必须停下记录，不能套用PEN-F地址或假造成功。
生产对象仍text46,800/BSS8,084；完整栈、放置、生命周期及G8未通过，未整体编译固件。

最新：[IRQ退出条件](IRQ_STACK_TRANSFER.md)将五个UDF对应到松下手册中的寄存器传送，
完整23条save/restore helper匹配。0800含IE=1但LM=0，仍屏蔽普通IRQ；恢复原PSW的
deferred窗口位于IRQ栈，返回后重新屏蔽才切回任务SP。现117条witness、493条解码，
复用CFG的10函数/257指令确认决策前没有显式PSW写入。TCB+48在查询时为1的条件
路径已知96字节；通用结果仍104，bootstrap已知416和完整上界null不变。
没有新增UDF模拟器、生产对象编译或广泛测试。下一项是TCB flag有效期、调度context
及原厂故障边界；这些未决条件不得用条件96字节报告覆盖。后续仍需推进代码/RAM放置。

最新：[冷启动现场](COLD_CONTEXT.md)已在创建私有锁前检查实际TCB+48、内核嵌套/
持锁状态和固定回调/mask/restart绑定，失败0xf06不创建锁。quarantine现为AND PSW
后BRA自环，6字节、body栈0，不再显式BREAK；本核任务进展会停止，资源保留。
10个root字段/9条指令、3次接受/12种拒绝只读观察、启动0/15及两种PSW下GNU语义通过。
只刷新3个对象，104个源码/头文件未变的对象资料复用；text46,800、BSS8,084，345个
全局定义、109外部依赖。C图刷新2个变化单元、复用16个，43函数/29callback，C峰值312。
下一步集中审查现场条件在native调用/异步IRQ期间的有效期和UDF/原厂故障路径；
原厂栈合并已知416，完整上界仍null，G6/G8未通过。不要再把自有quarantine列为BREAK。

最新：[原厂bootstrap栈](NATIVE_BOOTSTRAP_STACK.md)核对27函数/997指令，正常返回帧
无冲突；明确固定回调、context切换和任务入口top−4。合并此前C图的已知部分为栈顶
以下416字节，完整上界仍null。[IRQ节点](IRQ_STACK_TRANSFER.md)定位独立8 KiB栈和
进出SP：85条witness、451指令、14函数；单次已知部分8+56+40=104，不是全栈通过。
该原厂研究节点的证据继续复用；后续生产C/ASM及现场检查已按上方最新节点更新。
不要重新展开整条IRQ handler链后全部累加到Usr3。

此前：[bootstrap调用栈](BOOTSTRAP_STACK.md)按GCC调用图收敛到42函数和29条具体callback，
只生成18个可达C对象元数据，尺寸/`.su`与统一清单一致。最深已知C路径312字节，
加Usr3/原CALL/桥为400；完整上界仍为null，原厂create/delete及异常/IRQ栈不能按零处理。
原厂create/delete责任已推进到上述新节点，复用当前图避免重跑整套测试。
此前启动前缀加载者和guard writer有限调查没有取得新资格，继续保留未决。

最新：[统一安装清单与目标符号](INSTALLATION_MANIFEST.md)汇合101项、546字节，原厂字节
匹配且互不重叠；107生产对象一次统一编译，无重复定义，84个安装目标存在。109外部
依赖中108有原厂地址，私有RAM符号仍待批准放置。当前text46,543、BSS8,084。
3处启动前缀修改的上游加载路径仍未知；下一项优先关闭该路径，再复用当前`.su`推进
总栈/放置，继续处理生命周期准入。此次仅对象编译，未整体链接、构建或安装固件。

最新：[一次性原生bootstrap](COLD_BOOTSTRAP.md)已接合候选60191371，早期inline安装组、
实际Usr3任务资格、私有锁/core/runtime永久存储和发布已实现。15个新增host场景、48项
cohort负检查及54字节桥的局部GNU语义通过；失败不继续启动依赖runtime的接收任务。
107实现源text46,543、BSS8,084，runtime5704已计入，不能再重复追加。完整聚合对象检查
本批未重跑；下一项完整安装清单/符号分区与全栈，再推进放置/生命周期准入。
selector已有真实initializer检查，后续复用，不再另造一套开关。G8仍未通过。

最新：[runtime启动接续](BOOTSTRAP_ENTRY.md)核对85指令/10任务行，选定候选60191371：
domain0的Usr3、2048字节配置栈，早于四个接收任务和capture controller的启动。
第9段之后的候选太晚，domain2加载任务也不适合；UI第6段必须在后续驻留入口做资格检查，
不能由Usr3等待其尚未启动的Usr4/Usr5。下一项为早期inline/cohort与一次性bootstrap实现。
实际kernel任务配置consumer为60032998，旧6005b447查询路径不再作为创建证明。

最新：[冷启动清零桥](COLD_START_CLEAR.md)已实现53字节候选及局部启动顺序核对；
[流水线安装组](PIPELINE_INSTALLATION_COHORT.md)补齐旧清单遗漏的8处短CALL，当前归档36座，
并把16个CALL、9条栈调整、6个容量字段作为同组检查。104实现源text45,733，静态存储
粗计8,080。实际cold installer/bootstrap发布入口、代码/RAM资格、总栈及生命周期余项仍待
完成，未开始整体固件编译。优先依据上述两份新报告继续，避免重复旧对象/主机全集检查。

此前：[原生capture source](CAPTURE_NATIVE_BINDING.md)已定义具体provider，接合初始化、
fresh登记、两次population、13个node free以及capture pool release。目标56对象通过，
剩余32个符号全部为原厂地址；原生排他/完整闭包、G4、G6仍未完成，固件整体编译未开始。

捕获侧新增[两阶段冻结](CAPTURE_POPULATION_ENVELOPE.md)：第一段population返回时sample，
第二段确认后才可copyout；期间UI变化不改变已冻结值，提前消费不事后补填。
producer provider现限定实际controller entry60289852；13个已列node free call完成本次
无SHA重验。原生source/释放桥与排他、G4/G6仍待完成。

最新：[queue临界区准入](QUEUE_KERNEL_GATES.md)已落实为候选代码，收发最终检查与
删除观察位于原厂临界区内；删除后永久关闭本次启动的实验I/O，旧清理context保留。
定向host、51目标对象及88条原厂指令检查通过；整体固件构建仍未开始。

本机原厂整包和GNU工具链均已就绪；下文“尚无输入/下载中”属于早期过程记录。
[异步调度生命周期](ASYNC_DISPATCH_LIFETIME.md)确认请求按指针排队、上层清零隐藏
队列状态、worker返回后可能有第二阶段。不能据此推断完成或回调静止。
G2已实现controller侧冻结值之后的[一次消费票据接口](../../prototypes/ep7_volatile_hl/snapshot_transport/README.md)，
主机处理链strict/ASan/UBSan通过。目标对象另行检查，无目标执行。
[队列票据承载](QUEUE_TICKET_CARRIAGE.md)已接通启动配置→运行时queue字段→发送长度
上限→按实际长度接收的路径，核对154指令/9数据项。采用自有28/312字节消息缓冲，
不能只扩大send长度或改receive参数。wire编解码已实现并贯通command→三次relay→
票据claim→真实job代码，host strict/ASan/UBSan通过，目标对象通过。
本地raw receive/send ABI已实现并核对，保留实际长度；跨域positive255失败已记录。
实验票据整批撤销已实现并通过host检查。原生hook/上下文尚未安装，下一步核对五个
descriptor拥有者的显式栈扩展（包括command drain），整体固件构建未开始。

五个拥有者已完成[只读栈扩展审查](DESCRIPTOR_FRAME_PLAN.md)：每个局部帧新增12字节，
9处新栈调整与原指令同为4字节，53指令/4任务表行核对通过。没有写入固件。
下一项是command独立scratch、owned receive适配及三处materializer调用链ABI。

owned I/O实现已完成：148字节command scratch、312字节descriptor receive、发送前
消费票据及失败后的清理值返回。strict/ASan/UBSan定向链路及目标对象检查通过，见
[host报告](../../research/ep7/owned-queue-integration-host.json)与
[目标报告](../../research/ep7/owned-queue-target.json)。首次ASan运行超时30秒；诊断复跑
源码未改即通过，原因未确认。send局部栈400字节，不能把单函数结果当完整栈预算。
下一项落实materializer三调用链的实际栈资格、进入桥及安装前置条件。

materializer三调用链已实现[有界栈映射与接收桥](MATERIALIZER_RECEIVE_BINDING.md)：
资格检查后才取得16字节command和312字节descriptor。strict/ASan/UBSan及目标对象
检查通过，四条桥指令/return frame/relocation已核对。context provider仍未绑定，
不能用布局匹配替代安装/任务域证据。下一项为其余relay/worker收发seam和claim/retire。

四处双队列receive及kind19 relay/worker的[接收桥](DESCRIPTOR_RECEIVE_BINDING.md)已实现。
52指令/5数据、目标18指令桥检查通过。主机strict通过；一次ASan超时，带启动日志的
诊断复跑通过，原因仍未定位。共享helper仅对非扩展未知队列恢复原厂路径；4c/ab/4f
未知消费者拒绝接收，不能据此宣称全接收闭包。下一项为发送和最终claim/retire。

三段descriptor[发送与清理接口](DESCRIPTOR_SEND_BINDING.md)已实现，32条原厂指令和
17条目标桥指令核对通过。strict/ASan/UBSan通过，完整16-job主机链现使用真实forward
和owned receive；失败锁清理保留票据值，route变化仅保留撤销资格。原生retirement
owner仍未绑定。检查器增加`--asan-verbose`诊断选项，不改测试/30秒超时。下一项为
producer command与worker claim/drain清理，以及G3/G6 context和安装发布。

producer已通过[自有栈scope接合](PRODUCER_SCOPE_BINDING.md)：提前复制已冻结值，发送点
生成28字节command，失败不晚补填。原metadata148不变。发现原600514b6含发送后
通知，已将producer和descriptor发送均改为保留该原厂封装；此前raw send路径从未安装。
48条原厂指令、30条producer桥指令、23条queue桥指令及host strict/ASan/UBSan通过。
ASan超时已在最小PIE程序初始化阶段独立复现；non-PIE检查通过，详见诊断报告。
当前12个原生/capture/context外部符号未绑定，整体固件构建未开始；下一项为worker/drain。

[owned consumer](OWNED_CONSUMER.md)已接入完整16-job主机链：首次尝试先标记仅可清理，
锁失败/路由变化不能晚领取；清理失败保留原描述符票据，成功/重复清理幂等。strict、
ASan/UBSan和目标对象检查通过，consumer文本180字节。原生worker allocation/job登记、
cleanup前撤销及ACK/drain保持策略仍未绑定；下一个节点继续落实这些实际seam。

[worker job接合](WORKER_JOB_BINDING.md)现已实现：独立48字节scope、仅资格路径请求15512、
实际allocation身份登记、cleanup前撤销及保留失败重试。包装器新增136字节调用栈；
原五个descriptor帧计划不再扩大。53原厂指令/一表项、59桥指令、GCC指针返回a0及
strict/ASan/UBSan通过。当前17外部符号未绑定；真实context稳定性、等待策略和ACK/drain
仍未闭合，不能安装hook。接下来落实ACK/drain，以及G3的实际任务/运行时上下文。

[ACK/drain桥](ACK_DRAIN_BINDING.md)已覆盖正常拒绝、command drain和worker完成三处，
原厂ACK发送metadata身份前先撤销票据；失败保留descriptor与清理责任。38原厂指令、
16桥指令及host strict/ASan/UBSan通过。19个原生/context符号仍未绑定；下面转入G3共享
runtime、实际task stack/domain和等待/poison策略，避免仅继续增加未解析provider。

[当前任务实际栈视图](CURRENT_TASK_STACK.md)已实现：原厂get_tid前后核对、当前TCB链、
TCB+76 entry/+84 size/+88实际base及anchor范围。59原厂指令、复用get_tid桥和host检查
通过，无新增native API桥。该视图不授予安装/代际资格；下一项为共享runtime稳定发布和
私有锁poison/竞争分类，再把这些事实接入已有context providers。

[cleanup进度原语](CLEANUP_PROGRESS.md)已核对：600313ef定时delay使用wait reason2，
60036e23/tslp_tsk会消费TCB+21既有唤醒计数，不能混用。固定一个原生时间单位的GCC桥
已检查，尚未装入等待callback。下一步共享runtime分离永久发布与新准入健康状态，并
落实poison/意外delay错误时的保留策略；当前没有固件整体编译或原生执行。

[实际队列视图](RUNTIME_QUEUE_CONTEXT.md)已补齐root/limits/object/backing查询，复用get_tid
与kernel读接口。75条原厂指令、定向strict/ASan/UBSan和目标对象检查通过；没有SHA。
双读一致不等于queue generation/lifetime lease，禁止删除/重建仍须安装退出闭包保证。
下一项共享runtime将保留已发布context，健康状态仅影响新准入，避免poison后跳过旧job清理。

[共享runtime](SHARED_RUNTIME.md)已实现并关闭六个context provider外部接口，复用bootstrap和
私有poll锁，固定五个实际queue实例；stop/poison不撤销旧context。清理竞争定时delay，
永久错误/丢失布局转入保留路径。定向strict/ASan/UBSan与完整pipeline对象检查通过。
安装器/lifetime、捕获源、CPU reader与共享slot接合仍未关闭；下一个节点先处理reader，
再集中推进退出闭包、UI及G6放置，整体固件编译未开始。

[CPU reader接入](RUNTIME_READER.md)已完成：原postbuilder桥不变，observer经发布slot使用
worker同一core。host验证stop后在途job仍生效、撤销/poison后保持原输出；33条原厂指令、
49对象ABI/loop-state检查通过。20个外部符号为捕获源和19个native地址；没有整体固件
编译。下一重点回到退出/queue删除闭包与捕获源身份，再处理UI和G6放置/完整栈预算。

[队列自动重用](QUEUE_RECREATION.md)的实际风险已查明：limits为0/255，真实create以ID0
进入自动allocator，可在删除清ID后重新选择所有pipeline编号并换maximum/backing。
66条原厂指令、两配置项核对通过；没有重复C测试。下一项必须审明实际删除/退出路线，
落实保留实例或有静止证明的退出协议；不能把ROM配置ID称为不会被重用的静态ID。

## 本轮恢复后的增量

- 在既有 controller sidecar 中实现 `ep7c_resolve_live`，无需额外 token map。
  仅限调用方已证明存活且持有独占 controller 区间的节点；不接受以裸地址查询
  结果替代存活证明。旧裸地址遇到复用会查出新 token，这一限制已有可执行用例。
- 定向验证 COLOR4 快照冻结、忘记/复用、state33 重入、退出/重进、状态不一致
  poison 与全部8个槽位。严格 C11 和 ASan/UBSan 通过，无 SHA 校验。
- 现有检查器新增 `--host-only [--sanitize]`，不依赖原厂固件或目标工具链。
  见[执行报告](../../research/ep7/controller-sidecar-live-join-host.json)与
  [接口契约](../../prototypes/ep7_volatile_hl/controller_sidecar/README.md)。
- 本轮修改没有交叉编译；原生 node→token 调用点、对象存活/排他性证明及完整
  释放路径绑定仍待解决。旧交叉编译报告不代表此次源码已验证。

## 编译前路线与本轮推进

已建立 [G0–G8 完整编译前计划](PREBUILD_PLAN.md)。本轮首先完成
[生命周期证据清单](LIFECYCLE_HOOK_INVENTORY.md)：13个 node free、3个非 node free、
两处状态服务 call；源 witness 核对通过，不代表本次原厂字节重验或原生闭包。
新工具 `tools/ep7_lifecycle_inventory.py` 无需固件/交叉工具链，不执行 SHA 校验。

独立聊天“EP7 固件研究虚拟机环境设计”（gpt-6.1-terra / max）同步负责环境设计，
输出 `docs/ep7/VM_ENVIRONMENT_PLAN.md`。本聊天继续负责 G1/G2 身份/生命周期。
当前工作区没有私有原厂输入与目标工具链；下一步机器码资格审查需要准备这些输入。
未开始固件整体编译、打包或相机操作。

## 后续软件接合节点

实际 vertical slice 已接入 controller sidecar：register/resolve/authorize/seal/copyout
→节点撤销/33重入→后续 UI 修改→16个 fresh-job operation；捕获快照保持不变。
提前 copyout 的新节点不能晚 seal，NULL snapshot 路线仍完成原厂处理/清理 fixture，
输出保持中性。strict 与 ASan/UBSan 通过，见
[执行报告](../../research/ep7/sidecar-vertical-slice-host.json)。
这是主机按值传递契约的集成，未实现原生 metadata/descriptor handoff。

环境设计已由 Terra/max 完成，见 [VM_ENVIRONMENT_PLAN](VM_ENVIRONMENT_PLAN.md)。
当前正在从官方目录取得1100原厂输入及 GNU binutils2.45 源码；下载尚未验收。
旧 SHA guard 保留；新增的可选无哈希记录和结构检查入口不宣称历史逐字节身份。

## 原厂主程序可用于下一步研究

主程序首组件已完整提取，型号/构建/结构、加法和与自身编码回转通过，无SHA。
随后完整整包下载成功，五组件结构/加法和/回转通过，整包main与先前首组件逐字节相等。
见[完整报告](../../research/ep7/full-input-structure.json)。当前字节扫描取得global node的4个、wrapper
queue的8个、async descriptor/callback各1个字面引用候选；这些还不是已反汇编的
指令边界或生命周期结论。见 [输入准备与复现](RESEARCH_INPUTS.md)。

## 工具链与异步别名节点

[当前工具链](CURRENT_TOOLCHAIN.md)已构建；新sidecar七对象目标编译和符号集合检查
通过，仍有两个原生外部符号，无目标链接/固件构建。
[异步节点别名研究](ASYNC_NODE_ALIASES.md)已核对62指令和type39分发表，接通两层
回调的node传递，新增wrapper-only free4403分类。低层回调包含两条GNU命名为udf00
的自定义指令槽，未赋予语义。下一步审查6011209b请求保持、完成/取消与调度域。

## 原暂停检查点（历史记录）

以下记录保留原检查点范围；其中“未实现 token lookup”已由上面的主机实现更新，
其余原生绑定与固件安装阻塞仍然存在。
当前检查点内容以本分支提交为准：`git rev-parse HEAD`。
上一公开基线是 `9ff36d84fb6ac6f7e7c7b1b98833660cdbbf9099`；本检查点在其上保存已审新增工作。

先看 [QUICKSTART](QUICKSTART.md)。主机 smoke 不需要私有固件或交叉工具链。

检查点独立复核在不含固件/目标工具链的干净源码测试树运行：321项 E-P7测试
得到 OK（313项通过，8项可选检查明确跳过）、9项容器测试通过；六组 host smoke、
strict+ASan/UBSan 和实际软件 vertical slice 通过。skip 不是目标检查通过证据。

## 已保存的实际工作

- 原厂 E-P7 1.1/1100、model1420 的精确输入和五组件只读校验；原样 encode
  回转逐字节相等。SHA 见 QUICKSTART；仓库不含该固件。
- 实际 C H/L 状态、逻辑事件、UTF16 文本、每图快照、fresh-job decoder/direct
  reader、revoke/free 已在主机贯通；native 边界是明确的 fixture。
- MN10300 自写 ABI 桥已交叉编译/反汇编核对，未链接成目标程序、未执行或安装。
- 私有 poll-only 锁、startup ownership/quarantine、state-service 双调用点桥。
- `controller_sidecar/`：真实 controller-local C 回调、generation/token、单次捕获
  与复制；**原生 node pointer→token 接合、初始化和全部支持释放 hook 未实现**。
- `text_rollback/`：限定新建、未挂父 text class 的 cleanup→destructor→deallocator
  适配器。资源/对象资格与原生 allocator context provider 仍是未绑定契约。
- [metadata allocation](METADATA_ALLOCATION.md) 精确记录寄存器/返回帧接口；
  不是已实现 transport，也不允许凭 tag/kind19 读取未证明存在的扩展尾部。
- [packaging/recovery](PACKAGING_AND_RECOVERY.md) 核对本机 checksum 路径；
  无改动 roundtrip 不等于改包接受、可启动、同版本升级或可救砖。

## 仍然阻断相机可用版本的事项

1. 安全代码/数据放置、链接、短调用 trampoline/relocation、cache/栈空间和启动安装。
   没有证明某段全零/FF 就可注入，没有生成 E-P7 修改后的升级镜像。
2. 原生 category4/5、对象/字体/布局资源、输入焦点/完整拨轮次数、创建失败与回收绑定。
   `renderer_ready` 不能因为 host 文本测试通过而开启。
3. 捕获源→metadata→job 的实际身份/extent/lifetime handoff；所有支持的释放/取消路径、
   state33 重入、旧指针复用等。已复制的图像快照与 node admission 是不同生命周期。
4. GUI/capture producer/CPU reader 的任务域和同步、真实 runtime 分配/初始化、原生契约。
5. E-P7 完整 updater acceptance、版本/组件限制、可独立恢复的路径和专用实机测试。
   未证明救砖能力；无首次 native boot/HSL 实拍/像素校准。当前授权不包括刷机。

## 暂未纳入发布的探索

停止时以下仅是私有 scratch 或未完成思路，**不是随 clone 可执行/已审的实现**：

- 更新器更深层 component/model/write-dispatch 路径（72 witnesses 候选）；
- UI allocator context 两字节 accessor 绑定（77 witnesses 候选）；
- 不扩大 metadata、以既有 image identity 绑定快照的替代路线：刚开始，未独立复审；
- node pointer→current token join、代码放置/target-size 分析未完成或未开始。

恢复时先审这些候选与当前源码是否一致；不要根据本交接把未审结论补写成事实。
下一优先顺序是 identity/lifetime 接合与安全放置/恢复资格，而不是继续堆测试数量。

## 结果解释

主机测试成功说明被执行的自写代码在该 fixture 下工作；交叉编译只说明 ABI/对象
检查符合所设约束。两者都不证明 firmware 可刷、相机启动、JPEG/HSL 实际效果。
H/L 当前易失、重启归零；stock S 语义不应被改写。没有安全用户试刷日期承诺。
