# E-P7 worker 实际分配、登记、撤销与 ACK

2026-11-01。候选004的worker改动链完成定向机器码检查：24,686条新增指令，23次
原生私有锁操作均使用ID133，其中一次人为争用输入返回−50，其余成功。观察最大
worker栈深860B。未重编译固件、修改fishcu研究包或执行SHA、相机操作。

## 执行与结果

复用生产132个静态信号量初始化及原create133/runtime发布。实际core edit/capture
生成COLOR1的H[0]=3、H[2]=−2、L[2]=−4；transport prepare/publish及wire encode生成
serial1的312B descriptor。该descriptor的交付和preflight成功为输入模型，不重跑
已有三个队列传递结果，也不直接改私有transport或worker scope。

从原603f2721进入已安装的worker veneer/wrapper，实际领取同一冻结快照，再进入
原603f2800控制流及原构造器603537eb。603537f3处实际allocator桥把15488扩为
15512；原60022700/class2分配器取得domain0首槽61bd6d40。此时原15488B仍为A5，
只有新增24B被候选清零，scope记录真实返回指针与请求长度。

原构造器后段及转换是明确完成模型：复用既有bounded decoder fixture填原15488B，
重定位三处self-pointer，保留新24B；不宣称原图像/metadata构造通过。随后实际
process桥验证原调用栈/descriptor+36与allocation一致，登记token1并复制冻结值。

原处理完成模型进入实际postbuilder调用点603b02d9，执行最终far veneer、原builder
调用包装和候选observer。原COLOR builder输出准备为模型，observer本身实际解码
已登记job，并只改976B输出中的三项halfword：

|轴/色区|偏移|系数|
|---|---:|---:|
|H第1区|706|−3000|
|H第3区|730|2000|
|L第3区|734|−150|

其余字节保持5A。原builder的四个不同volatile返回值也被候选桥完整保留。

## 清理争用与释放顺序

处理返回前用真实raw poll133持有一次信号量，给清理制造可控争用。第一次候选
release执行原poll并返回−50；job映射、scope token均保留，尚未进入原cleanup。
实际runtime progress检查和delay包装进入600313ef，要求一单位延迟。这里明确
模型另一个参与者通过真实signal133释放争用，再返回成功；没有模拟真实时钟或调度。

重试成功后，candidate job token先清零，才进入原603e6c8d及原60353cb7析构路径。
原60022732/free实际把bitmap清零、recycle count置1并回收槽0。立即撤去15512B
payload后原析构/worker继续返回，未发生再次读取。资源数组为空是原job完成模型
的条件，未证明非空原生图像资源的全部清理。

在603f2727检查完整worker wrapper返回ABI和status0；后续原task片段把D2改为
完成状态，不能要求整个片段保持D2。实际ACK桥先清除12B trailer并退休transport
entry，原603df97d再构造12B ACK消息。发送在603eeba4截获，检查status/identity/
metadata，保留2B不透明padding；opaque reply handle55是输入，未验证队列交付。
全部transport entry为空、serial仍1。再次执行同一postbuilder调用点时job已unmap，
输出保持完整5A，证明迟到observer未取得旧登记或读取释放的job。

## 其余边界与探针修正

task6c/entry603f26a1/8KiB栈与ROM行核对，任务交接仍为fixture。domain0 class2的
fresh counters/bitmap/recycle空间为显式输入；原分配/释放和active-kernel分支的
锁指令执行，但没有把该状态当成真实系统整池初始化或并发归属的证明。CPU2私有
RAM保留是另一问题，不能由domain0 job池结果代替。

原参数准备、conversion、process、postprocess、通知和原ACK queue出口使用明确
完成边界。原worker本体控制流、改动桥、原job析构与ACK构造执行；未重演旧ISP、
完整relay/preflight、metadata生产者或照片像素。860B含模型选定的256B处理调用帧，
不覆盖原处理/IRQ最坏栈。驻留、多核和恢复资格仍待证。

首次探索修正四个探针假设，均未改固件：GCC按值ticket实为invisible-reference；
allocator RET须读stack RA，不能用已被callee覆盖的MDR；tail-delegated process
按原b0/24 frame返回603f2897；整个task片段允许D2成为状态，同时单独检查wrapper
ABI。修正后CLI完整exit0，仅执行这一项含一次cleanup争用的场景。

[工具](../../tools/ep7_candidate_worker_job_sim.py) ·
[机器报告](../../research/ep7/candidate-worker-job-sim.json)。
