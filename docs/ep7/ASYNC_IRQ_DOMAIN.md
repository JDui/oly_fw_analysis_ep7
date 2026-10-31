# type39 首阶段的 IRQ 执行入口

2026-10-31。接续[按指针异步输送](ASYNC_DISPATCH_LIFETIME.md)，本批关闭“第一层队列
由谁消费”的静态路径疑问。在原厂domain0配置成立时，该路径由class5/source29的
IRQ分派消费，不能视为controller任务内的普通函数回调。

## 从注册到实际消费

既有路径是type39→6010bf9f→6011209b，将工作函数60114980和原请求指针交给
600684c3。后者根据8050选择环形队列，发布后启用对应selector的source29并写触发字。

6006839d的初始化在600683dd装载consumer6006860a，以`source=29, class=5`
分别调用6006aa25注册selector0/1/2。该包装器把class与consumer组成两个word，
交给60054fce。后者按selector选择callback表，以`source*4`写入consumer：

|selector|callback表|发布与消费选择的队列|
|---:|---|---|
|0|a26ca7bc|6203be60|
|1|a26caa94|a27160b8|
|2|a26cad6c|a27169e8|

本批继续接通**domain0**的入口：root600411a4+184指向ROM类表6003c13c，
class5行6003c148为`{5,0,60054e0f}`。60032e39遍历这些12字节行，600331e4将
callback写入root+88的函数表621a6410。既有IRQ入口600386f8切换到IRQ栈后，
60038748按PSW类位选表，并在60038765间接调用对应handler。

class5 handler60054e0f的高源分支读取99200314，将其值右移2再减1作为source索引，
查a26ca7bc并调用。source29因此进入6006860a；后者读取8050、确认对应source，
按上表选择队列，并调用既有reader600686e2。reader从槽里取callback/request/参数，
在6006870a同步间接调用callback。本批没有把selector1/2的完整IRQ入口也列为已资格化。

## 一次必要的片段执行

复用现有严格GNU执行器。原厂class5 handler从60054e0f开始，以显式输入
`8a00=53`选择高源分支，`99200314=120`选择source29，callback表槽设置为已经
核对的6006860a，初始PSW=0500。执行18条原生指令后到达6006860a入口；
最后一条为60054e42的`calls (a0)`，PSW为0d00，栈写入位于其局部/调用帧内。

这同时核对60054e22在进入consumer之前将PSW的IE位置1。它不是完整关中断区间；
不能从这条路径单独排除其他优先级嵌套。没有模拟硬件中断投递或抢占，没有执行
consumer的清源操作、ring索引、自定义指令、type39 callback、最终返回或RTI。

## 对接入方案的约束

- 保留现有“controller冻结后按值输送”的方案；不在IRQ callback里新增sidecar或UI读取。
- 当60114980走直接完成分支时，原请求completion延续这个IRQ调用栈；它在状态为6时
  可进入另一个异步阶段，不能把第一阶段入口的结论推广到所有最终completion。
- type7的普通提交分支已定位到6011fa59→6011bb99工作记录排队；其消费者与其他
  分支仍需继续追踪。type7/type39的排他与取消汇合尚未闭合。
- 域选择相同与任务上下文相同是不同条件。注册/选择规则一致不能证明硬件已经投递，
  也不能代替对象存活、发布可见性或全回调互斥。

[探针](../../tools/ep7_async_irq_domain.py)复用既有异步与IRQ witness，核对92条精确
指令、3项配置数据，并完成上述一次执行；[报告](../../research/ep7/async-irq-domain.json)
保留执行边界。无SHA校验、固件改写、整包编译或相机操作。
