# E-P7 build1100：统一安装清单与目标符号

日期：2026-10-31。本节点将已有生产cohort、桥和原厂witness汇合为一份可消费清单。
**未生成补丁固件、链接脚本或安装器，G8仍未通过。**

## 当前清单

[生成器](../../tools/ep7_installation_manifest.py)从实际cohort和far-call宏读取安装目标，
复用既有原厂指令、表项和cold-bootstrap的完整inline字节。每项包含原厂字节、长度、
替换编码、目标符号、装载阶段和证据来源；尚未选定的代码地址不以假地址填入。
[报告](../../research/ep7/installation-manifest.json)共101项、546字节原厂跨度，互不重叠。

|修改类型|项数|
|---|---:|
|5字节短CALL改为JMP32，进入现有30字节veneer|36|
|保持7字节CALL32及原save/frame|32|
|UI函数指针表项|11|
|descriptor栈分配/恢复|9|
|三队列的最大消息/环容量字段|6|
|完整inline指令跨度改为JMP32及NOP后缀|5|
|domain2大池分配/释放上限32→31|2|

此处“完整”仅指**当前代码声明的安装组**，不是全部原生调用者、别名和生命周期闭包。
36座veneer必须与所在组同时驻留，不能把原5字节CALL直接拓宽覆盖下一条指令。

## 装载阶段发现

|阶段|项数|当前边界|
|---|---:|---|
|启动前缀|3|600201fe冷清零、600229b9分配上限、60022c28释放上限；上游装载路径未资格化|
|早期kernel复制|9|3处kernel inline与6个队列容量字段|
|第1段|1|Usr3 bootstrap CALL|
|第2段|66|capture、pipeline、CPU COLOR及9条栈调整|
|第6段|22|UI短/长CALL与函数指针表项|

当前原厂9行装载表和其分支选择表已逐字节对照。kernel复制及普通段的区间来自
[既有装载调查](../../tools/ep7_load_regions.py)，不是本次重新证明硬件映射或cache行为。
启动前缀3项的flash地址/复制目的地址明确留空：不能因为主组件解码坐标看似连续，就
把尚未证明的上游加载器套用普通段偏移。下一步须查明这3项如何在第一次使用前驻留。

UI第6段仍在自身入口做cohort检查，Usr3不能等待其尚未启动的后续初始化任务。
当前清单只描述离线输入中的改动方案，不增加开机后在线修补这些代码的路径。

## 目标对象与原厂绑定

[sources.txt](../../prototypes/ep7_volatile_hl/target/sources.txt)冻结107个生产实现源，
排除host fixture和两个ABI调用探针。本次用已有GCC13.4/binutils2.45统一编译一次，
只收集对象的符号、尺寸和每函数栈资料，没有整体链接或执行：

- 344个全局定义，无重复；84个安装目标/adapter符号全部存在。
- 109个外部依赖全部进入[唯一原厂绑定表](../../tools/ep7_native_bindings.py)。
- 108个条目有既有调查支持的原厂地址；`__ep7_private_uncached_start`仍未解析，
  仅记录a1dd4d00候选，不能导出为最终链接常量。
- 当前未链接text46,543、data0、BSS8,084，与上一份分批尺寸汇总相符。
  cold runtime5704及once标志4已计入；不可重复加预算。

绑定表区分函数、接续地址、指针变量地址、函数指针表项、只读资源和指令地址。
GCC使用的C外部符号带前导下划线，assembly native入口不带；例如
`_ep7_stock_gui_machine_unresolved=61fb2564`绑定的是**存放machine指针的单元**。
`ep7_stock_boot_next_copy_end_unresolved=6218d984`由assembly读取数据，不是可调用入口。

地址记录汇总既有研究，本次新验证的是101项原字节/装载表，以及107对象的实际符号闭包。
这不代表108个原厂地址的完整ABI、任务域、存活期重新通过，也不代表完成总栈上界。
对象报告保留当前`.su`资料，下一步直接复用，不重跑host全套或分组对象全集。

## 复现与后续

只读清单检查：

```text
python tools/ep7_installation_manifest.py --decoded generated/ep7/full-input/main.decoded.bin
```

已有隔离工具链内增加`--tool-prefix /work/install/bin/mn10300-elf-`可生成统一对象资料。
没有SHA检查，没有新的packer；后续容器处理仍复用已有olycontainer。

编译准入剩余的实质工作包括：启动前缀加载路径；代码/RAM归属与冷清零/第一次分配顺序；
实际native调用链和中断嵌套下的栈界；G1–G4仍未闭合的身份、释放、退出与GUI排他资格。
上述事项不能因“符号都有名字”或对象编译通过而跳过。
