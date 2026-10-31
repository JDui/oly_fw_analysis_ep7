# 实际队列对象视图

2026-10-31。G3 接入前的只读事实查询，未运行于相机。

`runtime/queue_context.c` 复用当前任务查询的 kernel read/get_tid 接口，沿原厂
`60036c8e`/`60036ede` 的查找路径读取实际队列。只接受同一域的有效 handle；
检查 CPU word、域 root、`root+60` 的 limits、`limits+26` 的 queue count，随后读取
`root+232` 指针表中的 `(handle & 0xfff)-1` 项。

|实际字段|offset|用途|
|---|---:|---|
|ID|0|要求完整 handle 相等，零表示已删除|
|attributes|20|包含 initializer 设置的 backing 分配标志 128|
|maximum|24|raw send 检查的消息上限；raw receive 没有 capacity 参数|
|ring bytes|28|实际配置的 backing 长度|
|backing|32|initializer 分配后保存的地址；本查询不读取其内容|

两次读取必须得到相同对象、表地址和配置；查询前后 get_tid 一致。
指针、索引、ring end 都先检查边界/溢出。失败清空输出，不访问陌生域的表。
native backend 复用原有 volatile 读和 get_tid 桥，没有新增内核 API。

这不是队列代际或存活锁。删除路径先释放 allocated backing，再清零 ID；
两次读取无法排除同址重建或检查后的删除。安装器必须单独保证查询至 raw I/O
返回期间禁止删除、重建和改配置；退出/关闭流程仍是编译前未决项。
不能凭查询成功设置 expanded_group_ready。

定向证据：

- [原厂 75 条指令核对](../../research/ep7/runtime-queue-current.json)：复用已有
  queue transport witnesses，只增加实际索引、limits 和 delete 相关窗口。
- [host strict 与 ASan/UBSan](../../research/ep7/runtime-queue-host.json)：执行真实
  query，kernel 回调模拟；覆盖索引越界、任务/CPU 域不一致、已删除 ID、ring end
  溢出、两次查询间 maximum 变化，不代表真实设备验证。
- [目标对象检查](../../research/ep7/runtime-queue-target.json)：queue query 文本 853
  字节，查询局部栈 104 字节，read_view 局部栈 44 字节；不能相加替代完整调用栈预算。
  仍仅有 get_tid 与 delay 两个原生地址外部符号，未链接固件。

未做 SHA 校验，未修改固件、未安装 hook。下一项是共享 runtime 持久发布、
固定实际 queue 实例，以及清理失败后保持原工作对象的策略。
