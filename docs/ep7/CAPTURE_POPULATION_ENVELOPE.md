# 捕获的两阶段冻结与 controller 身份

## 当前实现

复用现有 controller sidecar，新增 `ep7c_sample_population` 与
`ep7c_finish_population`。第一阶段只冻结 captured profile 的 H/L；第二阶段核对
同一 token、generation、associated、capture、ID、raw mode、selector，然后允许复制。
第二阶段不调用设置锁、不重新读取 UI。原有 `ep7c_seal` 组合这两步，保留已完成整体
填充的主机调用接口。

提前 copyout 会永久取消尚未完成的 sample，包括 output 为 NULL 的提前调用。
finish失败、身份/profile不符、free/reuse、state33重入均不能重新补齐。已经完整复制的
值保持独立生命周期。此代码没有提供原生对象锁或覆盖未知重复 population 路径。

## 本次核对的原厂顺序

|边界|原厂调用 / 返回|含义|
|---|---|---|
|新 node|602a31c7 → 602a3116 / 602a31cc|56字节node，A0返回；node+0为capture ID，+8为associated|
|入队|602a31d1 → 602a3204|早于两个population调用；不能把返回节点直接视为已冻结|
|第一段填充|602a31ea → 602a7ea0 / 602a31ef|正常返回后读取已拥有capture的profile并sample一次|
|第二段填充|602a31f7 → 602a8dbd / 602a31fc|同一拥有者与token完成后finish；不补读当前UI|
|selected关联|602a2903|此时才写associated+8=node；新node登记时不能要求这个后写backlink|
|metadata scope|602ac3de → 602ac748|既有producer自有scope接收已冻结值，metadata仍148字节|

第一段函数尾部 D0 是 typed getter 的结果；第二段也没有布尔成功返回约定。
调用者使用正常控制返回，不以 D0==0 猜测成功。原生 frame分别28/20/48；接合桥必须
保持它们的save mask、返回与caller-owned node/token。登记必须在入队前完成，完成确认
不能使已被提前消费的对象重新获得资格。

任务配置行60039664实测为 `{0x73,0,0,0x60289852,25,4096,0}`。
`runtime/contexts.c` 的producer provider现要求实际当前TCB entry为60289852且domain0，
随后仍核对producer自身scope/调用链。相同域的command或worker任务不能获取producer
context。配置ID0x73不是任务代际保证；实际检查使用已有当前TCB查询。
controller仅配置4096字节栈，新增observer和嵌套GCC调用仍必须纳入G6总预算。

## 执行证据与边界

- [当前输入报告](../../research/ep7/capture-envelope-current.json)：83条指令和1任务行。
  包括既有清单13处node free的实际 `CALL 60022732,[],4`；这里只重验已列出的call，
  没有由此推断不存在其他释放或证明异步排他。
- [sidecar host](../../research/ep7/capture-envelope-sidecar-host.json)：strict、ASan/UBSan
  通过，覆盖两阶段间UI变化、finish不取设置锁、提前消费永久中性、profile变更、
  失败完成、free/reuse和33重入。
- [实际软件链](../../research/ep7/capture-envelope-integration-host.json)：UI在sample与
  finish之间归零，原H+3/L-2仍经command、三段relay和16个fresh job得到原输出。
- [sidecar目标对象](../../research/ep7/capture-envelope-sidecar-target.json)及
  [controller provider目标对象](../../research/ep7/capture-controller-runtime-target.json)
  通过；[runtime host](../../research/ep7/capture-controller-runtime-host.json)验证非controller
  producer拒绝。没有运行旧SHA入口；sanitizer沿用已独立验证的non-PIE启动规避。

此节点完成了真实顺序所需的sidecar行为及实际任务准入；新node登记/前缀读取/两个normal
return/13个释放的原生桥、初始化绑定、完整排他和源provider仍须接合。不能把纯C两阶段
实现或配置任务行当成原生生命周期完成，也未开始固件整体编译。
