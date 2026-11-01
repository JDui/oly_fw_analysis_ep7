# E-P7 研究检查点 / 恢复研究

**2026-11-01 最新：007D实机启动失败，暂停安装及重复测试。** 用户报告安装后首次
启动能显示蓝牙图标、手机能连接，很快自动重启；此后黑屏反复重启且蓝牙不再出现。
这是现场观察，没有停止PC、复位原因或看门狗证据；本次AF状态及007D后的原厂恢复
结果尚未提供。不能把006的AF熄灭/已恢复状态复制为007D事实。
007D恢复全部22处GUI补丁，保留006的76处其他补丁；其失败说明恢复GUI组不足以解决。
原生bootstrap/私有锁133发布和零值冻结等局部验证不覆盖实机完整启动。保留BIN/ZIP，
交付目录增加STOP-INSTALLATION.txt。继续查共同启动、内核队列和拍摄改动。

用户指定后续按fishcu PEN-F的 **NAT（Natural）＋A档** 刷入；已核对上游安装说明。
后续在工作正常的原厂固件中先设置此基线，首次启动保持Natural，先观察稳定画面、
菜单和回放，再进入COLOR验收H/L。007D刷入前是否已采用该设置未知，不能回填。
该选择不证明重启原因已修复，不要求重新安装005/006/007D。详见[事件记录](BOOT_FAILURE_005.md)。

本轮新增[首次接收等待检查](../../research/ep7/candidate-007d-startup-receivers.json)：
原厂/007D分别从task21/57/6c的实际入口执行，均到达相同类型的原厂等待入口；007D
没有立即布局拒绝或重复poll。任务交付/栈/内核状态仍是明确模型，未执行等待完成、
调度或真实复位。没有修改生产代码或生成008；根因未知，不继续推荐007D。

历史007D离线交付：[分组诊断包](EXPERIMENTAL_SD_007D.md)复用006编译代码；整段GUI
等于原厂，范围外等于006。fishcu封装及ZIP回读通过，未重编译、无SHA，无H/L编辑入口。
COLOR构造模拟停在未建立的C++/调度等待状态，不是实机故障复现；正式H/L目标不变。

**2026-11-01 最新实机状态：006启动仍失败，暂停安装。** 用户在A档、前拨杆COLOR
下开机，黑色画面左上曾出现闪烁蓝牙图标，随后全黑；数秒后疑似重启，但蓝牙图标
没有再次出现。AF辅助灯一直熄灭。此观察不足以确认CPU复位，也不能排除依赖原厂
服务的终止分支。用户随后已回刷原厂；下方“006未上机”是历史
状态。005与006包保留，禁止将离线通过记录解释为本次启动通过。继续追查共同启动/
COLOR构造路径；真实停止PC仍未知。详见[事件记录](BOOT_FAILURE_005.md)。

**2026-11-01 最新交付：[006实验修正候选](EXPERIMENTAL_SD_006_DELIVERY.md)。**
源码`a059e5f`，构建`generated/ep7/flash-build-006-r2/`，交付
`generated/ep7/flash-packages/EP7HSL-006-EXPERIMENTAL/`。未绑定拍摄任务时的原厂回调
不再误停机；已绑定后仍严格保护。新增原厂AF helper故障提示；信号实机可见性待测。
最终候选boot-guard、H/L编辑/冻结、worker、加载、SD隔离、fishcu容器校验和原生
mode1路由通过；按最小必要测试要求没有重跑全包原生mode2解码，没有SHA。
用户补充005故障前为A档、前拨杆COLOR。当前机身原厂已恢复，006仍未上机；下一项
外部证据是同一条件下正常开机、菜单/回放及AF灯状态，再分别验收编辑与照片。
005唯一根因仍未确认，不能把一个已修正的离线反例等同于真实停止PC。

**2026-11-01 最新事件：005 实机正常启动黑屏，暂停安装。** 用户确认常亮转快闪后
关机、取出更新卡、不按 OK 重开仍黑屏、菜单/回放无反应；曾重复刷同一实验包。
用户随后用 `restore-stock` 原厂文件回刷，已恢复画面和菜单。新增原生静态分配对比
通过：005 多占 1,152B，仍余 179,112B 空闲块；这个场景没有出现内存耗尽。
当前没有定位到真实停止 PC/错误码，不能把终止循环假设写成已确认根因。
优先读取[事件记录](BOOT_FAILURE_005.md)，不要按下方历史“可交付”状态继续推荐 005。

## 2026-11-01 当前目标与节点

当前目标为尽快形成基础可刷入固件、到达实机硬件测试阶段；每个关键节点提交推送。
用户选择首版保留色轮编辑和照片处理的基础H/L，未选择只有标记的原厂启动探针。
用户确认没有经过验证的固件备份和独立恢复手段，先继续离线验证。
[推进计划](FLASH_READINESS_PLAN.md)保留完整目标；下面 10 月 31 日的“编译阶段完成”
不表示当前目标完成。

2026-11-01资格复核：用户进一步确认目前没有启动ROM、完整flash镜像或维修恢复
资料。现有包仍为NONINSTALLABLE，S6不通过。此前多个节点持续保留的prefix/所有权
与恢复缺口没有新输入可关闭；当前目标受阻，未完成。恢复工作需新增相关启动证据
或已验证的独立恢复条件；不重复编译/封装/同类模拟来替代缺失证据，不操作相机。
现有REPL与研究文件保留，未终止或重建共享环境。

最新：[fishcu离线材料与台架出口](FLASH_BENCH_REVIEW.md)已整理到
`generated/ep7/offline-review-kits/candidate-004/`。既有候选原样复制，原厂五组件用
fishcu reconstruct重建，两份各111,017,984B、全字节回读相等，另附10份已有报告。
原厂参考不是本机备份或已验证救援。没有重编译、重跑原生测试或创建安装目录。
当前S6审查仍未通过：prefix/所有权/完整栈/硬件可见性及独立恢复缺证。下一轮优先
取得能定位启动/池/guard的新增资料或合格恢复条件；不要重复同样模拟或扩展全ISP。
用户已答复目前没有可只读分析的启动ROM/完整flash/维修资料。

本轮只读查询fishcu上游默认分支及现有issue：E-P7检索结果仍为跨机型比较，恢复
参考指向PEN-F；没有取得能关闭上述E-P7缺口的新证据。这是定向检索结果，不是证明
资料不存在，也没有向上游发送消息。

此前：[最终候选加载接续/驻留](CANDIDATE_RESIDENCY_SIM.md)完成16,514条指令。原loader
三次读取实际候选657,408B后，刚加载的清零桥清16KiB并保持ABI/guard。103个跨度
中100个有已定位加载配方、3个prefix仍缺上游加载证明；22项已知原写区间不冲突。
五组件8字面量有界调查未找到prefix加载者或guard初始化者；没有提升为完整所有权。
物理cache、冷保留/池容量、完整栈与恢复继续待证。接下来整理fishcu候选和五组件
原厂恢复参考/台架验收，不再无限扩展未改动的ISP模拟。固件和研究包均未改变。

此前：[worker分配/登记/撤销/ACK](CANDIDATE_WORKER_JOB_SIM.md)通过24,686条指令，
观察新栈860B。原allocator实际收到15512并取得domain0槽61bd6d40，新24B先清零；
process桥登记冻结值，实际postbuilder点写出三项预期系数。真实poll133注入一次
争用，cleanup遇−50保留job/token，经一次明确delay完成模型及真实signal后才撤销、
进入原job析构/池free。payload即时unmap后正常返回，ACK先退休ticket再构造消息，
迟到observer不读旧job。原stock构造/转换/处理与ACK交付为边界；真实kernel/池初态、
任务交接仍为fixture。无固件/包变化；继续代码与私有RAM启动驻留的集中审查。

此前：[GUI编辑与共享冻结](CANDIDATE_UI_EDITOR_SIM.md)通过443,699条GUI链指令。
完整原预处理/最终veneer、实际container CALLS/parent桥及原viewer缓存接通；H第1区
+3、H第3区−2、L第3区−4进入同一core，原生poll/signal133共46次，capture API
冻结25B逐项一致。同dispatch重投拒绝，退出后session/receipt撤销，内容/文字回收，
撤去graph映射后late refresh无访问。观察栈820B含模型256B投递帧。MVC图初始
category2/contentNULL，stock创建/销毁、engine本体及显示输出仍为明确边界；不算
完整COLOR界面或照片通过。候选/fishcu包未变，接下来收敛worker和驻留的剩余风险。

此前：[原生文字控件与owner撤销](CANDIDATE_UI_OWNER_SIM.md)通过16,637条指令，观察
最大新栈408B。实际factory/constructor/attach/find/bind/setter建立180B文字child，
两种H/L文字更新与上下文恢复正确；OOM关闭display资格且不重试。cleanup、bulk与
cleanup后destructor完整返回，候选引用在原生free前撤销，释放payload即时unmap，
零剩余模型分配、迟到更新拒绝。request278完成图、分配/通知/单GUI锁、空原队列与
timer是显式边界；MVC未注册，不宣称完整编辑或LCD。无固件变化，下一项编辑会话
联通，然后worker/驻留和安装资格。

此前：[最终GUI输入机器码](CANDIDATE_UI_INPUT_SIM.md)通过7个场景/75,479指令。
完整原预处理、五处已安装JMP veneer、原halfword setter及candidate scope/dispatch
实际执行。完整7/−4计数不丢失，所有原输入寄存器/SP和原返回PC/MDR保持；超限65
和服务失败不留下编辑资格。engine body在原入口截停并按明确返回模型完成，未取得
完整parent/widget/显示资格。动态GUI任务/非modal状态为fixture；最大新栈716B
仅是该链观察值。无重编译/包变化/相机操作，继续基础功能及驻留风险。

此前：[SD软件入口](CANDIDATE_SD_ENTRY_SIM.md)完成1,624条指令。原callback取得最高
有效后缀；原pattern wrapper在E组成功后停止G/H/W。task88构造的32B消息原样
交付task18，真实type1分支将buffer a43a3ec0/长度111,017,984/mode0传到60c964c1。
底层文件查找/读取、queue和设备准备为显式模型，callback的FAT32 getter与排序、
两task的消息及分流实际执行。只读取实际包头，未重复完整解码；物理启动按键仍
未证明，无安装文件输出。下一项基础GUI/worker及驻留资格，避免扩大文件系统模拟。

此前：[原生共享更新器接收与路由](CANDIDATE_UPDATER_SIM.md)完成两个阶段。实际五组件
111,017,984B包mode2完整解码/校验/型号分流返回0，无写入且五份decoded等于fishcu。
首次运行后续主机地址别名断言失败，mode2明细JSON未落盘；观察记录明确保留这点。
修正只main转换地址的断言后，commit-only重跑通过：010e先服务路由到40002800，
再0102/0106/0101/main四次flash请求，main最后到806a0000；首次flash错误3102
阻止后续三次请求。所有写出口截获，未执行物理更新。下一步SD文件选择/入口、
基础GUI/worker及驻留资格；不重跑已完成整包校验，不自动升级安装资格。

此前：[新COLOR4捕获交接契约](CANDIDATE_SELECTED_HANDOFF_SIM.md)通过55,434条指令，
最大新栈368B。旧backlink拒绝，原厂两条发布指令后实际ID2/af6037c0复制冻结5/-3；
patched FIFO第二位置入/出队保持值，原prewrite候选撤销后同元素出队但scope全零。
只开放原backlink4B写权限，无新输入值；两份capture不变。selected handler的原曝光/
格式处理是明确完成边界，没有补metadata或宣称完整handler通过。后续按首版收敛
检查改动的GUI/worker消费边；S4驻留、物理更新入口和恢复继续保留。

此前：[生产静态信号量后的私有锁](CANDIDATE_STATIC_KERNEL_SIM.md)已通过。执行原厂60B
计数复制、255个ID清除和完整132行静态初始化后，候选取得ID133/6219b448，成功
发布runtime；COLOR4编辑/冻结的原生poll/signal均使用133。queue4c失配时原生回收
同一ID、used恢复132，全部原厂静态对象不变。修正的是测试的ID1假设，固件004未变。
更新器主线已定位60c964c1，正在执行实际五组件原生解码/校验和截获写入路由。
计划已按基础H/L收敛，不要求继续重演所有未修改的原厂校准内部流程。

此前：[selected参数准备](CANDIDATE_SELECTED_PARAMETERS_SIM.md)完成1346条新指令，最大
新栈156B。原序列reset、场景property gate及完整双描述符constructor接通，84B
原store容量；实际ID2/handle102资源指针af43ad40、ROM6055d290、首descriptor kind10。
实际event4b输出进入完整602a281a，602a8877已返回，602a91ee停602a92df读取metadata
6223e450+50，+48/+50/+52结果尚缺生产者。新capture仅8B真实部分写入，封存sidecar/
H/L、旧capture和旧backlink不变；保留原停止栈/寄存器，未补零或跳转。下一步追踪
metadata结果写入再恢复handler。候选004/fishcu包不变、不可安装；无SHA或相机操作。

此前：[新节点原生event4b邮箱](CANDIDATE_SELECTED_MAILBOX_SIM.md)完成2548条新指令，最大
新栈深160B。原冷kernel heap、mailbox1、fixed pool1和flag74配方实际初始化后，完整
602a3042发送新node61b21fc0，完整6020c101取回并归还块；余量16→15→16，空读返回-1。
296B原store和12B输出容量，padding按不透明栈残留检查。封存token2/H/L及capture不变。
通知flag仍1，未执行clear/wait、generic completion dispatcher或真实task handover。
下一步完整selected handler及backlink发布；首次探针停60555155读6223ceac，未补值。
候选004/fishcu包不变、不可安装；无SHA、固件重编译或相机操作。

此前：[原生node队列领取](CANDIDATE_NODE_SELECTION_SIM.md)完成2515条新指令，最大新栈
深208B。原168B engine参数、pool5900/3400与format reset接通，完整602a2d43领取
真实新node61b21fc0，原生handles5901/3401、1280x960、格式18、序号1，FIFO计数归0。
第二次调用返回NULL，无重复分配/pop。379B原store容量、24B明确冷BSS（特殊坐标与
扩展flags）、1B单竞争者锁模型；两对dispatch disable/enable释放。封存token2/
H/L5/-3及新旧capture不变。generic engine dispatcher仍未执行，backlink仍旧，
下一步原event4b投递/接收与selected handler。候选004/fishcu包不变、不可安装。

此前：[新COLOR4完整填充与H/L冻结](CANDIDATE_COLOR_POPULATION_SIM.md)完成89051条新增
指令，最大新栈深420B。原pending FIFO与完整602a3204将新node入队，实际caller
prewrite/6833word复制后完整第一段读99个原属性，raw11/selector4，token2采样5/-3。
随后实际edit+回读把当前COLOR4改为-3/2，完整第二段finish返回1，封存仍5/-3且
没有重采样。最终回602a44ba、SP恢复；新增27356B原store/copy，无新BSS。旧capture、
ID1和模板不变。请求/格式仍沿用最初ID1的离线状态，完整新请求未执行；旧associated
backlink仍19510000。下一步原队列领取、selected事件发布与异步消费。候选004/
fishcu包不变、不可安装；无SHA、固件重编译或相机操作。

此前：[完整node factory与fresh登记](CANDIDATE_NODE_FACTORY_SIM.md)完成29312条新指令，
最大观察新栈深348B。原pool3200/FIFO、完整关联池初始化接通；实际factory原生分配
56B node→61b21fc0、associated→6223e164，候选fresh查询ID2/af6037c0并生成token2，
返回602a4485、SP恢复。原空关联FIFO触发25002701的拒绝分支保留。实际reset hook
先撤销旧sidecar、保留serial，再重建25槽；这是显式reset场景，真实调度合法性待证。
新增308B store容量（36B旧canary重叠修正）、41B原只读store开放、8B CPU0小heap
冷BSS。旧capture/ID1注册表不变；associated旧backlink仍19510000，需真实发布。
下一步node准备与COLOR两段填充。候选004/fishcu包不变、不可安装；无SHA或相机操作。

此前：[实际候选入口的新capture分配](CANDIDATE_CAPTURE_ALLOCATION_SIM.md)完成7716条
新指令，最大观察新栈深280B。原信号量19、25槽capture池1500和选定ID2 flag reset
执行后，实际602a4480候选入口完整执行准入及注册表分配，返回ID2/af6037c0；原生
handles为2/102/1501、flags5，旧ID1/capture/sidecar不变。509B原store容量，其中
10B纠正旧夹具保护区与真实下一行的重叠，另1B明确冷BSS。602a3151检查点逻辑锁
均释放；独立续接停603dbd40读下一池3200的a269e9c4，该暂停现场信号量19仍持有。
node heap/associated/fresh未进入；下一步原pool3200与FIFO初始化，再接完整node
与COLOR填充。候选004/fishcu包不变、不可安装；无SHA/固件重编译/相机操作。

此前：[原生COLOR4公开设置与回读](CANDIDATE_COLOR_PROPERTY_SIM.md)完成269966条新增
指令，最大观察新栈深756B。完整602afa11接显式111=64输入，原解包111/908/973为
11/4/0，43次raw pair及全部依赖后返回0；完整602afa81回读64。原603dc386 reset、
603dc8f8两资源header及ROM信号量5e单行初始化完成；147B原store、6B明确冷BSS。
两次wait/signal配对、count回1、逻辑锁释放。只有9481/f6b1/8b91及8b54两位置变化，
旧capture/sidecar不变。原kernel semaphore recipe为next133/used132，当前S2仅
next2/used1的私有ID1 fixture尚未替换；单行5e初始化不等于完整启动，需独立验证
真实静态配置后的私有ID分配。下一步新capture/node分配及COLOR两段填充，不给旧
token补造代际。候选004/fishcu包不变、不可安装；无SHA/固件重编译/相机操作。

此前：[第二段完整返回与finish拒绝](CANDIDATE_POSTPOPULATION_FINISH_SIM.md)完成9758条
新增指令，最大观察新栈深404B。原状态片段6029d0b0..d1cc两组显式输入各181条，
生成1666/1684/1686=0/1/0，PC路径相同；command+72及请求+1914共6B来源未证明。
原temperature getter/store片段8条，以明确sample25输入生成25/0/0；没有传感器
采样/物理单位证明。新增11B原store容量、4B冷debug BSS、8B模型输入。第二段
继续9388条，原尾部清零512B，候选finish进入一次，返回实际602a44ba且SP恢复。
当前原生raw mode/selector0/0和重填充token不满足资格，核心finish返回false，
旧sidecar未封存、未更换代际；capture仅offset14406新增模型值25。下一步原生
COLOR设置与新capture/node分配。完整请求/调度/worker/驻留/恢复仍待证。前置已
完成原metadata领取/发布/初始化，独立释放重领证明同地址保留旧数据和旧引用，
见[CANDIDATE_REQUEST_METADATA_SIM](CANDIDATE_REQUEST_METADATA_SIM.md)。候选004/
fishcu五组件容器不变、不可安装；没有SHA/固件重编译/相机操作。

此前：[冷态快照完整回调与配置续接](CANDIDATE_SNAPSHOT_OUTPUT_SIM.md)关闭原输出构造器、
60426f83回调及6041a20a包装函数的冷态返回。两GPIO各240+85+88+199+49，共1322；
原返回6042705e/6041a224/60409ecb均核对，最终SP1901076c。仅160B原输出成员A5，
9个洞123/145/155/160..165仍未映射；额外10B转换store与2Bwrapper status0。121B
原copy与源相等，4half坐标copy通过；原整数换算中间值83/74。新增冷BSS条件12B：
fallbacka2788dec+12指针4B及未发布坐标622a094c/8B；活动writer604288f9/6028f3ef
未执行。快照指针6229fc48，selector0002；任务后续交换/收发、上游调度切口未关闭。
恢复原configuration栈/寄存器后，两GPIO各543，共1086，60419f58真实返回6229fc48。
当前fault60427ec6读622a06b4/2B，MDR6005c8df；setter6042805e未进入，population
未恢复，capture27332B不变。新观测栈880非完整上界。静态来源60425ba3的60425d03/
60425d0d/60425d1b分别从输入+128/+144/+196写b4/c4/f4三数组，8组；调用点604270d2，
源对象未接通。下一步追真实输入，不能补零活动数组。正式两报告和5个中间报告保留。
候选004/fishcu五组件包未变、不可安装；无SHA/重编译/相机操作。

此前：[原生未配置格式与getter返回](CANDIDATE_FORMAT_SNAPSHOT_SIM.md)新增14672指令，
两GPIO各reset1235、producer329、device defaults5169、完整mode563、producer40。
606a4a09/606a4a41完整reset写两个ffff、清123B/121B、设28B记录；277B原生目的。
601f25f8完整返回，3362B原生目的，3段ROM及2段1084B二次copy合计3336B逐字节相等；
原对齐对象指针a2682d00，稀疏成员+9432/+35604 reset。仅+1092/1093这2B通信状态
与旧mode295的1B沿用明确冷BSS条件。606d47fc完整返回，10次属性查询，新增9B目的
及7处store均核对。原6065e658/60556934格式getter返回60427f7d，150B栈记录含
121B空payload与+146状态2，表示未配置格式。当前fault60427f9c写6229fb98/2B，
MDR60427f86；下一步映射原输出成员并继续，勿认定有效活动格式。新栈深500，上游
676，均非上界。capture不变，geometry/population未恢复；候选004/fishcu包不变、
不可安装。两中间报告保留，正式断言与下一输出节点一起运行，无SHA或相机操作。

此前：[未就绪设备冷态坐标回退](CANDIDATE_OPTICS_COLD_SIM.md)新增736指令，两GPIO各
presence初始化94、两个type reset88、原缓存copy28、原回退101、producer继续57。
600f767d完整执行，四标志0，f8c1/f101指针6250f915/6250f769；原始caller片段两次
601f27ea完整返回，type2826、period500/287。50B原生store目的初值A5；另16B缓存
只在首次帧发布前使用明确BSS/alias条件，未伪造活动帧或补其5B栈来源。601f8ded
真实device NULL/type0/变换不可用，601f8974原样复制两halfword55004c00=(85,76)。
当前fault6065e79c读a2788ab2/2B，MDR6065e77c；已定位606a4a41原生reset写ffff，
606a4a09从6065c09a被调用。下一步执行该reset，不能补零该格式字段。新栈深676
非完整上界，capture不变、geometry/population未恢复。活动对象回调6029350a/
602935e3及60553f2e池分配已静态追踪，所需帧字段仍缺完整来源。候选004/fishcu包
不变、不可安装；无SHA、重编译或相机操作。正式报告由后续格式节点同一次运行验证。

此前：[冷态历史缩放回退](CANDIDATE_HISTORY_SIM.md)新增220指令，两GPIO各selector19、
fallback91。仅a273104a/2B和a2731148/4B使用原厂BSS/alias条件；原60309e4f计算
槽0指针a2731098并写回producer栈，6030407e从原分支返回16.16单位倍率65536。
完整活动记录未构造，其他4896B历史payload仍未映射。当前严格fault47001070读
a271ca80/4B，MDR601f6916；601f6903真实调用47001052复制16B，停在第一项源读取。
新最大观测栈652非完整上界。capture不变，geometry/population未恢复，候选004/
fishcu包未变、不可安装。历史记录+176来自6030c095内输入+332，成功后6030992a/
60309a48才更新索引，均未执行。16B缓存写入601f66f7的唯一直接调用点60293a9f：
60293a65从外层对象构造11B字段，缓存偏移4/9/10/11/15为未显式写入的栈字节。
下一步追该外层对象与缓存发布，不能整块补零；活动历史构造仍为独立待证。
正式report固定倍率/16B复制/frontier，保留selector及cold两份历史报告。初次新增
witness长度笔误已改成证据自身长度；无SHA、重编译或相机操作。

此前：[原厂诊断缓冲区与格式记录](CANDIDATE_FORMAT_RECORD_SIM.md)新增55234指令，
两GPIO输入分别为cold suffix26872、record reset prefix240、producer resume505。
60556bb2原现场继续至60556b1e完整返回；原厂分配60022700/600228b6取得CPU0 big
槽0/1的61bd6d40、61bdad80，各16384B，stride4040。counter2/bitmap3、2048条记录
初始化逐字节核对，64B slot guard未映射。依赖16B空池/空指针BSS和临时pre-kernel
锁寄存器模型，后者已移除；真实占用/启动顺序/并发仍未证明。格式reset606d4593只
到606d4645，五halfword从a2788cf6到a2788cec，原getter再复制五项到producer栈。
源仅7B补入明确BSS初态，其余3B为真实冷store；目标7B及额外8B状态从A5开始。
日志实际写入init字符串、timestamp1234与参数0，游标[1,0]；计时寄存器9890014c
输入3fffedcb是明示固定模型。当前严格fault6030b752读a273104a/2B，MDR60309e5c；
60309e4f/6030b745按索引选择a2731098起的5份980B历史记录。下一步追源初始化与
发布，不直接补零索引和活动记录。最大新增栈深564非完整上界，capture不变，
geometry/population未恢复。候选004/fishcu包未变、不可安装。正式report与历史
frontier保留；没有SHA、重编译或相机操作。

此前：[格式模块发布与状态](CANDIDATE_FORMAT_STATE_SIM.md)执行cold RAM前缀33、core前缀11、
2af4原生掩码复制45、完整606bbffc发布2768、48槽cache1586、6字段mode刷新300；
原snapshot producer再推进447指令。两GPIO分支总10380，新增观测栈580非完整上界。
13个原生字符串325B核对通过，48指针匹配原属性bank，6个字段由实际getter产生。
60693455的7处store生成10B记录a2788aa4=00000000010001000000；这些默认属性值
不是实机格式。当前严格fault606d673a读a2788cec/2B，MDR60664e1e。它要从对象
a2788cb0+60复制5halfword；606d4593有+70到+60复制，606d18bf附近有+80到+60复制。
下一步追源记录/更新，勿直接补零活动字段。新增映射706B，仅idle字节a2788cbf使用
明确BSS/alias条件。冷reset停60556bb2前，两份16384B诊断buffer分配未运行；核心
6065bff0只到6065c01e，mode刷新只到606d4898，完整启动未证明。format_context保留
configuration原栈/寄存器和producer新停止现场。候选004/fishcu包未变、不可安装；
geometry/population未恢复、capture不变。保存4个中间frontier与正式report。

此前：[原厂请求与快照字段](CANDIDATE_SNAPSHOT_SIM.md)执行128B原厂0501请求构造299、
请求复制215、任务前缀92、分发/producer前缀4832条指令，各GPIO分支均通过字段构造
6042661b返回与124B缓存复制一致性；完整producer/wrapper未返回。新接通service38、
157槽清零164/147槽注册4889、相机状态RAM后缀20、16项history初始化138。总21374，
新增观测栈深280，非完整上界。当前严格fault60556934读取a2788ca8/1B，MDR60427f7d。
格式模块原厂60556b1e重置置0、606bbffc在四helper后置1；0分支是缺省格式，1分支
6065e658才取模块状态，不能伪造1或把冷缺省当实机尺寸。保留四个中间frontier报告。
configuration原栈/寄存器在snapshot_context输出中保留，capture不变；没有resume
geometry/population。任务receive/log仍为明确切口，原BSS只供126B条件初态。候选004
及fishcu研究容器未变、不可安装；下一步格式模块生命周期与完整producer续接。

此前：[原厂容器解码/局部校验](CANDIDATE_PACKAGE_NATIVE_SIM.md)通过。010e完整262144B
原生解码1228520指令，等于fishcu主机结果；main完整26214400B原生局部校验39321696
指令返回0，A0终点21900000。头尾差异30指令返回3202；010e一字节损坏393312指令
到6002266d错误日志入口，sum1/MDR60c95ad4，未stub日志/声称3211后缀执行。合计
40943558指令，无SHA/固件写入/真机。原厂wrapper是5B CD，不是7B DD；首次witness
纠正，完整main首次45s超时后仅该调用放宽180s并成功。通过后不重复大循环。
S5完整更新器/写入/恢复、S3/S4仍待证。几何快照追踪新发现：60419d2b返回6229faf8
的128B请求对象；60419d34从A0原生复制128B。queue17任务60409ead复制请求，60409eb6
重置双快照，60409ebf从请求+4取producer回调、+23取mode，再60409ec4调用6041a20a。
仅为静态来源线索，尚未执行producer。下一步追踪该请求的原厂生产者及回调指针。

此前：[fishcu流程五组件研究容器](CANDIDATE_PACKAGE.md)已输出到
generated/ep7/research-packages/candidate-004/，111017984B。直接复用oly_container的
parse/replace_payload/reconstruct；E-P7型号1420、五组件顺序/地址/各自版本字段保留，
后四组件完整编码字节未变。主组件对实际ELF和101处patch重建一致，共103写入跨度；
parse/落盘回读通过，2组件/错误型号/换序三负控制拒绝。无SHA/重编译/相机操作。
产物名EP7HSL-NONINSTALLABLE.research.oly，不建DCOLYMP；命名不是设备强制拒绝。
S5仅容器子项通过，完整更新器/恢复和S3/S4均仍待证。下一步可独立执行原厂局部
校验器；处理链仍从下述124B几何快照producer继续，未放弃S3。

此前：[原厂冷状态与几何快照](CANDIDATE_SERVICE_STATE_SIM.md)接入RAM后缀160、诊断
初始化799、参数前缀169、pending reset5、task reset2条指令。两条原geometry现场
分别继续3177/3454指令，均停6041a5bb读6229fc44字节，MDR60419f58；动态setter
未执行，capture不变。两个中间frontier报告保留。39-halfword拷贝的78B参数源
62221998..622219e6只缺padding e1；仅该1B使用已定位BSS清零条件，合并完整有来源
record供严格halfword读取。GPIO80=1原厂39次写入逐值/地址验证；另一分支0次。
新增8901指令，110处store+数组共1054B。map_initializer_storage抽为共用helper，
上游链实跑通过。前置外设时钟、完整task及属性服务后缀未执行，不能算生命周期通过。
下一步124B双快照6229fc48及selector来源：6041a51c读旧快照/重置，6041a551轮换，
60419529初始化指针/回调，6041a20a调用真实producer；不要自动补零活动快照。
候选004未变/不可安装，无SHA/真机操作，最终封装仍用fishcu流程。

此前：[设备输入与配置分支](CANDIDATE_DEVICE_INPUTS_SIM.md)以14个明确寄存器输入关闭
两个采样停止点。仅切换logical GPIO80 bit4，两次native采样resume各635指令，
bitmap/shadow为0000/0200；五引脚采样各32、完整601168ba重置各183指令，通过。
真实1215查询305/304指令返回1/0。恢复原geometry栈/寄存器后分别继续318/321指令，
停6016bff6读62221d80半字/返回60165665，或60163281读622211e2字节/返回601655f2。
当前两条fault严格固定，未进入6042805e，capture不变，population未续。新增2948
指令，最大观测深度1076非完整栈上界。下一步原厂62221d80及622211e2/dd初始化和
生命周期；勿把明示硬件输入当作相机测量。候选004未改/不可安装，无SHA/真机操作。

此前：[设备输入转换](CANDIDATE_DEVICE_STATE_SIM.md)已执行原厂2248B/562word早期数据
复制3379指令和8种三bit输入转换，共5027指令；600222a2读取三路GPIO bit4、
600226bb发布8ff00198，所有输入/控制word原样恢复；6011681d产生设备列0/1/2，
60022090前缀产生remap selector。复用旧flash_gpio研究，六个原厂remap count均0。
显式输入0分支下，60118093采样182指令后停60022085读取9b80108c/4B，logical102；
另一路60118545两指令停600668b4读98e00058/4B，两处shadow均未发布。早期157指令
缺6203c794的报告保留。两个OR字节依赖已定位BSS清零，其他输入/时序未伪造。
原几何栈及capture不变，未续geometry/population，候选仍004/不可安装。下一步在
明确硬件输入模型下执行采样/谓词和配置；实机输入/外设时序/完整启动继续待证。

此前：[几何服务与配置构造](CANDIDATE_GEOMETRY_SIM.md)已执行原厂service5217、controller
reset前缀18、task前缀131、mode snapshot397、请求字段15+10、设备缓存4336条指令。
147个service属性槽及117行设备缓存全部匹配已注册属性bank；后者复用启动data-copy
来源60233034→61f9ad74，仅936B有条件映射，NAND/cache未执行。mode3由原厂调用点
产生，三份24B快照来自ROM fallback60533564。请求controller inputs仍为明确fixture，
完整handler/任务时序未执行。配置6042760c推进1920指令停601168ee读a272bcde，
查询1215/返回601654dc，尚未进入6042805e动态setter；capture不变，population未续接。
四个中间frontier报告保留；当前脚本严格固定预期fault。下一步601168ba/6011681d
设备状态初始化及8ff00198/设备表来源。不要直接补零或把reset尺寸用作拍摄值。
候选仍004/不可安装，无重编译/SHA/相机操作；S3未整体完成。

此前：[原厂模板复制与population](CANDIDATE_POPULATION_SIM.md)已通过copy并定位动态状态
停止点，候选仍004。新增capture配置ROM60096f98..600be008共1084条，经同一原厂
packer581230指令打包到624ea400/153008字节，再64545指令注册；总2293条不同索引。
真实CALL602a7ea0[f0],20执行prewrite一次及6833word复制，49697指令到602a7eb0，
27332B与模板一致。真实resume2429指令/40次getter后，604288d5读未映射622a064a
半字停止，MDR602a8315，目标capture+24178/+24180；最后property c36a。
原厂reset6042133f..364和动态setter6042844e..481已定位，后者读配置A2+48/+50。
不要用猜测拍摄值/零值越过。当前capture填充未通过，无sample/seal/worker后续运行；
下一步追溯配置对象和状态更新，再继续population/relay。新探针返回明确frontier，
不是完整成功；先前缺810a的35指令诊断报告独立保留。无重编译/SHA/相机操作。

此前：[原生属性与capture模板](CANDIDATE_PROPERTY_SIM.md)通过有条件初始化，候选仍004。
四组原厂ROM/default经真实清表、复制、按类型打包和注册，共1209条不同索引记录；
12段297381指令，6030002c模板初始化7908指令正常返回，16次getter查询与三个常量
正确。缺c082/8f11的两个中间报告和A5诊断报告独立保留。A5揭示initializer只写部分
字段；正常输入显式依赖原厂第二组BSS范围621caf00..62796888已清零，DMA本身未执行。
无NVM导入/校准声明，无自动补未知属性。native_call支持真实100000条trace分段resume，
完整保留153300条打包调用。当前capture仍只读/未改变；下一步60300055真实模板复制、
population/relay预处理，再推进worker分配/处理/撤销/ACK，S3未整体完成。

此前：[下游queue与worker领取](CANDIDATE_RELAY_SIM.md)通过，候选仍004；新探针
`ep7_candidate_relay_sim.py`12段50,621指令。4c/ab/4f在S2发布前原生初始化，
603ef864真实注册4c/4d→flag58；4c发送执行通知/flag-set，ab/4f在600515c2真实
读到未注册hook0并跳过通知。三次raw receive各返回312，descriptor全字节不变，
每次发送清除本地票据、接收清空队列。原厂worker CALL进入wrapper领取初始COLOR2
H0=5/L0=−3，停603f2800；旧有效E7T1票据重放后scope全零，首次scope状态1。
最大新增观测深度884，完整栈未知。`descriptor_context`返回materialized现场，
message_context支持额外发布前回调；旧CLI兼容，上游saved report各项不变。
接收后手动选择后续调用片段，不执行dual603efb6d/kind19 603f04b9预处理及worker
603f28da preflight；任务TCB/栈handover和preflight成功分支D0=0是明确fixture。
下一步关闭这些间隔并推进原厂job分配/构造/CPU/撤销/ACK。capture目前只读24084B，
较高偏移写入需真实布局依据，不得自动扩展补零。固件未重建/无SHA，S3未整体完成。

随后为capture预处理找到真实模板来源：population602a7ea9→60300055从6225882c
复制6833word/27332B，原始capture池槽41984B。模板由6030002c→60301170初始化，
不是静态ROM块。新`ep7_candidate_capture_template_sim.py`在克隆现场/新栈、A5有界
模板上执行2367指令后停6005d924，读取未映射a26ffa84半字；property key2b41、
native return6005e94d。report `candidate-capture-template-frontier.json`明确
template_initialization_passed=false，原capture逐字节不变，半成品未复制。最大深度
460，仅43字节偏离A5。下一步原生属性服务初始化/来源：6005d924按flag查override
a2707a88，再base a26ffa88，每行8B、key>>4、+4descriptor；6005d8e3初始化override，
6005d914清override状态，不能用零flag/零表跳过base数据。无固件bug或完成声明。

此前：[原厂descriptor填充与MULQIU修正](CANDIDATE_DESCRIPTOR_SIM.md)通过，候选仍004。
GNU旧模型udfu01 imm8/imm16误符号扩展；class1乘216变−40，7397指令后在603e050b
向未映射a26a07e8写入，未补错误映射。松下手册page70及GNU自身注释要求零扩展。
新增独立`mn103_mulqu_unsigned.patch`两行，ep7_build_sim追加`--unsigned-multiply-fix`
可在现有build约8秒增量更新，保留旧binary，后续用
`/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu`。6条单指令前后证据
保留；原厂materializer7413指令返回603dfb7d/D0=1，SP190105b8，同一票据及metadata
身份/ID1/capture正确，a26a08e4原生初始化0/1。locale48B与formatter pointer由原厂
初始化，trace mask0 fixture，真实logger/get_tid/formatter执行；没有成功stub。

`ep7_candidate_message_sim.message_context`现在返回report及包含machine/syms/descriptor/
received/wire/frozen的context；旧inspect结果不变。descriptor脚本在真实接收寄存器
处resume；METADATA19410000提供148B只读fixture（前2字12345678/55667788、+8ID1、
+72dispatch2001），不是原生metadata分配证明。最大新增深度300，完整栈仍未知。
下一步4c→ab→4f及worker，复用现有descriptor/worker/ACK frame研究；额外队列必须
在S2发布前初始化、原厂通知注册不能漏掉。固件004保持未变/不可安装，无SHA/真机。

此前：[queue4b 消息/通知/接收](CANDIDATE_MESSAGE_SIM.md)已进入候选004，源码0b874fa。
原厂接收函数真实入口60036c8e；旧绑定60036caf跳过destination/timeout保存与dispatch
检查，导致native−17/candidate−1并留队。004复用107对象，仅两个CALL重定位字节
600cb0a3/a4变化，布局及自有符号不变。修复后真实native返回28，command+票据完整
进入descriptor；空轮询native−50/candidate−2清除旧票据，其他输出/queue不变。
本节点6段16,931指令，上游冻结/FIFO119,948。最大观测调用深度640，非完整栈界。
后续用004；旧报告保留对应历史来源。没有重复编译或广泛测试，产物仍不可安装。

`ep7_candidate_message_sim.py`复用S2和capture helpers；prepare_kernel在冷清零/发布前
运行60030c4c初始化queue4b60B header及4864B独立backing。原厂6005134a初始化通知
表，603df7c9..7e0注册4b→flag203/bit1；实际named/raw send/60051078通知/60035a5e
flag-set各执行一次。flag对象6219e710依据ROM table/spec显式置为空等待链fixture，
不是任务唤醒证明。METADATA19410000仍未映射；materializer TCB切换和ancestor栈字为
fixture。下一步实际descriptor填充、下游queue和worker；不要把前300字节保持5A的
票据接收算成stock descriptor已构造。参考现有descriptor/worker frame研究与桥接。

用户补充：最后参考fishcu原项目方式封装；已写入FLASH_READINESS_PLAN。优先复用
`patches/hsl/pen-f/build.py`的parse→replace_payload→reconstruct和`oly_container`，
不用其SHA入口，不照搬PEN-F两组件输出/E122文件名/设备操作，保留E-P7自身型号与
未修改组件；封装检查不替代加载/所有权/恢复资格。

此前：[named-send gate修复](CANDIDATE_QUEUE_GATE_SIM.md)已进入候选003，源码296e721。
旧gate误用600514f1/60051555；实际两处DD CALL32返回600514f3/60051557。旧002在
maximum改变或I/O关闭时两分支共四次错误放行，003均原生返回−42且退出临界区/释放锁，
两次正常场景到复制前续接。仅重编译runtime/kernel_gate.c，106对象复用；整包链接
合成通过，26,214,336字节与002仅在600ca1fc/600ca204两个立即数字节不同，全符号
和布局不变。后续必须使用003；当前源码检查会拒绝旧002。旧S1/S2/S3报告保留历史来源，
本次没有重跑无关测试。下一步queue4b完整发送/通知/接收以及materializer/worker。
可在S2 bootstrap_context后、publish_runtime前用原厂60030c4c初始化queue4b已有
backing，补齐60字节header和环缓冲；避免把发布后的queue重建伪装成正常启动。
复用capture脚本已执行的冻结/FIFO输出。named包装600514b6必须保留60051078通知，
遇到未映射的通知表/root应按原厂初始化证据补齐，不能用零值跳过。

此前：[controller 与延迟 FIFO](CANDIDATE_CAPTURE_SIM.md)完成 S3 的第二个子节点。
23 段/208,056 指令：真实启动 helper copy 把6143ca00 经显式 resident alias
a143ca00 搬到47000800；实际 lookup6029b9d1、FIFO initializer/enqueue/pop 与
47001052 copy helper均执行。patched population prewrite、sample/finish冻结正确；
原生 pop 将32字节冻结 scope交给caller，重填后保持原FIFO顺序但scope全零；过早
copyout永不中途重采样，free后取消node映射仍不读旧node。TCB显式切到ID73/4096栈，
owner/state/pool/registry/capture与两层ancestor返回字是fixture，原厂完整population
和外层controller service未执行。最大观测深度368。下一步queue4b消息/通知及
materializer/worker；复用helper搬运和S2发布，不能跳过真实post-send通知。

此前：[H/L 状态与参数模拟](CANDIDATE_STATE_SIM.md)完成 S3 的首个子节点。复用 S2
实际发布的 runtime，13 次候选调用/13,672 指令：COLOR3 修改/冻结与 COLOR2 隔离、
后续编辑不影响旧快照、原生 poll busy −50 无修改/不 poison，最终 observer 的
20 个系数写入正确；真实撤销后将 job 取消映射，再调用不读旧 job且输出不变。
GCC CALL [],0 的第三参数在 caller SP+12，不能写成 SP+8。job 是既有 direct-reader
schema fixture，尚未执行真实 constructor/worker。下一步 controller adapter 和
消息/worker 原生连接；不要重跑完整主机测试或手写另一个已发布 runtime。

此前：[原生创建与发布模拟](CANDIDATE_PUBLISH_SIM.md)已完成 S2 的有条件场景。
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
