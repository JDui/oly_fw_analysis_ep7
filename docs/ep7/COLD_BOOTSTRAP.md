# 一次性原生 bootstrap 与早期安装组

2026-10-31。现有bootstrap/private-lock/runtime已在具体启动入口组合为生产候选，
补上永久对象与发布调用。**仅完成源码、目标对象和合成语义验证；没有安装或整体固件构建。**

## 从 Usr3 接续发布

[启动入口研究](BOOTSTRAP_ENTRY.md)的60191371原为CALL6011f620、mask0/frame4。
新的[桥](../../prototypes/ep7_volatile_hl/runtime/cold_bootstrap_bridge.s)先调用
[初始化函数](../../prototypes/ep7_volatile_hl/runtime/cold_bootstrap.c)，成功后tail-JMP原函数。
54字节桥在原W下方暂用40字节：保留D0/D1/A0/A1、D2、MDR和PSW，GCC保留D3/A2/A3；
原调用帧和60191378返回地址不变。Usr3从entry到该位置没有硬件loop指令；该契约不适用
于任意inline位置、活跃SETLB循环或中断入口。

初始化依次执行：

1. 拒绝重复进入或已有发布slot；查询实际任务，要求ID002d、domain0、entry601912fb、
   实际栈2048字节且当前anchor在其中。栈范围判断复用ep7n_native_current_task。
2. 核对早期安装组，以及sidecar确实已初始化、未poison、state/serial/generation均为0。
   不靠补写一个ready开关跳过安装事实，也不尝试重置旧对象。
3. 使用既有ep7b_prepare创建独占1/1 semaphore和同一个core；ep7r_prepare复用它。
4. ep7r_publish再次调用安装检查，验证并固定五个真实queue实例/容量/backing，然后只发布一次。

core/boot/runtime现在有真正的永久BSS实例，目标总计5704字节，另有4字节once状态。
仍依赖已研究的16KiB冷清零/独占放置，不能靠“BSS链接出来了”推断设备已经清零。
原厂函数的新绑定只有 `ep7_stock_bootstrap_original_unresolved = 6011f620`。

失败使用现有自有quarantine保持循环，不回到原厂启动后续接收任务。
prepare失败沿用ep7b现有回收/保留策略；prepare成功但runtime准备/发布失败时，仅尝试
回收尚未发布的私有锁。删除失败保留owned handle；已发布或重复调用不删除、不清空runtime。
这不是已验证的相机故障恢复机制，真实exception/cache行为仍在后续资格范围。

## 早期检查的准确范围

[cold_cohort.c](../../prototypes/ep7_volatile_hl/runtime/cold_cohort.c)先要求第1–4段的
copy-attempt和initializer-completed位均存在、原生controller state62234fc0为0，再核对：

|接续|完整覆盖长度|预期候选形式|
|---|---:|---|
|600201fe 冷清零|6|JMP32到cold_clear +1个NOP|
|60036d3c queue receive gate|10|JMP32 +5个NOP|
|60036f93 queue send gate|6|JMP32 +1个NOP|
|60031072 queue delete observer|6|JMP32 +1个NOP|
|602897d7 controller initializer|6|JMP32 +1个NOP|
|60191371 bootstrap CALL|7|CALL32，mask0/frame4|
|600229b9 /60022c28 池边界|各2|8020→801f、8f20→8f1f|

NOP采用GNU定义的CB。跨度逐条对应完整原指令，不截断尾部。
随后复用capture、pipeline和CPU COLOR的既有cohort，覆盖其实际CALL/veneer、帧与queue字段。
加载位不等于字节传输成功；此时看到缩小后的池边界，也不证明更早没有分配过保留槽。
启动前缀加载者、guard writer、RAM/代码所有权和cache可见性仍必须另行关闭。

该阶段完全不读取第6段UI表，也不等待后续Usr4/Usr5。UI已经有owner/MVC/input cohort；
selector初始化与COLOR gate均已有initializer表项检查，继续复用，后续汇入完整离线安装清单。
发布runtime不会直接开放H/L renderer，初始四profile的H/L仍为零。

## 本次最小验证

[检查脚本](../../tools/ep7_cold_bootstrap_check.py)、[报告](../../research/ep7/cold-bootstrap.json)：

- 三个新增目标对象通过：bootstrap text399/BSS5708，早期cohort text357，bridge text54；
  bootstrap局部栈96，installed局部栈20，cohort局部栈12，bridge额外40。**未取得完整栈峰值。**
- 15个独立进程场景使用实际bootstrap/provider/core/runtime/transport；原生任务、sem、queue
  回调为fixture。检查单次发布、重复进入、错误任务域/entry/ID/栈、安装组变化、旧容量、
  创建/删除失败以及sidecar未初始化/poison/已有serial的拒绝；失败均不继续原厂调用。
- 实际early cohort在不可执行合成页上运行，48项负检查覆盖加载位、已进入controller状态、
  每个inline字节/NOP、bootstrap CALL及两条池边界；没有映射后续UI页。
- 生产汇编的完整字节与两处重定位核对，合成链接禁用relax；复用GNU11类指令函数体，
  在两种PSW初值和模拟GCC可破坏寄存器条件下，核对恢复状态、原返回位置及40字节以外内存。
  三个负控制分别检出PSW、MDR、D2恢复缺失。该受限harness不是完整libsim或相机执行。

开发期间修正了host链接遗漏已有queue_context.c、生成harness的strict缩进告警；未放宽
编译告警或替换生产逻辑来通过。未重跑历史pipeline/UI生命周期全集或完整聚合对象检查。
聚合脚本已登记新源码及4个cold外部绑定，现有对象尺寸/定义用于增量核对。

[更新预算](../../research/ep7/prebuild-storage-budget.json)：107个实现源的未链接text46,543，
静态BSS8,084；16KiB payload余8,300，两个代码候选合计65,280还余18,737，均未扣最终对齐。
永久runtime已经计入BSS，删除了旧预算重复追加5704字节的可能；只重新编译一个sizeof探针。

下一项为完整安装清单与最终符号/分区、原厂调用段和新增桥合并的全栈上界；原生捕获/退出、
GUI旁路、代码/RAM所有权与cache准入仍未完成。G8保持未通过，不宣称已开始固件整体编译。
