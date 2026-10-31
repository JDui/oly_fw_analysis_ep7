# UI 与 CPU COLOR 的五字节远跳接合

2026-10-31。复用[捕获侧远跳桥](FAR_CALL_VENEERS.md)的30字节宏和完整字节检查器，
接入4处MVC重建、5处拨轮采样和1处CPU COLOR调用。当前候选已列出的28处短CALL
均有保持原5字节宽度、原返回PC/MDR和保存帧的方案。没有选择代码放置、改写原厂输入
或开始整体固件编译；本结论不声称已经穷尽尚未发现的hook。

后续[流水线安装组审查](PIPELINE_INSTALLATION_COHORT.md)发现上述清单漏了消息链的
8处已知短CALL，现已补齐；当前归档数为36，旧28项报告仍只代表当时那一批。

## 原厂站点与接合

|组|原厂CALL|保存组 / frame|桥表|
|---|---|---|---|
|MVC重建|60e261d4、60e26201、60e26226、60e269f0|f0 / 28|4×30=120字节|
|拨轮采样|60ea0070、60ea00f7、60ea0d70、60ea0deb、60ea0e66|00 / 0|5×30=150字节|
|CPU COLOR|603b02d9|f0 / 96|30字节|

原目标分别为60e266a9、60ea3b2c、603b0068。检查器对当前26214336字节解码main
逐项比较这10处完整5字节CALL，并核对桥表顺序、原返回地址和mask/frame。
这里只重验这些解码字节，没有重复原厂整包身份检查或计算SHA。

[MVC cohort](../../prototypes/ep7_volatile_hl/ui_mvc/cohort.c)和
[input cohort](../../prototypes/ep7_volatile_hl/ui_native/cohort.c)现在要求站点为JMP32，
只访问链接时已知、按30字节编号的桥，并核对桥表总长。原来的两个7字节主循环CALL、
各vtable/entry/exit检查保留。重建与拨轮adapter不再需要落入原signed16交集。
桥恢复原返回PC，所以现有拨轮来源和caller-frame资格无需改写成远桥返回地址。

新增[CPU cohort](../../prototypes/ep7_volatile_hl/target/postbuilder/cohort.c)，核对实际
603b02d9与对应已知桥。postbuilder observer在读取setup的request/output字段前调用
它；缺失、错误返回槽、错误MDR修复或错误adapter目标均拒绝。这个检查不产生原生
生命周期、代码驻留、排他或cache保证，仍需G6完整安装者调用/满足这些前置条件。

## 针对本次改动的检查

[报告](../../research/ep7/remaining-far-calls.json)记录strict与ASan/UBSan两种主机检查：

- 捕获侧复用实际39项cohort及旧fixture的第3场景，检查每处错误站点和坏帧时在读node
  前拒绝。修正旧fixture仍生成直接CD CALL的问题，其余49个生命周期场景未重跑。
- UI复用现有fixture初始化和实际MVC/input C；9处站点、9个原返回地址与两个错接桥
  情况均被拒绝。没有执行原生机器码或重跑UI生命周期/渲染全集。
- CPU实际cohort检查未安装、错误返回PC、MDR修复和最终目标；合成页面仅为可读写的
  非执行内存，未映射原厂代码。

主机夹具共用一个只生成数据的[字节构造器](../../prototypes/ep7_volatile_hl/target/far_call_fixture.h)，
其生产代码依赖也已同步到既有capture/MVC/content/viewer检查入口。

[GNU指令函数体对照](../../research/ep7/all-far-call-semantics.json)增加00/0后覆盖全部
10种实际tuple，RET/RETF共20条返回路径、20个省略修复的负控制通过。桥本身不变；
仍只在合成寄存器/栈执行GNU定义的指令函数体，不包含中断、UDF、MMIO或完整libsim。

[pipeline对象](../../research/ep7/pipeline-far-call-target.json)为63个、
[UI对象](../../research/ep7/ui-far-call-target.json)为54个，自有符号均闭合；剩余39/67个
分别为已有原厂外部符号。3张新增生产桥表共300字节，逐项核对真实汇编字节、尺寸、
目标重定位与cohort顺序。CPU observer编译器改用A2保留setup，检查器据实际输出更新，
并核对拒绝分支在首次setup读取之前；局部帧从28增至32，必须计入后续全栈。

最新[预算](RAM_OWNERSHIP_AND_BUDGET.md)复用这两份对象尺寸：101个实现源、未链接
text44,793字节、data0、BSS2,376字节。相对捕获远桥节点净增195字节text，额外桥由
UI检查器简化抵消部分体积；core/bootstrap/runtime合计后静态存储仍8,080字节。
这些总数未含链接对齐、installer、原生queue backing扩展或完整栈。

## 下一个门槛

G6接下来须资格化早期可执行承载、16KiB保留区的冷安装/清零、全部hook安装和
后续分段覆盖、可见性及总栈。最终链接禁止未经审核的relax，并再次核对包括后续流水线在内的全部桥
的精确30字节与真实重定位结果。G1/G2/G3生命周期和G4串行/旁路关卡仍保留，G8未准入。
