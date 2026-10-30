# 票据的具体存储：显式扩大五个描述符栈对象

2026-10-31。上一方案要求每次relay显式携带票据；现在已找到实际拥有300字节
descriptor的五个栈帧，可把对象扩大到312字节，保持原生字段偏移。这不是借用padding。
本文件是未应用的变更方案；没有修改原厂程序或产出固件。

[探针](../../tools/ep7_descriptor_frames.py)在当前输入核对53条指令、4个任务配置行，
并仅汇编9条自写的新栈调整指令，确认它们与旧指令同为4字节。
[实际报告](../../research/ep7/descriptor-frame-plan.json)记录完整数值和直接SP偏移清单。

|拥有者 / 入口|descriptor相对SP|原局部帧→新局部帧|调整地址（分配 / 回收）|任务表栈大小|
|---|---:|---:|---|---:|
|command处理 603df803|20|320→332|603df805 / 603df933|4096|
|双队列relay 603ef892|12|312→324|603ef894 / 无返回循环|4752|
|kind19 relay 603ef94a|4|304→316|603ef94c / 603ef9b4|4096|
|kind19 worker 603f26a1|4|304→316|603f26a3 / 603f2792|8192|
|command drain 603e0546|12|312→324|603e0546 / 603e05e2|沿用command任务|

每个原descriptor恰好结束在原局部帧末端。增加12后，trailer属于新分配的局部空间，
保存寄存器区相应上移；原生SP相对字段偏移、descriptor指针计算和返回save-mask保留。
有回收指令的函数必须同时改正负两处。双队列relay在核对窗口中循环回到603ef8a1，
没有可修改的正常epilogue；不得虚构一个返回点。

完整五个函数窗口中的直接`(offset,sp)`访问均在原局部帧内，没有观察到需要跟随帧
变化移动的直接incoming-argument偏移。这个检查不涵盖所有间接栈别名、保存context、
异常展开或被调用函数；任务表预留栈也不是测得的空闲栈余量。command任务调用drain
时两层帧均存活，新增开销为24字节而非12；ABI桥、日志调用和scratch另计。

## materializer仍需要独立command scratch

603dfc7a的局部帧424不在上面五项中。它把输出descriptor指针存于SP+12，
把16字节command接收到SP+152；此处不是已经证明可用的28字节连续对象。
因此必须在603dfc9b的接收适配中使用独立scratch（队列最大148），只把16字节
前缀交回原位置，再将已解析票据写入**已扩大、调用者拥有**的descriptor尾部。
不能直接让28字节command进入原SP+152区域。

materializer的三处已识别直接调用是603dfb78、603e058f、603e05cd，均为
`call ...,[d2,d3,a2,a3],16`。前者来自正常router，后两处来自command drain。
正常router的descriptor由603df803的a3=SP+20提供；drain的a2=SP+12提供。
这给出两类明确拥有者，替代全局“当前descriptor”变量或从metadata地址回查generation。
原始字节call扫描不是全部间接入口证明；接收适配只能承认已经资格化的调用链。

## 适配行为

1. 新接收开始时清除扩展尾部，即使随后超时/失败/切换到备用queue4d也不能保留旧票据。
2. raw实际长度16/300只表示legacy；28/312再核对版本和身份。未通过则保留原生前缀、
   尾部中性。16字节command的metadata+12只用于按值身份，不以它读取扩展metadata。
3. 正常materializer将票据从command复制到它收到的owned descriptor。另两处drain
   在完成/ACK路径撤销票据，不把丢弃任务视为正常图像处理。
4. 已扩大的relay buffer可完整接收312字节，预处理仍接触原来的300字节前缀。
   通用sender仅对获准queue4c/ab/4f及已证明的owned对象发送扩展长度；其他路径
   按原生长度处理，不能让未扩大的消费者接收312字节。
5. 最终worker一次claim出独立快照，并安排票据retire；job之后不借用descriptor尾部。
   pipeline退出用invalidate_all撤销剩余记录，serial不重置。

这是一组必须一起安装的修改：五个帧、三个队列容量、receive/send适配、command接收
scratch、最终claim/cleanup。当前只有方案、codec和callable raw ABI已实现；未装
hook，未宣称全接收闭包、完整栈预算或任务域已通过。下一步编写持有实际容量的
接收适配和从这三种materializer调用链取得输出descriptor的ABI桥。
