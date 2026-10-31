# G4：显示容器生命周期、空导航表与独立 ID 查询

已将 `61032f10` 显示容器的创建、挂接时子控件填充、bulk cleanup 和析构连接起来。
文本创建现在会查询实际 child list，ID 已存在就不分配；查询桥保存并恢复原厂的共享
遍历游标。尚未安装 owner 捕获/撤销 hook，renderer_ready 仍为 false。

## 资源 +12 的已知消费方式

descriptor+12 保存到 object+24。文本 vtable+132/+136 分别为 setter `60cfe528`
和 getter `60cfe52e`。显示容器的 +208=`60d037a8` 从 owner+120 取得当前 child，
调用其 +136，读取结果的首个无符号 halfword 作为条目计数。非空匹配分支会按条目中的
目标 ID 调用 owner+436，更新 owner+120，再调用 service+580=`60d0107d`。

四个原厂文本描述符指向的表首计数都是 **0**，该消费者在 `60d037d4` 直接分支至
`60d0382d` 返回 0，不读取条目。后续描述符副本可以保留同一个原厂静态表引用，
其映像地址和存活仍由安装范围保障；无须构造新的导航记录，也不把指针改为 NULL。
这不是对任意导航表或所有消费者的完整分析。非空分支 `60d037e0` 存在当前 objdump
未识别的指令，本批没有依赖它的语义或宣称已经解析非空记录的全部格式。

## owner 的实际阶段

|阶段|实际路径与含义|
|---|---|
|工厂|表 `60fa9754` 为 type6111 → `60d37a6f`，请求1360字节，调用ctor `60d7ab3f`，随后用 `60d02a61` 载入描述符|
|child list 构造|基础ctor `60d028f9` 在 owner+92 调用 `60d0239e`；此时还不是57个子控件已填充|
|parent bind|`60d42d46 → 60d02ac3` 绑定 parent，`60d02aff` 调用 virtual+424=`60d7abf6`，后者循环创建/挂接索引1..57|
|bulk cleanup|owner+152 经 `60d43d4b → 60d02bbd → +432=60d42d69 → 60d02c03` 处理 child list|
|owner 析构|`60d7ab79 → 60d42c67 → 60d0297c → 60d023b2 → 60d023df → 60cfef5a` 清链表节点，然后返回 owner 的 deallocator|

填充回调结束时固定返回1；它不检查每次 factory/attach 的完整成功状态，不能仅凭这个
返回值证明57个 child 全部成功创建。owner 捕获必须结合实际分配来源、bind 阶段和
当前列表资格，不能把工厂返回非空或精确 vtable 当成生命周期证明。

bulk cleanup 从每个 child 的 +248 取得 allocator bytes，选择 service context，
依次调用 child+368、+152、+0，再调用析构返回的 deallocator。最后才清列表节点。
纯 owner 析构的 `60cfef5a` 只按context5/0释放链表节点，不访问 node+8 的 child。
因此独立文本句柄须在 **bulk cleanup之前** 撤销，owner析构还要有最终撤销覆盖；
只挂析构会太晚，单独调用析构也不能替代正常 child cleanup。

## ID 查询已接入创建流程

候选 ID `0x7e10` 未出现在该 owner 的57个原厂描述符中。静态缺席不是运行时预留。
`ep7_text_native_open` 在具体 qualifier 和 owner/service/descriptor 检查后，将自身
置为busy，调用实际查询桥；发现同 ID 就清busy并返回 -1，不进行 factory 分配。
ID 从传入 descriptor+2 读取，查询当前 immediate child list，不递归查子容器。

原厂 +436=`60d02cc2` 使用 `60d02439/60d02454` 遍历；两者会写 list+16，亦即
owner+108。新 `find_child.s` 保存 owner 和旧游标，调用原厂方法，再无条件恢复游标。
GCC参数 D0=owner、D1=uint16 ID；原生 A0=owner、D0=ID，结果保留 A0 指针。
桥自有12字节帧，原生函数自建24字节帧；共12条指令、32字节。链接地址为
`ep7_stock_ui_find_child_unresolved=60d02cc2`。

该桥复用原厂查询，没有新写链表遍历器。恢复游标不提供存活锁，也不能抵消列表并发
修改；qualifier 仍须保障实际 GUI 串行范围、有效 child list 和直到 attach 的成员稳定。
不通过这些前置检查时，不会调用查询桥或读取 owner+108。

## 本次验证与剩余接合

- [原厂证据](../../research/ep7/ui-owner-lifecycle-current.json)：124条指令、12项数据，
  复用现有资源解析和无SHA输入验证；保留非空分支的decoder缺口。
- [主机报告](../../research/ep7/ui-owner-lookup-host.json)：沿用生命周期实际C组合，增加
  ID碰撞在分配前拒绝的场景，共16项strict/ASan/UBSan通过。native查询为mock，
  不声称主机执行了32字节目标桥。
- [目标报告](../../research/ep7/ui-owner-lookup-target.json)：16个对象通过，11个剩余
  外部符号均为原厂入口。查询桥逐指令/重定位检查通过；当前lifecycle C925字节，
  open局部帧80字节，尚未计算完整原生链的最坏栈。

下一步是选择带真实 owner 来源的具体调用位置，完成捕获、bulk cleanup前撤销和析构
兜底，并构造有独立ID/布局存储的文本资源副本。H/L viewer、输入资格、安装顺序和
G6放置仍须接合。这里没有整体固件编译、目标执行、相机控件创建或刷机结论。
