# E-P7 下游队列传递与 worker 单次领取

2026-11-01。候选004中，同一份原厂 materializer 生成的312字节 descriptor 已经由
实际原厂队列4c→ab→4f复制并接收，worker wrapper 领取到原先冻结的 COLOR2 参数
（H0=5、L0=−3）。领取后重放原来的有效票据，第二次 scope 保持中性全零。
这是传输和领取子节点；三个任务的完整预处理、调度和 worker body 尚未执行。

[执行脚本](../../tools/ep7_candidate_relay_sim.py)和
[实际报告](../../research/ep7/candidate-relay-sim.json)复用此前实际启动、runtime发布、
controller冻结/FIFO、queue4b与materializer的执行结果，没有重新手写票据或发布状态。
`descriptor_context`新增返回现场的接口，`message_context`接受发布前准备回调；
原有CLI及默认报告保持兼容。此次上游materializer/message各项报告与已保存结果一致，
capture/FIFO仍为119,948条指令，没有重跑无关测试或编译固件。

## 原生执行与结果

|片段|指令数|结果|
|---|---:|---|
|4c/ab/4f初始化|各34|在S2发布前，原厂60030c4c初始化真实header结构及独立backing|
|4c/4d通知注册|63|原厂603ef864注册两队列到flag58/bit1|
|4c发送/接收|9,147 / 6,190|312字节完整往返，flag58由0变1|
|ab发送/接收|8,675 / 6,307|312字节完整往返，原厂通知表查询值为0|
|4f发送/接收|8,665 / 6,319|312字节完整往返，原厂通知表查询值为0|
|worker首次领取|2,664|scope状态1，25字节快照与最初冻结值相同|
|已领取票据重放|2,489|scope状态0/48字节全零，没有第二份有效快照|

合计12段50,621条指令。每次发送都执行named wrapper和raw send，接收都执行修复后的
raw receive60036c8e并返回312。发送端12字节票据清零；队列记录长度312、占用316字节，
接收后计数归零、全部容量归还。跨三个队列的descriptor逐字节保持一致，三个接收缓冲
由原厂队列复制填充，探针不负责从上一阶段手工复制成功数据。

通知数组沿用此前6005134a的真实初始化结果，没有重新清零。4c/4d的原厂注册实际
执行；flag58对象由ROM pointer/spec确定，为明确的空等待链fixture。ab/4f没有在本
现场注册hook，named wrapper在600515c2读取到0并跳到600515d9，不调用60051078。
探针同时断言表查询执行次数和值，区分“执行原厂无hook分支”和“调用通知函数”。
没有据此声称真实系统不存在其他动态注册，亦未验证等待任务唤醒。

各任务ID、entry、priority、stack size均与原厂ROM配置行核对：21/603ef892/4752，
57/603ef94a/4096，6c/603f26a1/8192。TCB字段和有边界栈的交接仍是显式fixture，
没有模拟真实任务创建/切换。最大新增观测调用深度884字节，不是完整任务或IRQ栈界。

worker的实际603f2721..2722指令进入候选wrapper，原生CALL建立父frame，候选将
同一票据标为E7C1并从transport领取快照，停在原厂body入口603f2800。scope位于
19010798，状态1；scope快照不会受先前已改变的当前H/L值影响。负例从此状态克隆，
明确注入原来完整的有效descriptor（包括E7T1），再次执行同一wrapper；transport
拒绝已消费的票据，scope全零。不是只检查已改写的本地marker，也不是并发调度测试。

## 保留的未执行边界

该探针分别执行已经审查的发送/接收调用片段。中间dual预处理603efb6d、kind19
预处理603f04b9、外层router选择和worker preflight603f28da尚未执行；descriptor
跨这些明确间隔保持接收后的值。worker入场D0=0是preflight成功分支fixture，
不是preflight已经返回成功的证据。不得将本报告写成完整relay任务或S3整体通过。

下一步接入这些预处理、原厂job分配/构造、CPU/ISP处理、撤销和ACK。现有capture
fixture只覆盖controller实际读取的24,084字节且只读，预处理对更高偏移的写入需要
真实对象布局/来源依据；不能通过无边界扩展或把未知内存补零消除fault。
metadata/identity槽/idle flag/queue backing来源、代码驻留/RAM归属、多核和恢复条件
仍保留。最终封装继续参考fishcu原项目；当前004没有更新容器，仍不可安装。

## 复现

```sh
python3 /repo/tools/ep7_candidate_relay_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

沿用现有离线Docker只读挂载；无SHA校验、API成功stub、固件文件改写或相机操作。
