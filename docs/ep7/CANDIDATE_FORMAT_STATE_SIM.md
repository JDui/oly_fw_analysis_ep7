# E-P7 格式模块发布、模式字段与状态记录停止点

2026-11-01。[探针](../../tools/ep7_candidate_format_state_sim.py)实际执行格式模块的原厂
就绪发布helper，恢复原快照回调后进入就绪分支6065e658。48个属性缓存指针、6个
模式字段和一份10字节参数记录已由原厂代码产生；完整格式getter和快照回调尚未返回。

[报告](../../research/ep7/candidate-format-state-sim.json)覆盖原有两条GPIO输入分支，
新增10380条指令。当前两者严格停在606d673a读取a2788cec的halfword，MDR60664e1e，
即后续10字节状态记录的第一项。未知字段仍未映射，原几何构造和capture population
未恢复。候选004及fishcu研究容器未改，无SHA、重编译或相机操作。

## 已执行及核对

|原厂片段|每个分支指令数|范围与结果|
|---|---:|---|
|60556b1e..60556bb2|33|RAM重置前缀，ready置0并发布状态对象指针；停在诊断缓冲区分配之前|
|6065bff0..6065c01e|11|核心前缀的6处RAM写入，622bea84置1，执行原厂单指令606a46cf后停止|
|606bb540..606bb57f|45|原厂getter读取2af4属性，将完整24字节掩码复制到622c5430|
|606bbffc|2768|完整helper及其四个子调用返回，最后实际将a2788ca8置1；13个字符串复制逐字节通过|
|606d6bd9|1586|48个指针全部匹配已建立的原厂属性记录并保留在缓存中|
|606d47fc..606d4898|300|执行原始谓词和6次getter，按原厂store写入状态对象+5..+10|
|原快照producer resume|447|进入就绪后的格式getter，原生生成10字节参数记录，停在下一状态记录读取|

实际掩码值24字节全零，来自已注册的原厂默认属性；没有手动关闭日志。13个字符串
来自60719bfa..60719d3f的ROM，共325字节，仅各自含NUL的实际长度可写，未放开每个
48字节记录的整块空间。核心606a46cf本来就是RET，并非模拟器成功stub。

模式getter的实际key依次为8c61、c021、8de1、8551、6761、8481，6个输出字节当前
均为0。60693455随后从原厂查询结果写入a2788aa4..a2788aae，7处store的宽度、寄存器
值与最终10字节逐项核对；记录为00000000010001000000。这些是默认属性场景下的
软件结果，未认定为相机正在使用的格式或尺寸。

共新增706字节状态映射：496字节发布/掩码/字符串/参数记录、11字节核心状态、
192字节属性缓存、6字节模式字段和1字节有条件BSS初态。直接store共135处。
最大新增观测栈深580字节，不是完整任务栈上界。

## 生命周期边界

原厂调用点60190fd3和6019139a分别调用冷重置与就绪发布；6019138c还在发布之前
调用6065bff0完整核心初始化。本节点只执行该核心的前缀，后续初始化未全部接通。
因此“原厂ready写入已执行”不代表所有消费字段及完整启动顺序已经具备资格。

60556bb2后的6055761a会检查并分配两份16384字节诊断缓冲区。本次在此调用之前
停止，未提供假分配器或假指针，完整冷初始化尚未完成。606bb540只执行掩码复制
前缀，未声称执行其后续属性复制及日志设置。

606d47fc先检查状态对象+15的空闲字节。仅此1字节使用已定位原厂BSS清零与缓存/
非缓存地址别名一致的条件初态，允许原厂谓词执行；未手动指定查询结果。该刷新
在606d4898停止，后面的状态字段、属性服务和完整任务启动仍未执行。

快照原栈和寄存器只在上述初始化结束后恢复。原有queue receive/log切口、GPIO
输入模型、默认属性来源和上游条件继续保留；partial capture全27332字节不变。
S3完整处理链、S4驻留/所有权/多核缓存/完整栈及S5完整更新器/恢复尚未通过。

## 下一个依赖与历史证据

606d672d从a2788cac取得对象基址a2788cb0，读取+60开始的5个halfword。当前第一次
读取a2788cec即停止。原厂冷重置只为这类记录写入部分字段，例如+62为100；
不能据此把其余活动字段全部补零。606d4593包含+70到+60的原生5-halfword复制，
606d18bf附近还存在+80到+60的复制，后续应追源记录及实际更新顺序。

保留[就绪发布后的模式字段停止点](../../research/ep7/candidate-format-state-frontier.json)、
[模式字段后的核心状态停止点](../../research/ep7/candidate-format-mode-frontier.json)、
[核心前缀后的参数记录写入停止点](../../research/ep7/candidate-format-core-frontier.json)、
[参数记录写入后的状态读取停止点](../../research/ep7/candidate-format-record-frontier.json)。
当前正式报告增加精确frontier断言、48指针与7处参数store的核对，不重复容器大循环。

## 复现

```sh
python3 /repo/tools/ep7_candidate_format_state_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

预期native_module_publication_completed、format_parameter_record_produced为true，
snapshot_producer_completed和population_resumed为false，两个frontier读取a2788cec。
