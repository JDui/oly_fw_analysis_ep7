# E-P7 HSL：从离线候选推进到可刷机包

2026-11-01。当前用户目标是尽快完成最基础可刷入的固件，到达实机测试硬件阶段；
每个关键节点提交并推送。用户已选择首版保留色轮编辑和照片处理的基础 H/L 版本。
本轮不改为仅带标记的原厂启动探针，也不把容器校验等同于可运行固件。
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

## 基础 H/L 首版的收敛规则

首版保留四 COLOR profile 的易失 H/L 编辑、拍摄时冻结及已绑定 CPU COLOR
处理分支；重启归零，持久化和扩大拍摄模式支持后置。已有实现、原生证据和模拟器
直接复用。离线检查集中在改动所依赖的契约，不要求重演所有未修改的原厂校准、
传感器、ISP 或文件系统内部流程；这些边界可使用明确标注的输入模型，但不得因此
宣称真实硬件或完整原厂生命周期已通过。

接下来依次关闭三个有限出口：

1. **更新器接收与路由**：实际五组件包执行原生解码、校验和型号分流，写入请求在
   模拟边界截获；核对全部组件去向与错误是否阻止后续写入。继续追 E-P7 文件选择
   与启动入口，不套用 PEN-F 的按键或文件名假设。
2. **基础功能和启动的具体风险**：优先检查生产静态内核配置后的私有锁分配、
   新增代码/RAM的装载和保留、改动经过的捕获冻结/异步消费/撤销，以及 GUI 编辑
   到系数输出。仅针对尚未覆盖且会改变安装或功能结论的路径补测；原生 metadata
   全初始化探索保留为研究支线，不无限扩大为整个相机软件的重演。
3. **fishcu 封装与交付审查**：复用 parse → replace_payload → reconstruct，保留
   E-P7 五组件与各自版本，形成实际包、对应原厂恢复文件与明确的台架验收步骤。
   同时分别报告容器有效、更新器接收、启动/功能证据及未验证的恢复条件。

已有模拟不因流程收敛自动升级为硬件证据。发现具体实现缺陷先修复并做定向验证；
没有变更的对象、有效封装和已通过检查不重复执行。以下 S1–S6 保留为证据归类，
长篇历史子节点不是要求逐个继续扩大的待办列表。

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

S5可独立推进的[五组件研究容器](CANDIDATE_PACKAGE.md)现已生成，111,017,984字节。
直接复用fishcu容器流程，E-P7元数据与四个未修改组件逐字节保留，主组件实际ELF/
patch及落盘回读通过。它仍标记不可安装；局部/完整原厂更新器、恢复与S3/S4资格
尚未因此关闭。下一步执行原厂局部校验路径。

该[局部原厂校验](CANDIDATE_PACKAGE_NATIVE_SIM.md)现也通过：实际main完整26,214,400B
原厂校验返回0；实际010e完整解码与主机结果一致；头尾差异和单字节损坏分别返回
3202或进入真实错误日志分支。原厂完整更新器/写入/恢复仍未执行，S5尚未整体完成。

## 当前进度

S5的[SD软件入口](CANDIDATE_SD_ENTRY_SIM.md)已执行1,624条指令：原callback选择
最高有效后缀，原11组pattern wrapper、task88消息构造和task18接收分流接通，
实际32B消息将111,017,984B长度及buffer传到共享更新器mode0。SD读取/队列交付等
为显式边界，包只映射头并在共享入口停止；没有重复整包校验。物理按键启动与恢复
仍未验证。下一项按基础H/L范围检查GUI/worker和驻留，不扩展整套文件系统模拟。

S5的[共享更新器接收与路由](CANDIDATE_UPDATER_SIM.md)已取得阶段证据：实际五组件包
mode2完整通过，后续mode1的五项写入分流和错误3102停止传播也通过。第一次完整
运行在已通过validation之后被主机别名断言拒绝；修正后只重跑commit，阶段结果与
缺失的mode2明细报告分别记录。物理SD/USB入口、写入/回读和恢复仍未验证。

基础H/L的[新捕获交接契约](CANDIDATE_SELECTED_HANDOFF_SIM.md)已通过：实际新node的
原生backlink发布后，候选取得COLOR4冻结5/-3；延迟FIFO保持ID2与值，prewrite撤销
后同元素正常出队但scope中性。未重演selected handler的原曝光/格式处理，未知
metadata保持未填；没有把契约检查算作完整照片或并发生命周期通过。

首版收敛后的[生产静态信号量检查](CANDIDATE_STATIC_KERNEL_SIM.md)已通过：实际原厂
132行初始化后，候选取得ID133并发布runtime，H/L编辑/冻结使用原生poll/signal133；
发布失配只回收自己的133，原132对象及used计数保留。关闭此前S2的ID1专用夹具
假设，完整调度/队列初始化、加载及安装资格仍需独立证据。

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

[模板复制与population前缀](CANDIDATE_POPULATION_SIM.md)随后实际执行patched prewrite
和6833word复制，全27332字节一致。追加1084条原厂capture配置默认记录后，总2293条
属性已注册；population经过40次getter，停在604288d5读取未映射622a064a，目标
capture+24178/+24180。其原厂reset和动态setter已定位，配置对象来源/更新尚未接通。
当前保持未知状态未映射，完整population未通过，也未进入relay预处理或worker。
下一步沿配置来源关闭这个真实停止点，不以原厂初值零代替实际拍摄状态。

[几何服务与配置构造](CANDIDATE_GEOMETRY_SIM.md)已实际执行服务初始化、controller/task
前缀、模式快照、请求字段生产/消费及117行设备属性缓存初始化。两组缓存指针分别
匹配147个槽和117行原厂属性，快照来自ROM；请求分支输入与启动数据搬运条件明确保留。
6042760c推进1920指令后停601168ee读取a272bcde，尚未进入动态setter6042805e。
partial capture保持不变，population尚未恢复；下一步追踪设备状态初始化和表来源，
再接配置构造。原厂重置成功不等于活动拍摄状态已证明，S3仍未整体完成。

[设备输入转换](CANDIDATE_DEVICE_STATE_SIM.md)继续关闭软件来源：原厂早期CPU复制
2248字节初始化数据，8种三bit输入实际发布板型编号、选择设备列及GPIO selector，
全部控制word恢复。随后两条原厂采样分别停在9b80108c和98e00058的真实寄存器读取。
新增8590条指令，没有补入未知相机引脚值。下一步可用明示硬件输入模型验证采样及
配置分支；当前geometry/population仍未续接，实机输入与外设时序继续保留为条件。

[设备输入模型](CANDIDATE_DEVICE_INPUTS_SIM.md)已用两组明确寄存器值执行原厂采样、
601168ba重置和1215查询，真实返回1/0。恢复原配置栈/寄存器后，两条分支分别继续
318/321指令，停在原厂状态62221d80或622211e2的读取。新增2948条指令，动态setter
仍未执行，capture不变。下一步追踪两个状态的原厂生命周期；模拟输入不替代实机证据。

[原厂冷状态片段](CANDIDATE_SERVICE_STATE_SIM.md)已接通上述两个读取，几何构造分别
继续3177/3454指令，统一停在124字节双快照selector6229fc44。78字节参数记录的
39次原厂halfword复制逐值通过；仅1字节padding使用明确BSS清零条件。前置外设调用
和完整任务仍未执行。下一步追踪快照producer/请求来源；配置和population尚未完成。

[原厂请求与快照字段构造](CANDIDATE_SNAPSHOT_SIM.md)已执行128B请求生成/原生复制，
真实回调60426f83中的6042661b返回，124B字段与原生缓存复制一致。新增21374指令，
两个输入分支均停60556934读格式模块就绪a2788ca8。完整producer/wrapper未返回，
不能提前消费中间快照；几何配置和population仍未恢复。下一步区分该模块原厂冷重置
与完成初始化的生命周期，不把缺省格式当作实机尺寸。候选及fishcu研究包保持不变。

[格式模块发布与模式字段](CANDIDATE_FORMAT_STATE_SIM.md)随后执行原厂ready发布helper、
48槽属性缓存和6字段刷新，进入就绪分支并生成10B参数记录。新增10380指令，两条
路径统一停606d673a读a2788cec，后续10B状态记录仍缺来源。完整核心初始化、两份
诊断缓冲区分配和完整状态刷新未执行；仅空闲谓词1B使用明确BSS初态。下一步追踪
对象+70/+80到+60的原厂状态复制及更新，完整格式getter/快照/geometry仍未通过。

[原厂诊断缓冲区与格式记录](CANDIDATE_FORMAT_RECORD_SIM.md)继续执行冷初始化后缀，
原厂分配器取得两份16KiB并初始化2048条记录；原厂reset/getter完成10B记录复制。
新增55234指令，两输入统一停6030b752读a273104a/2B，即980B历史记录的索引依赖。
冷初始化在明确空池/BSS/pre-kernel条件下完整返回，真实生命周期/并发归属仍未证明；
格式reset只到复制后，完整快照和geometry/population仍未完成。下一步追踪历史
索引与记录的原厂生产者。capture、候选004及fishcu五组件研究容器均保持不变。

[历史冷态回退](CANDIDATE_HISTORY_SIM.md)已验证：仅6B明确BSS条件下，原索引getter
选择槽0，原缩放函数实际返回65536。两输入总220指令；活动历史构造与成功后索引
发布仍未执行，其余4896B payload未映射。随后停47001070读a271ca80，即16B缓存
原厂复制的第一项；已定位601f66f7写入者及60293a65参数构造器。下一步追外层对象
与缓存发布，不能把有5B未显式写入的参数块整块补零。完整快照/geometry仍未完成。

[未就绪设备的冷态坐标回退](CANDIDATE_OPTICS_COLD_SIM.md)继续执行原厂可用标志重置、
两次type/period初始化及真实无设备分支，共736指令。16B缓存明确限定在首次帧发布
之前的BSS条件，未把活动帧中5B栈来源当作零。原厂两halfword复制保持(85,76)，
之后停6065e79c读取a2788ab2；该格式字段有原生reset写ffff，下一步执行其来源。
活动帧/镜头校准仍未通过；完整快照、geometry/population与S3仍未完成。

[原生未配置格式与getter返回](CANDIDATE_FORMAT_SNAPSHOT_SIM.md)新增14672指令：完整
格式reset写ffff，完整设备默认初始化复制3336B，完整模式刷新通过。原格式getter
返回60427f7d，150B记录的状态2表示未配置；不能当成有效格式。新增冷BSS条件仅
设备通信2B与刷新前旧mode295的1B。当前到服务输出6229fb98的首项store，下一步
为已审查的原输出成员提供写入空间。完整快照及geometry/population尚未完成。

[冷态快照回调返回与配置续接](CANDIDATE_SNAPSHOT_OUTPUT_SIM.md)已完成：只提供160B
原输出成员，原121B copy、坐标转换、输出构造器/回调/包装函数全部返回；新增1322
指令。12B新BSS条件只限冷fallback指针与未发布坐标记录，活动场景仍未通过。恢复
原geometry配置现场后再执行1086指令，真实消费6229fc48快照，停在622a06b4数组
读取。下一步追60425ba3的实际输入及三组数组发布；动态setter和population未执行。
这关闭冷态producer返回子项，S3、S4及安装资格继续保持待证。

[冷态参数数组与原生临界区](CANDIDATE_GEOMETRY_ARRAY_SIM.md)再推进3012条指令：
五组数组40次复制、原getter返回、原控制器4B参数发布及完整调度锁保存/恢复均通过。
72B数组与1B前次状态仍为明确冷BSS条件，两个系统寄存器输入复用单任务内核模型；
未把零参数当成活动拍摄。当前停603f9f3f读取62293d1c/2B，动态setter与population
尚未执行。下一步追该状态的原厂初始化；S3、S4与安装资格继续待证。

[原生参数池领取与发布](CANDIDATE_PARAMETER_POOL_SIM.md)另完成独立来源分支：
完整603fa59a初始化、604155f4领取/重置/发布及603fa833查找，共6716条指令。
真实槽1指针62293f78、mask迁移和两份324项曲线通过；数组默认值768/32767/−32768
来自原厂reset，新增1952B全部为实际store目的空间，无新增BSS假设。活动writer及
属性9121转换未执行，没有替换暂停的geometry输入；主线仍停62293d1c的34B记录。
其来源已定位到a2743544与6041698a，下一步接通构造/发布，S3与安装资格继续待证。

[状态复制与设备默认值刷新](CANDIDATE_GEOMETRY_STATUS_SIM.md)新增3122指令：
34B记录的17次复制通过，32B仍明确限定为首次发布前BSS；完整601ede5e从已有ROM
默认数据写出三项512，真实消费者已读取。随后原配置因C011默认0不在65个有效
类型键中，进入6040e126诊断0x0e004504，参数(0,65)；没有绕过诊断或执行动态setter。
这证明当前默认配置不能继续充当有效拍摄输入。下一步追C011原生更新并从配置入口
重跑，保留冷态失败证据；不在暂停帧中替换单一类型。活动34B来源、population、
worker与S3/S4/安装资格仍待证，fishcu五组件研究包不变。

[C011原生公共设置](CANDIDATE_MODE_PROPERTY_SIM.md)现已完整返回：原厂条件调用提供
ID24/value3，1333描述、439回调、201关联规则由原生函数建立；96个直接关联属性
按ROM顺序处理，含嵌套共105次。新增1,065,004指令，观察最大新栈深960B。最终
改变12个标量及8b54暂存记录，C011与暂存均为3；partial capture未改变。共享RAM
别名、3B冷BSS与18B原initialized-data条件明确保留；真实模式事件、post-hook注册、
资源队列清理仍待证。下一步刷新原快照并以新栈重跑6042760c，旧失败配置不续接。

[新快照与完整几何构造](CANDIDATE_RECONFIGURED_GEOMETRY_SIM.md)现已通过：完成原生
曲线和模块初始化，快照offset9实际由0变3；新栈6042760c查表匹配第4行/key3，执行
动态setter并以19个word发布76B配置，完整返回且SP恢复。新增1062B均为原生写入
容量，无新增BSS条件；4B沿用原initialized-data配方。旧partial capture保持不变。
未配置格式、无设备及任务调度切点仍明确保留；下一步从模板初始化/prewrite重新
执行完整population，不能恢复属性更新前的旧帧。S3/S4和安装资格仍未整体完成。

[完整第一段capture填充](CANDIDATE_FRESH_POPULATION_SIM.md)现已通过：模板重新原生
初始化，实际602a44a3候选桥执行prewrite与6833word复制，再完成98次属性读取，
候选sample观察器返回602a44a8。第二段实际入口随后停6006d68c读取98e0009c/4B，
尚未finish。新增81,009指令，观察最大新栈深460B，没有新增映射或BSS条件。原生
raw mode/selector为0/0，不满足COLOR冻结条件；没有伪造有效拍摄或新分配代际。
下一步追第二段硬件输入和6223d41c请求对象生产者；完整生命周期与安装资格仍待证。

[第二段寄存器与日期记录](CANDIDATE_POSTPOPULATION_CLOCK_SIM.md)已接通：3个明确
模拟寄存器共12B，原ready字段RMW、日期解码/校验与capture写入实际执行，新增958
指令、最大观察新栈深144B。输入是固定2021-01-01与非零子计数，不代表相机时钟；
外层控制器握手未执行。当前停602a8e9c读取请求对象offset2166；已定位76B消息
处理写入及602a471d尾段reset两条来源，下一步接对象构造。第二段/finish仍未完成。

[原生Standby参数与入口回调](CANDIDATE_STANDBY_PARAMETERS_SIM.md)已在独立分支完成：
原服务初始化、完整16B参数构造/刷新、原发布及状态11完整入口回调，共932条指令，
最大观察新栈深48B；223B原生store容量，只有1B首次状态发布前冷BSS条件。4B flags
投影沿用已有明确输入，不代表完整76B消息。capture与主线暂停现场不变，offset2166
仍未产生；下一步执行类型11消息片段与请求构造，保留dispatcher和生命周期缺口。

[类型11消息片段与完整请求构造](CANDIDATE_REQUEST_CONSTRUCTOR_SIM.md)现已通过：
原发送后缀、完整接收materializer、flags分类和602a471d实际执行，共541条新指令，
最大观察新栈深96B。68B新store容量、8B明确消息输入及2B首次激活前BSS条件；
76B command仅映射38B，分配/完整模板复制/队列投递未执行。原生offset2166清零后，
消费者继续6条指令停在对象+512格式halfword；下一步追6055545e格式记录生产者。

[原厂格式资源归属拒绝](CANDIDATE_REQUEST_FORMAT_GUARD_SIM.md)已复现：563条新增指令，
最大观察新栈深180B，84B格式输出容量，无新增BSS。原6029b85a要求registry mask1，
当前capture-only标志4触发真实诊断25000402；格式+88仍为A5，半成品未供消费者使用。
下一步复用既有分配归属分析，执行6029be82依赖的原厂资源池；不直接修改标志或ID。

[原生辅助资源与完整格式构造](CANDIDATE_REQUEST_RESOURCES_SIM.md)现已接通：前三池
原生构造、6029be82取得handle0001/0101并自行设置mask1，完整6055545e返回。新增
3903条指令，最大观察栈深200B；1119B store容量、27B明确冷BSS及1B单竞争者锁模型。
原锁获取/释放与计数迁移通过，图像backing未映射；已有ID1不等于新capture代际。
消费者实际写入格式字段后停在offset1684；下一步追1684/1686及command+60/+72来源。

[完整消息参数准备与分类](CANDIDATE_REQUEST_PREPARATION_SIM.md)再完成1064条指令，
最大观察栈深164B：完整602a4a5c、服务刷新/暂存/4计数器reset与602a6630返回。16B
输入沿用首次状态发布前BSS，模式输入8B由原reset片段写出。修正旧FIFO前canary
覆盖13B原厂状态的过宽边界，FIFO/剩余保护区与capture不变。下一步原metadata槽
领取和初始化；command+60仍NULL，主线1684/1686及完整生命周期继续待证。

[原生metadata领取、发布与重用](CANDIDATE_REQUEST_METADATA_SIM.md)完成563条新指令，
最大观察栈深56B，35B真实store容量，无新BSS。原调用者发布command及其+60指针，
完整参数初始化返回；独立release/reclaim证明同槽重用保留旧数据和旧command引用，
指针不能替代代际。状态生产者读到原生halfword1024后停在未知command+72，主线
1684/1686未续接；下一步追flags来源或明确输入模型下的条件验证，保留生命周期缺口。

[第二段完整返回与finish拒绝](CANDIDATE_POSTPOPULATION_FINISH_SIM.md)已完成9758条
新指令，最大观察栈深404B。两组明确flags/未知halfword模型执行原状态片段，原
temperature片段接入sample25；11B原store容量、4B冷debug BSS及8B模型输入。第二段
原尾部和候选finish实际返回602a44ba，SP恢复，私有锁释放。核心finish返回false，
当前raw0/selector0和重填充token没有封存旧快照。完整输入来源、请求/调度未因此
关闭；下一步原生COLOR设置与新capture/node代际，继续S3/S4及恢复准入。

[原生COLOR4设置与回读](CANDIDATE_COLOR_PROPERTY_SIM.md)已完整返回：显式公开111=64
由原setter解包11/4/0，43次raw pair及依赖后返回0，原getter回读64。新增269966
指令、最大观察栈深756B；147B真实store容量、6B冷BSS，原两资源header和信号量5e
单行初始化完成，两次wait/signal均释放。旧capture/sidecar未改变；下一步原新
capture/node分配和COLOR填充。新增S4具体任务：原domain0有132个静态信号量、下个
自动ID133，须建立独立完整原配置上下文验证私有runtime，不能沿用S2的ID1假设。

[实际候选入口的新capture分配](CANDIDATE_CAPTURE_ALLOCATION_SIM.md)已接通：原信号量19、
池1500及选定ID2 reset后，实际602a4480入口完整执行准入和注册表分配，取得ID2与
af6037c0、handles2/102/1501。新增7716指令，最大观察栈深280B；509B原store容量，
其中10B来自旧夹具保护区重叠修正，另1B冷BSS。旧ID1/capture/sidecar保持不变。
分配完成检查点锁已释放；独立续接停pool3200 header读取，其信号量19仍在持有。
下一步原pool3200、FIFO、node heap/关联对象与fresh登记；完整node和COLOR填充
尚未完成，S3/S4、驻留与恢复准入继续保留。

[完整node factory与fresh登记](CANDIDATE_NODE_FACTORY_SIM.md)现已返回：原pool3200/FIFO、
关联reset hook和完整25槽初始化后，实际factory取得node61b21fc0、associated6223e164，
fresh查询ID2/af6037c0并登记token2。新增29312指令，最大新栈深348B；308B store容量、
41B原只读store开放、8B明确冷heap BSS。原空FIFO拒绝分支保留；reset先撤销旧登记、
保留serial，但真实任务中reset的合法时机未证明。associated旧backlink尚未更新，
下一步原node准备与COLOR population；生产内核、生命周期、驻留及恢复仍待证。

[新COLOR4填充与H/L冻结](CANDIDATE_COLOR_POPULATION_SIM.md)已完成两段：新node原生入队，
6833word模板复制后raw11/selector4，token2在第一段采样5/-3；实际API改当前设置为
-3/2后，第二段finish仍封存5/-3且不重采样。新增89051指令，最大新栈深420B；
27356B原store/copy容量，无新BSS。原请求/格式与固定硬件输入的离线条件仍保留，
完整新请求生产者未执行。下一步原队列领取、selected event的backlink发布、
source copy与job消费/释放；S3/S4、驻留与恢复资格未因此通过。

[原生node队列领取](CANDIDATE_NODE_SELECTION_SIM.md)已完成：原engine参数与5900/3400
两池初始化后，完整selector领取新node，原格式18准备与序号1写入，实际FIFO出队；
空队列再调用返回NULL。新增2515指令，最大新栈深208B；379B原store容量、24B冷BSS
和1B单竞争者锁输入。token2/H/L5/-3不变。generic engine workrecord调度、活动帧
坐标和新请求来源未关闭；下一步原event4b投递/接收与selected handler/backlink。

[新节点原生event4b邮箱](CANDIDATE_SELECTED_MAILBOX_SIM.md)已接通：原冷heap、静态mailbox、
固定消息池1和flag74的实际初始化后，完整通知回调发送实际新node，再由原接收入口
取出并归还消息块。新增2548指令、最大新栈160B；296B原store和12B输出容量，空读
返回-1，池余量恢复16。封存值不变。仍未执行notification clear/wait、真实任务切换、
generic completion dispatcher或selected handler，冷heap场景不证明生产启动。
下一步原selected handler/backlink、源复制及异步消费/释放；安装准入保持未通过。

[selected参数准备](CANDIDATE_SELECTED_PARAMETERS_SIM.md)已生成原序列/场景状态及双
描述符，实际ID2资源查询和ROM字段进入原构造器。新增1346指令、最大新栈156B，
84B原store容量；完整handler入口内第一参数helper返回，第二helper停metadata
+50读取（后续还需+48/+52）。8B部分capture变化保留，封存值/旧backlink不变。
下一步追结果字段的实际生产者，不以默认值越过缺口；handler/backlink及后续异步
生命周期仍未完成，S3/S4与安装准入不变。
