# 消息流水线安装组与遗漏短CALL补齐

2026-10-31。汇合实际安装清单时发现：此前“已列28处短CALL”没有纳入消息流水线的
8处已知CALL。它们不是新功能入口，而是早已有适配器、尚未安排远距承载的入口。
本批复用同一30字节宏补齐，当前已归档36座短CALL桥；没有声称穷尽全部安装入口。

## 这8处原厂CALL

|作用|地址|原目标|mask / frame|
|---|---|---|---|
|立即producer scope|602ac3de|602ac748|b0 / 32|
|双队列接收|603ef8b5、603ef8d2、603ef8fd、603ef91a|603eeb57|f0 / 44|
|worker scope|603f2722|603f2800|30 / 56|
|正常ACK、drain ACK|603dfc67、603e05c6|603df97d|30 / 32|

全部保持原5字节站点、原返回PC、MDR和保存帧；桥会真实建帧并进入已有adapter。
原来的caller-stack资格继续使用原返回地址，例如602ac3e3、603ef8ba、603f2727。
worker ACK在603f2769本来就是7字节CALL，不额外添加远桥。
[生产桥表](../../prototypes/ep7_volatile_hl/snapshot_transport/native/far_calls.s)为8×30=240字节，
暂用栈开销沿用4字节；没有重写桥算法或修改原有16处adapter职责。

## 一组核对调用、存储与队列配置

新增[cohort函数](../../prototypes/ep7_volatile_hl/snapshot_transport/native/cohort.c)读取实际
已驻留指令/配置，要求以下31项全部匹配：

- 16个pipeline CALL：8处JMP32必须指向各自已知桥，8处CALL32必须指向指定adapter，
  保存组和frame逐项一致。不得跟随任意跳转地址读取“看起来像桥”的内存。
- [五个descriptor帧](DESCRIPTOR_FRAME_PLAN.md)的9条栈调整：各增加12字节，
  command/drain两层的同时存活责任保留；双队列relay没有虚构epilogue。
- queue4c/ab/4f配置的6个字段：maximum312、ring10112。命令4b和备用4d保持既有配置；
  实际运行时对象/attributes/backing仍由原runtime发布检查负责。

调用、帧调整和容量字段的字节区间互不重叠。cohort检查只返回布尔值，没有patch、
分配、发布或锁操作。必须先保证这些指令/表已经加载，才可调用它。
**它尚未接入完整冷启动发布回调**；后续installer必须将它与capture初始化、kernel三处
gate、UI表项、CPU reader、RAM/代码放置及存活证据一起作为发布前条件。仅此函数为true，
不表示整个安装组已合格，也不表示可以边运行边安装这些修改。

## 本批最小检查

[脚本](../../tools/ep7_pipeline_cohort_check.py)复用原producer、receiver、sender、worker、ACK
探针的指令定义及原五帧计划，核对当前输入的16个完整CALL、9条原栈调整和6个原容量字段。
这些旧工具的固件/SHA入口均未运行。检查器将实际cohort行顺序、8座桥的原返回地址和
目标重定位相互比较；新依赖均存在于此前pipeline对象定义中。

[报告](../../research/ep7/pipeline-installation-cohort.json)记录：

- 只新增编译两个目标对象：cohort text647、局部栈44；桥表text240；均无data/BSS。
  已加入日后pipeline目标检查清单，本批未为此重编整个pipeline/UI对象集合。
- 单个严格host夹具接受完整合成安装组；逐项损坏16个CALL、8个桥返回地址、9条帧调整、
  6个容量字段均被拒绝。合成页面不可执行，没有复制或运行原厂代码。
- 原GNU指令体检查器扩展到14种tuple，RET/RETF共28条返回路径与28个负控制通过。
  这是指令函数体对照，不是完整libsim、硬件中断或相机执行。
- [预算](../../research/ep7/prebuild-storage-budget.json)复用已有尺寸并计入前一批53字节
  清零桥，104个实现源text45,733、data0、BSS2,376。只新编一个类型尺寸探针；
  core/bootstrap/runtime5,704，静态存储粗计仍8,080，16 KiB内粗余8,304。

没有SHA、生命周期全集回归、固件改写或整体固件构建。代码容量65,280字节减上述text后
粗余19,547，但两个代码区仍未资格化，且尚须计入installer、节对齐和全栈。
下一项汇总剩余inline/table修改，落实原生bootstrap调用与完整发布检查，同时继续
启动前缀加载、保留区所有权及生命周期余项；G8仍未通过。

## 同批有限加载线索核查

另对五个原厂组件只搜索了启动入口/flash基址/保留槽与守卫相关常数字面量；未找到可
证明启动前缀加载者的新路径。`a1bd6d40`的main命中600227c0实际属于600227be的
非缓存释放范围上界，不是守卫初始化。010e中的Luke任务字符串也不能把该组件认定为
主CPU复位加载器。这些是有限检索结果，不是“加载者不存在”的证明，没有新增硬件结论。
