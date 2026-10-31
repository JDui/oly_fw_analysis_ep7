# E-P7 原生属性注册与 capture 模板初始化

2026-11-01。候选004的原厂模板初始化6030002c/60301170已正常返回。四组原厂
ROM/default记录共1209条，由原厂清表、复制、打包和注册函数建立索引；16次原生
属性查询完成后返回。模板中的三个32位常量和厂商字符串通过直接字节核对。
这关闭了此前未映射属性表的停止点，尚不是完整capture population或整机启动证明。

[执行脚本](../../tools/ep7_candidate_property_sim.py)及
[当前报告](../../research/ep7/candidate-property-sim.json)沿用已发布runtime和
materializer的严格模拟上下文，在独立栈上执行初始化。原capture的24084字节保持
不变；模板尚未复制给它。没有重编译或改写候选004，没有SHA、API成功stub或真机操作。

## 原厂数据和执行结果

|原厂片段|指令数|已核对结果|
|---|---:|---|
|6005dabf清索引 / 6005d914复位override|36,868 / 5|4096行只清数据指针；未注册行头保留A5，override标记和根清零|
|6005d987注册固定ROM|24,897|60078e2c..6008e9cc的449条记录及数据地址一致|
|6005daeb赋原厂bank指针|4|a2711a88/a2711a8c指向两组原厂ROM记录|
|6005e111复制默认bank / 原厂调用段注册|14,186 / 28,905|9416字节复制到624b6400，522条记录一致|
|6005e309打包配置默认值 / 6005d987注册|153,300 / 7,674|600921dc的125条记录按类型对齐打包到624da408，实际范围19145字节|
|6005db03创建首个配置对象|58|28字节槽由原厂分配器占用，ROM、RAM、容量绑定一致|
|6005e129生成factory默认记录 / 原厂调用段注册|17,367 / 6,209|113条记录、版本18、4924字节范围；输入A0=0明确无导入NVM数据|
|6030002c模板初始化|7,908|正常返回，16次查表，三个常量20192/29664/18912及厂商字符串一致|

共12段297,381条指令，最大新增观测调用深度460字节。所有1209条记录占不同索引行，
未注册行的指针仍为零。每条已注册记录的key、count、data pointer与原厂源数据核对；
两个复制bank及配置打包范围逐字节比较，未用hash替代。

153,300指令的打包调用超过引擎单次100,000条trace上限。共用native_call现在只在
instruction_limit停止时携完整寄存器和捕获内存继续，保留100,000+53,300两段完整
trace，并断言trace长度等于实际执行数；不是重新开始调用。其他调用默认预算不变。

实际模板查询的9个key为2b41、62f1、c082、6534、8f11、6551、00fd、00ed和d4f4。
2b41来自固定ROM的厂商字符串；c082来自原厂copied default；8f11来自配置默认字符串；
00fd/00ed来自factory默认记录。这些是原厂默认值，不是实机NVM、序列号或校准验收。

## 从停止点收敛到当前结果

原始[未注册表报告](../../research/ep7/candidate-capture-template-frontier.json)
在2b41查表时读取未映射a26ffa84停止。随后保留了两个真实中间报告：

- [仅449条ROM记录](../../research/ep7/candidate-property-rom-frontier.json)：执行3250条指令，到缺失c082的原厂诊断入口60061808。
- [再加入522条copied default](../../research/ep7/candidate-property-default-frontier.json)：执行4736条指令，到缺失8f11的同一诊断入口。

这些报告是当时探针版本的历史输出，schema与当前完整探针不完全相同；不能把它们的
未通过字段改写成通过。当前工具的--rom-only保留ROM-only停止点模式。

[A5模板诊断报告](../../research/ep7/candidate-property-poison-template.json)记录了
四组属性齐备后原厂初始化正常返回的结果。返回本身并不代表模板所有字段均被写入：
例如capture偏移5212、23938、24184、24222、24532和27285处仍依赖先前的内存状态。
因此A5诊断模板不能作为已填充capture的输入，不能靠整个函数返回就消除这些未知项。

## BSS与服务启动的显式条件

当前正常探针只把模板初值设为零，依据既有[RAM归属研究](RAM_OWNERSHIP_AND_BUDGET.md)：
原厂60020068/6002006e传入第二组清零范围621caf00..62796888，包含整个
6225882c..6225f2f0模板。探针核对这12字节原厂操作数，再执行实际初始化；并未运行
DMA清零，也未据此证明DMA完成。报告显式记录startup_DMA_executed=false。
--poison-template保留A5诊断模式，不能用于后续默认capture。

索引存储、首个空闲配置对象槽、上游kernel/runtime仍是有边界fixture。原厂trace
helper按显式bit2禁用条件执行，未模拟trace环或硬件timer。其他属性bank、override
激活、完整服务启动顺序、真实NVM导入和写回未执行；未知属性内存没有自动补零。

下一步执行60300055真实模板复制，并沿原厂population/预处理确定动态capture字段；
之后推进worker分配、处理、撤销和ACK。S3尚未整体完成，S4加载/所有权/完整栈及
恢复条件继续保留。最终更新容器仍按fishcu原项目流程封装，当前004仍不可安装。

## 复现

```sh
python3 /repo/tools/ep7_candidate_property_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

沿用已有离线Docker环境，repo和toolchain volume只读挂载。当前报告使用正常条件BSS
初值；历史A5报告单独保留，不把两种初值的结论混合。
