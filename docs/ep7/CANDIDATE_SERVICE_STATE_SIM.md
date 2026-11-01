# E-P7 原厂冷状态片段与几何快照停止点

2026-11-01。两条设备输入分支已接入有原厂代码来源的冷状态，分别继续3177/3454条
指令，均到达6041a5bb读取几何快照selector6229fc44。GPIO80=1分支还完整复制了
39个halfword的78字节原厂参数记录。动态setter和完整配置仍未执行。

[探针](../../tools/ep7_candidate_service_state_sim.py)与
[报告](../../research/ep7/candidate-service-state-sim.json)复用前一节点的真实寄存器
和栈。初始化片段独立执行；涉及外设的前置调用、完整服务/任务启动仍保留为条件。
候选004未改写，未重新编译、做SHA或操作相机。

## 已执行范围

|原厂代码|每个输入分支的指令数|范围与结果|
|---|---:|---|
|6016227a..60162367|160|RAM初始化后缀；到RET前停止，622211dd/e2等标志清零，5000/9500等原厂常量保留|
|60163bc8|799|完整诊断状态初始化，含768字节原厂memset|
|601696d3..601698bf|169|任务参数重置前缀，停在属性服务查询之前|
|601613f9|5|完整pending状态重置，62221040/44清零|
|60169011..60169018|2|原厂任务状态reset片段，将62221d80置0|
|原几何构造resume|3177 / 3454|两个输入均到达同一快照selector缺失处|

本节点合计8901条指令。最大新增观测调用深度1088字节，不是完整任务栈上界。
复用原有直接store解析器，提取为map_initializer_storage公共helper；仅110处已审查
store目标和有界数组可写，初值A5。加上下面的一个有条件BSS字节，合计1054字节。
这次复现也实际运行了原几何初始化的同一helper及全部上游断言。

60162162完整初始化在RAM后缀之前有60165f82/60165725/60165ff5调用，涉及外设时钟
和9b900000/4访问。本节点没有声称执行这些调用，也没有API成功stub。601696d3
前缀之后还会进入601f0120属性服务；60169011所在完整任务还包含前置helper和后续
queue注册。本次“冷状态”只是有来源的离线生命周期场景，不是活动拍摄状态已确认。

## 78字节记录与一个填充字节

原厂6016bc84返回62221998；601739dd设置-39循环计数，601739e0..601739e9以
halfword复制到调用者栈。源记录范围严格为62221998..622219e6。

执行参数前缀后，这78字节中恰有一个字节622219e1没有字段store：e0是byte字段，
e2开始是halfword字段。其余77字节均来自实际执行的原厂写入。原厂启动BSS范围
621caf00..62796888包含该字节，因此仅给它提供“该BSS清零已成功”的条件初值0；
未执行DMA，也未自动填入其他未映射地址。

严格引擎要求一次halfword访问落在同一显式region；探针将这份来源完整的78字节
记录合并为一个region，保留每个原生字段字节。最初记录报告时曾因Python端跨region
读取失败而退出，修正后实际执行通过。没有修改CPU模型来容忍未映射读取。

GPIO80=1分支实际执行39次原厂halfword写入，逐项核对源地址、连续目的地址和D0值
与初始化记录一致；GPIO80=0分支没有走这条复制分支。记录字节保留在当前报告。

## 边界与后续

[第一次接入状态](../../research/ep7/candidate-service-state-frontier.json)后，两个分支
分别在62221a14和62221040停止；[接入参数前缀后的报告](../../research/ep7/candidate-service-padding-frontier.json)
保留GPIO80=1读取填充字节时的严格fault。当前两条路径都停在6041a5bb读取
6229fc44，宽度1，MDR60419f58。脚本固定该fault，并拒绝诊断、quarantine或其他停止点。

新依赖是两份124字节几何快照的selector；6041a5bb按selector*124返回
6229fc48中的一份。6041a51c会读取旧快照并重设selector，6041a551负责轮换。
60419529设置部分指针/回调；6041a20a通过传入回调构造快照，不能把整份对象自动补零
当作活动配置。下一步追踪该原厂回调和请求来源，再推进6042760c的76字节配置对象。

partial capture全27332字节保持不变，原population栈保留，未触发completion/seal
或下游worker。S3仍未整体完成；真实外设效果、任务调度、NVM和加载/所有权继续待证。
最终封装仍按fishcu原项目流程处理E-P7自身型号与组件。

## 复现

```sh
python3 /repo/tools/ep7_candidate_service_state_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

预期两项geometry_configuration_passed均false，native_parameter_record_halfword_copies
分别为0/39，population_resumed=false，且两个frontier都指向6229fc44。
