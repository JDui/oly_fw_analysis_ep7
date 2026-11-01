# E-P7 原厂请求、快照字段构造与格式模块停止点

2026-11-01。实际原厂调用点生成了128字节请求，原生复制到服务对象后，任务分发
从请求中读取真实回调60426f83并执行。内部6042661b已返回，124字节字段对象与原生
缓存复制逐字节一致。完整producer及wrapper尚未返回：两条GPIO输入分支都停在
60556934读取格式模块就绪标志a2788ca8，MDR60427f7d。

[探针](../../tools/ep7_candidate_snapshot_sim.py)和
[报告](../../research/ep7/candidate-snapshot-sim.json)固定上述真实停止点，累计新增
21374条指令，最大新增观测栈深280字节，不是完整任务栈上界。候选004及已有fishcu
研究容器未改写；没有重编译、SHA校验或相机操作。

## 原厂请求与回调

60422143实际提供命令0501和空可选上下文，调用60425eaf构造请求；299条指令后停在
通用dispatcher603f3344。请求+4为回调60426f83，+20为命令0501，+23为mode。
60419d34用原生copy搬运完整128字节到6229faf8，215条指令，字节回读一致。

60409e3c任务前缀执行92条指令，取得请求及字段指针；随后显式跨过尚未运行的
receive/log区间，从60409eb6恢复真实分发代码。6041a51c重置selector及快照指针，
6041a20a通过请求回调进入60426f83。这是有明确切口的任务交接，不是queue17调度
已验证，也没有将任何未知API替换成成功。

仅两个selector字节和首份124字节快照使用已定位的原厂BSS清零条件；初值不是
活动快照。当前真实6042661b执行完成后，60427013的返回点、60427025的缓存复制
返回点各出现一次；622a084c的124字节与6229fc48一致，缓存时标为ffffffff。
尚未填完后续服务格式对象，不能提前让等待中的几何消费者使用这份中间状态。

## 接通的初始化依赖

|原厂片段|每个分支指令数|核对结果|
|---|---:|---|
|60419529|38|发布服务指针、两项回调及部分字段|
|6020d024，D0=0/1|164 / 4889|先清157个属性缓存槽，再注册；原147个指针不变，10个空槽保留NULL|
|6054c732..6054c7a5|20|相机状态RAM重置后缀，19处直接store；前置/后续外设初始化未执行|
|603fe086|138|16项halfword历史值和两个极值均为−32768，index为0|
|任务分发与producer前缀|4832|字段构造与缓存复制完成，停在格式模块就绪读取|

这些片段独立执行，只映射已审查store目标和有界数组，未知间隙仍未映射。157槽
清零和148次getter产生147个注册槽是原厂两个分支的不同范围；10个NULL槽触发
原厂属性查询回退，不能伪造成已注册指针。

历史中间结果保留：[请求首次进入回调](../../research/ep7/candidate-snapshot-request-frontier.json)、
[相机状态重置后](../../research/ep7/candidate-snapshot-camera-state-frontier.json)、
[补齐原厂空缓存槽后](../../research/ep7/candidate-snapshot-cache-frontier.json)、
[历史初始化后](../../research/ep7/candidate-snapshot-history-frontier.json)。前三处依次
停在62237252、622a0bcc、62295a90，当前报告在此基础上增加精确断言和字段复制证据。

## 仍需推进

就绪标志a2788ca8有两个直接写入来源：60556b1e的原厂重置置0，606bbffc在四个
helper完成后置1。60556934在0分支生成原厂缺省格式，在1分支调用6065e658。
后续需区分实际冷重置场景与模块完成初始化后的场景，不能直接填1宣称模块就绪，
也不能把0分支的缺省尺寸当作真实拍摄格式。

原几何构造栈保留，partial capture的27332字节不变，population、relay预处理和
worker尚未继续。S3整体、S4所有权/缓存/完整栈，以及S5完整更新器与恢复仍未通过；
安装资格没有变化。最终包继续复用fishcu流程，保留E-P7五组件及各自元数据。

## 复现

```sh
python3 /repo/tools/ep7_candidate_snapshot_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

预期两项snapshot_field_constructor_returned和snapshot_cache_copy_byte_identical为true，
snapshot_producer_completed为false，frontier读取a2788ca8，population_resumed=false。
