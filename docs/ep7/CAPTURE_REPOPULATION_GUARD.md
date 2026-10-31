# 捕获重填充：在原厂首次写入前撤销旧快照

原有两段 completion observer 只在三条新建路线返回后 sample/finish。已经 sealed
的 capture 若再次进入填充函数，而 ID、地址和 COLOR profile 不变，旧 `attempted`
检查只会拒绝再次采样，却没有撤销旧 sealed 快照。这不能作为图像代际保护。

本批复用现有 sidecar、capture lookup 和 native bridge，不扩展56字节节点或原厂
capture，不在异步回调中重新读取 UI。解决的是这两个原厂函数正常入口的重复填充；
其他图像重用/配置写入与完整别名释放仍属于 G1 后续闭包。

## 两处公共边界

|包含函数|替换的原厂 CALL|observer 时机|随后写入|
|---|---|---|---|
|602a7ea0 第一段 population|602a7ea0 → 6029b9d1，`[],24`|lookup 返回实际 capture A0 后|7ea9调用60300055，模板循环60300061写 capture|
|602a8dbd 第二段 population|602a8dca → 6029b9d1，`[],24`|lookup 返回实际 capture A0 后|8ddd起写 capture；之前24/28/20偏移均为本函数栈存储|

两处都是完整7字节 wide CALL。新桥先保留原 D0 ID 调用同一个原厂 lookup，随后
保存其 D0/D1/A0/A1/D2/MDR，传 A0 和 phase 给 `ep7cn_prewrite`，恢复后 `ret [],24`。
D3/A2/A3依赖既有 GCC 保存契约。桥增加40字节 observer frame，以及内层原厂 lookup
24字节调用帧；没有移植或猜测原厂 `udfu01` 索引运算。

7ea0 的10处、8dbd 的11处已列直接 CALL 都进入相同公共边界，因而无需为每个调用者
复制一份填充逻辑。三条已确认 fresh/sample/finish 路线仍是唯一能够新建、采样并
封存的入口。未接合调用者也会在实际写入已登记 capture 前撤销其旧快照，但不会因此
获得 H/L 准入。正常入口支配关系不等于证明没有跳入函数内部的未知代码。

实际 CALL 检查组从25处扩为27处，要求两个新 observer 与原有创建/采样/完成/状态/
释放 hooks 同时存在。初始化 inline hook和冷启动安装顺序仍由 G6 独立负责。

## 有界状态变化

每个 sidecar 项增加 `begun`、`post_begun`，仍按原 token 和 controller generation
保留身份，不通过重复填充生成新 token：

1. 第一段写入前只能从未尝试的 fresh 项进入；正常返回后才可以 sample。
2. 第二段写入前只能从已经 sample 的项进入；正常返回且 prefix 一致才可以 seal。
3. 重复第一段、重复第二段、倒序进入或重叠进入，立即清除 sampled/sealed并锁定
   attempted。即使所有原厂地址/profile都相同，后续 completion 也不能恢复旧快照。
4. 缺少任一 prewrite 通知，completion不能替代它完成封存。提前 copyout 继续永久
   中性；只有真实释放/重新分配后的新 token 才能重新尝试。

公共 observer只扫描当前代际中 capture标签相同的已登记项，不读取capture内容、
不通过裸 ID 绑定新 token，也不影响另一个 capture。已经交给下游的按值快照保持
原值；这是前一图像独立拥有的数据，不随原节点重填充而修改。

`ep7cn_prewrite` 使用现有销毁类事务入口，runtime stop后仍执行撤销。外来任务或
新增 C 工作中的重入写入不能只关闭准入然后继续原厂写入，而是进入不返回隔离。
这保护已接合边界；它没有给整段原厂执行、其他CPU或未接合写入建立内存锁。

`ep7c_seal` 仍是软件 fixture 的完整流程便利函数，现在依次调用 begin/sample/
begin/finish；原生代码不能用它替代写入前通知。

## 本次验证

- [原厂静态报告](../../research/ep7/capture-repopulation-native.json)：123条精确指令、
  3项任务/事件数据和原有四入口的全 main 有限 CALL 候选清单通过。使用既有容器
  结构、加法和及回转验证；没有 SHA 或原厂代码执行。
- [原生 C 报告](../../research/ep7/capture-repopulation-host.json)：21个独立模拟启动
  场景通过 strict/ASan/UBSan，其中9个新增场景覆盖重复填充、第二段单独重写、倒序/
  重叠、漏通知、错误 capture、外来/重入写入、stop后撤销及无效 lookup结果。
  首次 strict运行因 fixture低地址映射未覆盖新增两个 CALL地址而崩溃；扩大自有
  映射至602a9000后两种构建均通过。没有扩大生产代码的有效地址范围。
- 既有 portable sidecar strict/ASan/UBSan通过，已同步显式 begin契约。
- [整链报告](../../research/ep7/capture-repopulation-integration.json)：现有16个job的
  按值快照、队列输送及CPU reader软件链通过。首次编译发现 fixture仍引用已移除的
  UI admission接口，现改为当前 transaction mock；真实 router/raw/UI/core仍参与，
  native input/gate仍为mock，不把这个结果当成GUI原生接合验收。
- [目标对象报告](../../research/ep7/capture-repopulation-target.json)：57对象及自有
  软件符号闭合检查通过，仍有32个已列原厂外部绑定。桥434字节/165条指令，新增42条
  桥指令的输入、结果、MDR、frame和重定位顺序通过核对。native binding text1458 /
  BSS696，cohort text481，sidecar text2795字节。prewrite局部`.su`36字节；这些数字
  不是完整controller最坏栈的证明。

下一步继续沿已登记节点的队列、全局指针、associated和异步完成回调，核对剩余
释放/重用责任。随后汇入 G2/G3 退出存活及 G6 放置、完整安装和总栈审查。当前
未安装 hooks、未执行目标代码、未开始整体固件构建，G8仍未就绪。
