# 原生 metadata 领取、初始化、发布与重用

2026-11-01。原四槽metadata池初始化、完整领取和参数初始化已执行；原调用者实际
发布当前command，并将metadata指针写入command+60。请求状态生产者已读到原生
生成的halfword1024，随后停在尚未提供的command+72 flags读取。

证据：[复现工具](../../tools/ep7_candidate_request_metadata_sim.py)、
[执行报告](../../research/ep7/candidate-request-metadata-sim.json)。capture、候选004
及fishcu五组件研究容器保持不变，没有SHA或相机操作。

|原厂路径|实际结果|新增指令|
|---|---|---:|
|6029c697..c6bb|四槽free/index及selector原生初始化|57|
|6029c98e..c99d|完整materializer及实际current-command发布|57|
|6029cd4f..cd90|实际领取槽0、写command+60、完整602ab5e4初始化|419|
|独立分支602a75c3/602a7556|原生释放后重新领取同一槽|25|
|6029d156状态生产者前缀|读取metadata+6后停在command+72|5|

合计563条新增指令，最大观察新栈深56B。新增35B全部用于真实store：四槽的2B
header及1B selector共9B，首槽本分支实际初始化26B，无新增BSS。其余96B槽成员
和闲置槽payload继续未映射。

本分支复用之前原生生成的16B事件，在其已存在的command内副本上执行原materializer
的原址复制，再由6029c997发布6223d414。它验证返回指针到发布的代码关系，未执行
新的queue receive或整个dispatcher。随后原6029cd5c将6223e450写入command+60。
原state2348=0选择class10000，完整602ab5e4生成flags256、kind1及halfword
`(1024,1241,512,0)`；20/24/32三个word为0，selector推进到1。

只做一项关键归属验证：在独立副本中，原release清free标志并将selector退回0，
但保留旧payload和command+60；下一次原claim返回同一地址，旧数据仍保留。这说明
裸指针相同不足以证明同一请求代际。它不证明完整固件存在越界或释放后使用，也不
替代上层清理、并发静止和代际传递的证明。主探针中的槽继续保持已领取状态。

原状态生产者6029d16a读取command+72/4B时停止，没有填写未知flags；offset1684/
1686仍未生成，第二段填充未恢复。下一步追该输入的生产/传递，或明确限定flags
输入模型下的条件验证；完整消息来源、事件时序、有效COLOR、S3/S4与恢复仍待证。
