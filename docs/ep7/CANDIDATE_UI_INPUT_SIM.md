# E-P7 最终拨轮跳板与 GUI 输入作用域

2026-11-01。候选004的五处拨轮JMP、实际原厂预处理和分发包装完成目标机器码检查。
7个定向场景共执行75,479条指令，含显式边界返回指令；没有重新编译固件或运行
未改变的host测试全集。成功输入保留完整计数，超限和服务失败不留下可用编辑作用域。

## 实际运行的链

从原主循环CALL60cfd53a进入已链接preprocess桥，再进入完整原厂60e9fa88。
其hash分流、五个逻辑拨轮handler、事件/方向归一、原count setter60ea3b2c、
候选sample及prepare_end均执行。各handler由真实CALLS调用显式轮值服务模型，
给出有符号halfword计数和状态；日志输出也使用返回模型。

|原事件|服务selector|实际JMP/续接|输入计数|输出事件/参数|
|---|---:|---|---:|---|
|9031|1|60ea0070 / 75|7|9031 / 2|
|9032|0|60ea00f7 / fc|−4|9032 / −1|
|904f|2|60ea0d70 / 75|7|9031 / 2|
|9051|4|60ea0deb / f0|7|9031 / 2|
|9050|3|60ea0e66 / 6b|7|9032 / 1|

每处进入JMP前和返回原续接后对比D0..D3、A0..A3、SP；全部保持，MDR恢复为原返回PC。
原全局halfword和候选私有delta均保留7或−4，没有改用表中的方向/缩小参数。
五处完整30B远跳及cohort取自实际候选，未临时补装测试跳板。

原预处理完成后，从原CALL60cfd558执行dispatch桥。真实event/parameter/extra/machine
传给原engine入口60d1144d，同时候选phase由pending进入dispatch。这里截停engine
body并返回明确的四寄存器结果；桥保留其D0/D1/A0/A1结果与原callee-saved状态，
最后清除作用域。没有把这个完成边界称为完整parent、widget或编辑链通过。

另两例直接针对风险：计数65虽仍经原厂归一和engine调用，却不取得候选编辑资格；
服务返回1时原预处理返回1，正常不进入engine。两者最终phase均为idle。

## 内存、任务与栈

私有BSS由实际候选冷清零桥初始化。原GUI构造器60cfceba明确请求entry60dd5067、
16KiB栈；探针使用显式domain0/动态ID254/TCB和同尺寸栈，原get_tid和候选任务查询
实际执行。没有模拟动态任务创建、调度器交接或并发所有权。

28B事件包位于原主循环约定的SP+396。非modal状态使用明确的零输入，其他modal
和filter分支没有因此取得资格。轮值服务对象及vtable是模型；它的物理输入生产者
未运行。该链最大观察栈深为主循环SP下716B，含嵌套224B原预处理和候选调用；
这不是GUI任务、renderer、原engine下游或IRQ的完整上界。

初次运行因探针的构造器witness抄录错误停止；修正为实际20字节后7例完整exit0。
固件004及fishcu研究包未改变，无SHA、联网或相机操作。

本节点关闭最终输入跳板/作用域的目标ABI与完整计数问题。GUI内容/owner显示与
COLOR门控、worker消费及驻留资格仍需各自证据，LCD/拨轮手感属于后续硬件验收。

[工具](../../tools/ep7_candidate_ui_input_sim.py) ·
[机器报告](../../research/ep7/candidate-ui-input-sim.json)。
