# 捕获冻结值的栈作用域与命令发布

2026-10-31。首端producer复用sidecar冻结值、ticket注册表、wire codec和清理责任方。
metadata仍分配148字节，不使用其尾部或裸地址回查。原生provider后续已在
[capture source](CAPTURE_NATIVE_BINDING.md)接合，忙碌等待路径已在
[deferred carriage](DEFERRED_PRODUCER_CARRIAGE.md)补齐；以下验证数字保留原批次范围。
没有安装固件。

## 具体栈承载

只替换602ac3de对602ac748的调用，保留`[d2,a2,a3],32`。此时d0为captureID、a2为
associated record。桥额外分配64字节；该帧SP=S的+24..55保存32字节scope，包含
captureID、25字节已冻结snapshot和单次消费状态。GCC helper第三参数指针在S+12，
原captureID/associated值在S+16/+20。

helper须先证明controller排他性、live associated↔node身份与sidecar资格，再复制
已经冻结的值；不得重新采样UI。缺失资格时scope中性，
原厂metadata函数照常执行。桥以独立32字节native帧调用原602ac748，返回到自写
链接标签后回收64字节，以原mask/frame返回。嵌套期间额外栈成本为96字节，另加
GCC辅助函数/更深原生调用；这不是完整任务栈预算。

602ac869命令发送桥入口W=S-80：

|偏移|验证/对象|
|---:|---|
|44|native CALL保存的d2，即captureID|
|48|返回PC必须为602ac870|
|52|原16字节command，须与原a0相等|
|80|须为已链接的自写scope返回标签|
|96|scope桥保存的原captureID|
|104|32字节owned scope，其captureID须与前两项相等|
|176|原producer返回PC必须为602ac3e3|

栈范围与安装组资格先行。旧直接调用在W+80不会匹配新标签，因而不读取更远的
scope/上层帧。另一路602ac60e不承认a2为associated；它现在使用等待队列预先保存、
由有界 service 栈拥有的独立 scope，详见上述 deferred carriage。
发送桥保留`[d2,d3],48`；未获准时恢复四个参数，在原W跳回6020beb4。

`producer.c`先将AVAILABLE改为CONSUMED，再检查资格和准备ticket。失败不晚补填。
prepare/encode之后先publish，再发送28字节，允许enqueue内立即出现消费者。
prepare/资格失败走原16字节路径；publish/发送失败将ticket值交给清理责任方，
不改变原metadata释放责任。

## 保留原厂发送后的通知

本轮发现600514b6在入队/错误归一化后，于600515d4条件调用60051078，后者调用
本地60035a5e通知服务。只调用raw60036ede会绕过这条路径。

producer和descriptor sender现均使用`ep7_gcc_queue_send_preserving_hooks`，构造
原生pointer/count二字对并调用原600514b6，保留其路由、错误处理和通知。本地域
资格仍由provider先证明。named timeout结果-2映射到owned I/O的-50词汇，再恢复-2；
主机回归防止二次归一化成-1。旧raw send veneer保留作研究接口，当前发送候选不再使用。

## 验证与限制

- [原厂证据](../../research/ep7/producer-scope-current.json)：48条指令，含发送状态和通知链，无SHA。
- [联合目标对象](../../research/ep7/producer-scope-target.json)：两座producer桥共30指令/81字节；queue桥共23指令，新增named send自身24字节帧/native48。scope布局局部栈52、capture helper52、发布入口100、portable producer80；12个原生/capture/context外部符号仍未解析。
- [主机集成](../../research/ep7/producer-scope-integration-host.json)：strict、ASan/UBSan通过。立即消费者成功claim、冻结值不随以后UI变动、失败不晚补填、发送超时和锁失败清理保留均已执行。完整链由真实portable producer生成28字节命令，经三段forward/receive进入16个真实job槽位。native API/资格仍是fixture。

此前sanitizer超时已独立复现于仅输出MAIN的最小程序：默认PIE版本在ASan初始化
完成前反复DEADLYSIGNAL，non-PIE连续6次退出0。见[诊断输入与结果](../../research/ep7/asan-startup-diagnostic.json)。
集成检查仅给sanitizer可执行文件增加`-fno-pie -no-pie`，保留检查项、fail-fast和30秒
超时；当前通过。这是本机已观察的规避方式，不是sanitizer内部通用根因结论。

G2仍需最终worker claim/retire和drain/失败清理；G1 native snapshot来源、G3任务/锁、
G6安装发布/完整栈预算仍未闭合。本批对象不等于固件整体构建。
