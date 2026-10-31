# 原生 capture source、登记与释放候选接合

## 已实现

后续 [捕获事务与三组接合](CAPTURE_TRANSACTION_GUARD.md) 已扩展实际调用检查，加入
新增C访问期间的busy保护和非返回的销毁失败处理；下文初次56对象结果保留为历史证据，
当前结果为57对象。其他原生别名/释放闭包依然须单独证明。

`controller_sidecar/native_binding.c` 定义实际 source provider
`ep7q_capture_snapshot_unresolved`，以及共享 sidecar 存储、初始化、state观察、fresh登记、
两阶段population、node free、capture pool release observer。历史名字中的`unresolved`
保留兼容，但在本次56对象pipeline中已成为定义；剩余32个外部符号全是原厂地址。
这消除了源接口空缺，没有自动证明所有原生存活/排他条件，也没有安装补丁。

|候选hook|位置|保留的原厂调用或续接|
|---|---|---|
|初始化inline|602897d7|重放实际state=0写入，续接602897dd|
|state service|60289c5e、60289d02|复用原桥；先调用6028a882，正常返回后观察|
|fresh返回登记|602a31c7、602a440a、602a4480|602a3116，[d2,a2],28；原A0 node返回给原调用者|
|sample|602a31ea、602a442c、602a44a3|602a7ea0，[d2,d3,a2,a3],20；正常返回后使用原caller A2=node|
|finish|602a31f7、602a443e、602a44b5|602a8dbd，[d2,d3,a2,a3],48；相同node完成确认|
|node free|既有清单13处|observer后尾转60022732，原A0和[],4帧不变|
|capture pool release|6029be5d|observer后尾转603db89e，原pool handle和[],4帧不变|

## 真实对象与取值

fresh allocator正常返回时，node的56字节prefix已初始化且尚未入队；读取其ID和associated
标签，以原厂getter6029b9d1获得当前实际capture地址，登记token及reserved ID/capture。
不扩大node/metadata，不读取未经申请的尾部，不要求此时尚未写入的associated+8 backlink。
原厂getter原生结果在A0，call frame24；专门的GCC桥保留这个指针返回约定。

后续sample/finish和source copy都先在独立存活契约下resolve/authorize，再读node prefix。
raw mode/selector分别读取实际capture+24053/+24083。两阶段之间更换ID、地址或profile会
失去资格。c3de的associated由该原厂调用持有；source核对associated+8=node、node+8关联、
associated ID及传入capture ID，然后只复制已封存的值。失败前缀也会消耗提前copy的机会，
不允许将未完成记录晚补成有效snapshot。

pool release处A2是原厂实际registry row，+12是当前已分配capture指针，+16是pool handle。
observer在释放+16前按+12撤销reservations，覆盖未sample、已sample和已sealed记录。
同一capture下的登记全部撤销，其他capture不受影响；后续同址重用需要新token。
不根据UDF索引指令自行计算ID，不把释放后仍留在row+12的旧值当作新分配证据。
已复制进producer scope/transport的独立快照不随源释放删除。

## 上下文与关闭行为

使用已发布runtime的实际current-TCB查询，要求domain0/controller entry60289852。
首次有效调用保留其TCB、ID和stack视图；变化或未知非销毁上下文永久关闭新的capture接合。
外部非销毁上下文只设置atomic关闭标志，不并发清理controller-owned sidecar；销毁或
state observer上下文失配则隔离，不能返回原厂继续释放。新增C访问有busy保护，并核对
25处实际CALL。初始化只允许第一次native state=0；重复初始化隔离，不重置旧sidecar或token。
settings采样复用同一个worker/reader core，原state service callback改用这个具体绑定。

这些检查不证明task generation、不禁止中断，也不能补救未接合路径的并发free。
安装前仍须证明该controller区间、异步别名、重入与任务/捕获存活；不以“同entry”代替锁。
G6必须先建立zeroed storage及全部hooks，然后在controller开始使用前完成初始化/发布顺序。
运行时发生restart后没有重新启用协议。

## 验证

- [当前原厂证据](../../research/ep7/capture-native-binding-current.json)：118条指令、任务行、
  三个完整callee body的直接SP访问检查。fresh仅+4/+8/+12/+16；population无直接SP操作；
  postpopulation仅+4..+28。没有直接incoming-stack参数证据；不能替代所有被调函数的审查。
- [主机结果](../../research/ep7/capture-native-binding-host.json)：strict、ASan/UBSan通过，
  检查unsampled/sample/sealed在pool release前撤销、其他capture保留、同址重用旧token失效、
  reserved capture不被后来的prefix覆盖。native读内存/调用仍未在主机执行。
- [集成链](../../research/ep7/capture-native-binding-integration-host.json)：更新后的sidecar
  继续通过strict与ASan/UBSan的16-job处理；native API仍由fixture提供。
- [目标对象结果](../../research/ep7/capture-native-binding-target.json)：56对象通过；新桥123条
  指令、13个relocation按顺序核对，复用state桥17条指令重新检查。整个选定pipeline没有
  LIR/LAR/扩展寄存器依赖；没有链接或目标执行。

native binding文本1159字节、BSS656字节；新桥325字节。observer自有40字节，getter桥16，
原厂嵌套帧28/20/48另计；完整controller栈预算尚未完成。现有短CALL不能直接扩成7字节
覆盖相邻指令，G6仍须给出合格近跳trampoline或完整重定位方案。这些桥不是可直接写入的补丁。

## 下一准入条件

优先核实controller与异步node别名的排他、其他capture retirement/repopulation入口及全部
支持的释放闭包，然后落实G4原生UI资源和G6 placement/installer/完整stack预算。
当前绑定登记31c7/440a/4480三条同形fresh路线，其他分配/填充路线保持未资格化；
state33出入清除规则保持，最新具体边界见[后续记录](CAPTURE_TRANSACTION_GUARD.md)。
没有将限定子集扩称所有连拍、影片或回放已支持。整体固件构建、升级打包及相机操作未开始。
