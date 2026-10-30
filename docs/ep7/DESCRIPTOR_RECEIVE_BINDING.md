# relay 和 worker 的描述符接收桥

2026-10-31。已实现四处双队列接收和两条kind19 helper调用链的有界布局、原生入口
桥及本地raw receive接合。未安装hook或扩大实际队列。沿用materializer的栈映射，
公共的地址溢出/范围/word读取已抽到`native/stack.c`。

|拥有者|wrapper返回PC|父返回PC|相对wrapper入口W的descriptor|handle|
|---|---|---|---:|---|
|双队列relay首次4c|603ef8ba|无额外父读取|56|4c|
|双队列relay再次4c|603ef902|无额外父读取|56|4c|
|双队列relay首次4d|603ef8d7|无额外父读取|56|4d|
|双队列relay再次4d|603ef91f|无额外父读取|56|4d|
|kind19 relay经603df9f1|603dfa0b|[W+60]=603ef962|64|ab|
|kind19 worker经603df9f1|603dfa0b|[W+60]=603f26bb|64|4f|

五处实际替换调用点为603ef8b5/8d2/8fd/91a及共享helper内603dfa04，原生mask/frame
均为`[d2,d3,a2,a3],44`。桥把原始d0/d1/a0/a1保存在W+12..27，将该结构及W传给GCC；
这些字段与GCC返回/flush区W+0..11、原生保存寄存器W+28..43相互独立。
布局还必须匹配handle、原nominal长度300、实际a0和312字节栈范围；timeout来自W+48。

共享helper并非kind19专用。对不在扩展集合的未知队列，入口返回内部值256，桥恢复
全部四个参数，在原W直接跳回原厂603eeb57。原timeout和trace参数W+48/+52保留；
没有复制未证明的尾部。对4c/ab/4f，未知调用者或缺失安装/任务资格一律失败，
不会回到可能只拥有300字节的旧接收路径。安装前仍须证明扩展队列接收闭包，
否则拒绝未知消费者虽然避免越界，却不能保证原厂功能继续工作。

4d的当前原厂配置已核对：60040d76=4d，配置行6003b430为最大300、ring9728。
获准的双队列拥有者即使从4d接收，也先清除新分配尾部中的旧票据。未获准的4d
调用保留原厂300字节路径。资格provider仍未绑定，不以数值extent或PC代替安装证明。

验证：

- [只读原厂证据](../../research/ep7/descriptor-receive-current.json)：52指令、5项数据，无SHA。
- [主机执行](../../research/ep7/descriptor-receive-integration-host.json)：六条布局均进入真实owned receiver；检查短栈、指针/队列/长度不匹配、旧尾部和非活动安装。strict通过；一次普通ASan运行超时30秒，启用启动日志的诊断复跑ASan/UBSan通过。超时原因未确认，未将复跑通过视为已修复。
- [当前联合目标对象](../../research/ep7/descriptor-receive-target.json)：描述符桥18条指令/45字节，局部分支relocation指向原mask/44字节RET；mapper376字节/局部栈52，入口162字节/局部栈124。联合对象包括此前materializer和公共stack helper，仍有5个明确未解析原生/context符号。

下一步是发送桥、最终worker一次claim/retire、drain和失败清理，再合并所有扩容与
启动发布。当前没有执行原生桥、模拟硬件队列、证明完整任务栈余量或生成修改固件。
