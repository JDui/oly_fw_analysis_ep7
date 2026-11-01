# E-P7 研究容器的原厂解码与局部校验

2026-11-01。[五组件研究容器](CANDIDATE_PACKAGE.md)已通过E-P7原厂局部完整性检查。
实际main含header/trailer共26,214,400字节，原厂60c95a43调用600fa454，完整遍历后
返回0；读取终点21900000与显式buffer20000000加组件大小一致。此结果不替代完整
更新器的型号、版本、入口策略或写入/恢复验证。

[探针](../../tools/ep7_candidate_package_sim.py)与
[报告](../../research/ep7/candidate-package-native-sim.json)复用现有严格GNU引擎。
机器码取自实际研究包的main；输入只读，无API成功stub、SHA、固件文件修改或相机操作。

|定向场景|原厂执行结果|指令数|
|---|---|---:|
|完整010e组件原厂解码|262,144字节组件，payload与主机解码逐字节相同，头尾不变|1,228,520|
|完整修改后main局部校验|返回0，完整读取组件，调用者SP和保存寄存器恢复|39,321,696|
|main头尾第一个word不一致|返回3202，在加和循环前拒绝|30|
|010e首个payload字节翻转，保留旧校验|实际加和为1，进入6002266d错误日志入口|393,312|

共40,943,558条指令。针对共同校验失败分支使用较小的真实010e组件，避免再重复
26MB循环。错误日志入口前停止；日志函数及后续3211返回后缀没有被stub或冒称已执行。
原厂decoder只完整执行010e组件；main以主机解码后的完整组件输入原厂checker，
没有声称原厂完整decoder也遍历了整个main。

## 执行前提和保留的问题

原厂wrapper60c971a5/60c971b9实际是5字节CD CALL，tuple分别f0/28、f0/20；探针核对
原始字节，并使用同tuple的远距合成调用。控制对象仅明确提供+4的buffer指针和+16
的普通封装模式1，其余字节为A5。代码、栈和输入buffer是显式驻留模型，不运行文件
发现、分配、版本策略、flash控制器、写入分发、整机启动或恢复路径。

探针首次把两处原厂CALL误写成7字节DD witness，核对原字节后纠正，未改固件。
第一次完整main循环因单进程45秒工具超时终止，不能算失败固件或通过结果；随后
仅为这个完整循环放宽执行超时至180秒，实际返回成功。未重编译或改动CPU模型。

S5的主机封装与原厂局部完整性两个子项已通过。S3的几何/capture/worker链、S4
加载和所有权、完整更新器接受性、独立恢复和真机验收继续保留。

## 复现

```sh
python3 /repo/tools/ep7_candidate_package_sim.py \
  --package /repo/generated/ep7/research-packages/candidate-004/EP7HSL-NONINSTALLABLE.research.oly \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

此项已通过，代码/容器未变时无需重复完整加和循环。
