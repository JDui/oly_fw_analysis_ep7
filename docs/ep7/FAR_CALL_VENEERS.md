# 五字节调用点的远跳桥

2026-10-31。G6 已选定并实现捕获侧的短调用方案：原位5字节改为 JMP32，跳到
自有30字节桥，桥构造原 CALL 帧并进入已有 adapter。18处捕获短调用不再要求
adapter 落入原16位距离交集。没有改写固件，也没有据此批准任何代码区域。

后续[UI与CPU接合](REMAINING_FAR_CALLS.md)已复用同一宏完成其余10处候选短调用，
并把语义对照扩展到10种tuple/20条返回路径。下文保留捕获节点的原始9种tuple结果。

## 用原 CALL 建帧，恢复原返回位置

若原位 CALL 位于P、进入后的SP应为W，原厂返回地址应为P+5，位于W+frame。
仅跳到普通 C 函数、或仅调用远处 adapter 再跳回，都会破坏现有返回PC/栈来源检查。

[宏](../../prototypes/ep7_volatile_hl/target/far_call.inc)采用以下固定顺序：

1. 真实 CD CALL 跳到其下一条指令，使用原来的 register mask 和 frame。
2. 临时在W之下再留4字节，保存D0；把P+5同时写入原返回槽及MDR。
3. 恢复D0和SP，JMP32至已有 adapter。

这样在 adapter 入口处，原帧、已保存寄存器、参数位置、返回PC与MDR均与直接 CALL
一致。自有桥暂用的4字节位于W-4，必须加入完整栈预算。宏限制为d2/d3/a2/a3的保存位、
4字节对齐且不超过248字节的frame，并拒绝小于寄存器保存区的frame。

依据是[GNU MN103 指令定义](https://gnu.googlesource.com/binutils-gdb/+/cbe950e9fe8a56f788bcf985cc51733f18abb45b/sim/mn10300/mn10300.igen)：
CALL写栈返回槽及MDR，RET从栈取返回地址，RETF从MDR取返回地址；ADD立即数到SP以及
使用的MOV不改PSW。还核对了本地GCC13.4的mn10300.md中SP调整不改flags的说明。
这里依赖的是已审查的base MN103语义，没有把其他型号扩展位或自定义UDF加入模型。

## 捕获侧18处与实际cohort一起接合

[生产桥表](../../prototypes/ep7_volatile_hl/controller_sidecar/far_calls.s)和
[cohort](../../prototypes/ep7_volatile_hl/controller_sidecar/cohort.c)使用同一短调用顺序：

|已有 adapter 组|桥数|
|---|---:|
|engine configure / engine pool|2 / 1|
|waiting service scope|3|
|associated pool reset|1|
|fresh / sample / finish|3 / 3 / 3|
|state service|2|

总计18×30=540字节。其余21处原7字节CALL保留直接目标检查。
每个短调用现在要求实际站点为JMP32、指向对应的自有桥；
[通用字节检查器](../../prototypes/ep7_volatile_hl/target/far_call.c)还逐项检查桥的
CALL tuple、原返回PC、MDR恢复指令、SP恢复及最终adapter目标。

检查器只访问链接时已知的桥地址，不跟随站点中任意读出的跳转地址。入口仍要求
这些代码和表已驻留；cohort成功不替代冷安装顺序或代码不可变性。错误/缺失的任一桥
会拒绝捕获资格，而不是把不完整安装当作可接受的另一种编码。

桥表禁止插入对齐空洞。最后链接不能启用未经审核的relax来缩短桥中的跳转，
installer须再次核对最终ELF里的每项30字节、540字节总量和全部重定位目标。
当前对象检查已经逐项核对18个原PC、保存帧及实际adapter符号重定位。

## 只验证这个新边界

[检查器](../../tools/ep7_far_call_check.py)复用GNU文件中的9个指令C函数体，不重写它们
的寄存器/栈语义。来源文件仅下载至被忽略的generated目录；主站连接失败后从
[RTEMS的GNU镜像同修订](https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/cbe950e9fe8a56f788bcf985cc51733f18abb45b/sim/mn10300/mn10300.igen)
取得。脚本不联网、不计算SHA；第三方源文件和临时生成的函数体没有提交。

本次在小型主机harness中执行这些函数体，输入只有自写桥和合成寄存器/栈：

- 覆盖捕获侧8种实际save/frame组合，另加CPU COLOR的f0/96组合。
- 进入adapter前比较全部32个寄存器和原栈区域；只允许W-4那一个临时word有差异。
- 各做RET与RETF返回对照，共18条返回路径；检查SP、返回PC和保存寄存器恢复。
- 分别省略MDR修复、栈返回槽修复，18个负控制均能暴露失配。
- 通用cohort检查器通过1个正例、6个有针对性的错误编码/ABI/目标反例。

[语义报告](../../research/ep7/far-call-semantics.json)记录上述范围。这不是完整libsim
运行，不包括中断插入、cache/MMIO、真实E-P7处理函数或相机执行。
自写合成fixture曾汇编、链接以取得真实编码；它不是整体固件候选。

[目标对象报告](../../research/ep7/capture-far-call-target.json)：61个pipeline对象通过，
自有符号闭合，剩余39个均为已有原厂外部符号。生产桥表540字节、通用检查器text434字节、
capture cohort text662字节；相对上一版共增加text1,011字节，无新增BSS。
cohort和通用检查器局部栈分别48/20字节，不能把它们和桥暂用4字节机械相加就称全栈上限。

只运行本边界的语义/字节检查及受影响pipeline对象检查，没有重跑捕获事务或UI全部host
测试。G6下一步将同一机制用于UI等剩余短调用，并资格化早期代码承载、完整冷安装、
链接对齐和全栈。G1/G2/G3的剩余生命周期关卡仍保留，G8没有放行。
