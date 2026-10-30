# 描述符转发、旧格式回退和票据清理

2026-10-31。三段转发都经过603dfa41，再于603dfaa1调用603eeba4。新增桥只对应
这个发送调用点，保存原生`[d2,d3,a2],36`帧约定。没有写入或链接固件。

|路径|[W+56]父返回PC|额外校验|descriptor相对W|
|---|---|---|---:|
|正常command路由|603dfc44|[W+104]=603df8c0|124|
|双队列relay|603ef93e|原生a0匹配|68|
|kind19 relay|603ef993|原生a0匹配|60|

W为发送桥入口SP；[W+36]必须为603dfaa8，timeout从W+40读取。栈范围、实际a0、
安装组与任务资格均须满足后才能读取312字节。未知调用链直接按原厂300字节发送，
不读尾部。它不会产生扩展消息，但不证明未资格化分支的票据能被清理；安装前仍要
闭合所有获准票据的路由，不能依靠这一回退掩盖遗漏。

桥以W+12/+16/+20保存原handle、buffer和trace指针，GCC使用W+0..11，原生保存
寄存器在W+24..35。回退恢复这三个值，并恢复该调用点静态确定的d1=300；在原W
跳回603eeba4，保留timeout/trace栈参数。已执行raw发送时只返回其归一化状态，
不再重发。编译器普通调用约定保护未由原生mask保存的a3。

`forward.c`复用owned sender：先消费本地trailer，再发送独立300/312字节scratch。
有效票据成功转发到4c/ab/4f后仍归接收方；发送失败、4d旧格式路由、非支持queue
或失去kind/route资格时，将票据值交给`retire_owned`。若raw未被调用，则返回内部值256，
由原生桥恢复旧格式发送。没有清理责任方时不允许发送扩展消息。

新增`ep7w_retirement_ticket`只为撤销读取owned312中的marker/metadata/serial。
它不检查已可能被预处理改变的kind/route，也不能用于claim；普通`ep7w_ticket`仍保留
这些准入检查。metadata身份仍必须对应原票据，不能通过裸地址重建当前generation。
`retire_owned`必须接管失败的poll-lock清理义务，保存票据值直到成功撤销或获准的
pipeline失效；禁止保留descriptor指针。原生责任方尚未绑定，主机fixture已验证一次
锁失败后的值保留和后续撤销，不能据此宣称相机端已实现该责任方。

验证结果：

- [32条原厂指令](../../research/ep7/descriptor-send-current.json)核对调用链、参数、timeout和mask/frame，无SHA。
- [主机集成](../../research/ep7/descriptor-send-integration-host.json)strict/ASan/UBSan通过，使用`--no-hash --asan-verbose`。三种sender布局、发送失败/重试、route变化、旧queue、延迟清理，以及完整三段forward/receive→16个真实job槽位均执行。此前sanitizer偶发超时原因仍未确认；新选项仅增加启动诊断，未扩大30秒超时或改变测试。
- [联合目标对象](../../research/ep7/descriptor-send-target.json)：发送桥17指令/44字节；布局319字节/局部栈56，入口148字节/局部栈92，forward114字节/局部栈72；owned sender局部栈仍400字节。联合对象7个未解析符号均为原生地址或context provider，没有目标链接/执行。

下一步接通捕获producer的28字节command、最终worker的claim/retire、drain/失败退出，
并落实任务域、真实栈界限、安装发布和清理责任方。当前收发桥不能单独安装。

后续[producer接合](PRODUCER_SCOPE_BINDING.md)发现600514b6还包含发送后的通知。
当前descriptor sender已改为复用该原厂封装，保留通知与错误路径；上文旧目标报告的
直接raw send接合已被替代，未曾安装。最新联合对象/主机报告见producer文档。
