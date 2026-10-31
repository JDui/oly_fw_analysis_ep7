# TOP 出队触发链与 type7 完成时的对象借用

2026-10-31。接续[三字工作队列](TYPE7_WORK_QUEUE.md)。本批核对150条精确指令和
4项分派表；仅静态检查，不重复执行已验证的入队/出队，也不模拟分配器和调度器。
[探针](../../tools/ep7_type7_completion.py)、[结果](../../research/ep7/type7-completion.json)。

## 一条具体的出队触发链

这里的 lower、sensor、upper 是三张不同分派表的命名空间，数字不能互换：

|阶段|实际调用/数据边界|
|---|---|
|lower type92|6014dc5a 表601ca7e8 → 6014dfb8；以命令71调用6014e67c|
|sensor type71|6014e705 → 6013015a，表601ba774 → 601307b3 → 60137df6 → 60136337|
|条件下的 lower type85|621f4a7c所指对象的半字+4不等于3，返回的前置调用之后，601363c3设置85，601363d8调用6014dc5a|
|upper type135|lower表601ca7c8 → 6014def0；栈上构造168字节请求、kind135，6014df08调用601e77d8|
|TOP consumer|upper表601eccac → 601e78c4 → 601200aa；601200dd从TOP取三字记录|

这条链以原厂分配、初始化和相关callee正常返回为前提。状态+4等于3另走分支，
不能把上述type85路线当成每次调用必经；本批也不宣称穷尽所有type135/type149的来源。

6014e67c在分派sensor请求前调用6006a922(2)，保存返回状态，结束时调用6006a96b恢复。
其底层60054d9f条件地改写PSW的0x0700字段，保留其余位。它是已知的入口/退出包围，
不是所有嵌套callee均保持该阈值的证明，也不是所有IRQ、核或完成回调的互斥证明。
这条静态链尚未确定最外层type92调用者的任务身份。

## 新描述符仍借用原 engine

普通TOP mode2满足处理条件后，以0x8007调用60120d73；mode5使用0x18007。
60120d73分配并清零136字节的下层描述符，保存以下关系：

|字段|内容|
|---:|---|
|+8|engine+4的地址|
|+20|原engine指针|
|+24|完成函数601210ae|
|+28|type7/type139时为601211c0清理函数|

0x10000标志还会把engine+64改为60120cac，因此mode5不能直接沿用mode2的完成回调假设。
普通mode2在此处保留原engine+64。提交成功且0x8000置位的路线保留描述符；其他路线
经过释放或诊断。描述符分配成功和TOP记录出队都不延长engine/workrecord的存活。

601210ae从descriptor+20取回engine；非type6分支在完成时重新读取engine+64，
非空时以原engine为A0间接调用。它没有保存提交时的callback副本，也未携带H/L代际。
因此“队列已经保存指针”不能保证随后调用的是提交时的同一工作周期。

status0/14994还会先调用6014dc2d。其资源释放6014fb57的结果决定是否调用descriptor+28；
外层之后仍有描述符检查与清理分支。资源引用和分配器的完整契约尚未闭合，本批既不
把这些调用直接解释为安全销毁点，也不据此认定原厂存在use-after-free。

## 对 H/L 的影响

现有候选不在TOP consumer或这些engine回调内新增H/L查询。保持controller处封存、
按值传送的方案；不追加一个借用engine地址重新绑定当前快照的实现。

后续按[新增读取责任表](CAPTURE_READ_OBLIGATIONS.md)审查具体对象和区间。对原厂
engine的全局完成顺序，只追踪会释放、重用或改写这些新增读取对象的边；不能用
“回调通常先到”替代保护，也不要求证明所有无关原厂回调都互斥。G1/G2/G3和G6/G8
仍未关闭。无SHA、生产代码变更、固件改写、整体编译或相机执行。

复现：

```sh
python3 /repo/tools/ep7_type7_completion.py --decoded /repo/generated/ep7/full-input/main.decoded.bin --objdump /work/install/bin/mn10300-elf-objdump
```
