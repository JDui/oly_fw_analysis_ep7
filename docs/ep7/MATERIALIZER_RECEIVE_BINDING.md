# materializer 的有界栈映射与接收桥

2026-10-31。实现对应603dfc9b这一个调用点，替代它对603eeb57的调用；
没有修改固件、链接镜像或安装hook。复用已有本地raw receive ABI和owned I/O。

令W为原生CALL `[d2,d3,a2,a3],44` 后的桥入口SP。原生CALL把返回地址存于
调用前SP，再分配立即数指定的整个帧；已有ABI研究支持此语义。
materializer自身局部帧424，进入它的CALL帧16；正常router另有CALL帧48。

|入口W相对偏移|内容 / 验证|
|---:|---|
|44|receive返回PC必须为603dfca2|
|48|原生有符号timeout；原wrapper从同一位置读取|
|56|materializer保存的输出descriptor指针|
|196|原16字节command，来自materializer SP+152|
|484|materializer的调用方返回PC|
|532|仅正常router分支读取，须为603df8c0|
|552|正常command拥有者的descriptor，必须与偏移56的指针相等|
|496|两条drain路径的descriptor，必须与偏移56的指针相等|

偏移484只接受603dfb7d（正常）、603e0594（首次drain）和603e05d2（drain循环）。
未知调用链先拒绝，不读取偏移532。全部读操作、16字节command和312字节descriptor
范围先核对当前任务的真实栈界限与32位地址溢出。拒绝时输出归零，不进行I/O或写栈。

**这些PC和范围不证明扩容已经安装。** `ep7q_materializer_context_unresolved`
必须先验证五个帧、队列/适配安装组的发布状态、当前任务和本地域，并提供稳定的真实
栈映射及队列资格函数；它目前仍是未解析外部符号。原帧恰好也具有相同指针关系，
所以不能仅凭布局匹配设置`expanded_group_ready`。

桥只用四条自写指令传入handle和W，再以原来的mask/44字节RET返回。GCC的
返回/参数暂存区W+0..11与原生保存寄存器W+28..43不重叠；原返回地址W+44保留。
最后使用RET从栈恢复返回PC，不使用已被内层CALL修改的MDR。后续原厂指令立刻
比较d0，因此没有新增保留算术flags的要求。此桥省去了原wrapper的诊断日志调用。

C入口使用真实本地receive veneer，调用已有command receiver：独立148字节scratch
接收，写回原16字节前缀，再将票据放到扩大后的descriptor尾部。它返回原wrapper
约定的0/-1/-2，materializer继续执行自己的成功/失败转换。drain的票据不在此提前
claim；ACK/失败退出的retire仍须在对应生命周期接入，不把此桥视为drain闭包。

验证结果：

- [当前原厂指令证据](../../research/ep7/materializer-frame-current.json)复用现有输入检查/反汇编工具，不做SHA。
- [主机报告](../../research/ep7/materializer-frame-integration-host.json)：strict与ASan/UBSan通过；覆盖三条布局、短栈、错误指针/PC、非活动安装、非目标handle和地址溢出，并将正常布局接入owned receive。原生入口未执行。
- [目标对象报告](../../research/ep7/materializer-frame-target.json)：四指令桥13字节，mapper519字节、入口155字节；mapper/入口局部栈60/136字节。联合对象仍有context provider和两个raw原生地址共3个未解析符号。没有把单函数栈相加当作全链路安全证明。

下一项：把相同的有界栈资格接到四处双队列接收、两个kind19消费者及三段发送，
再实现最终claim/retire和drain清理。安装组必须覆盖所有扩展消息消费者，未资格化
的分支不能凭tag访问尾部；任务域、启动发布和完整栈预算仍属G3/G6。
