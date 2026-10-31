# G1：新增原生读取的具体责任

2026-10-31。对照当前[原生绑定](../../prototypes/ep7_volatile_hl/controller_sidecar/native_binding.c)
和[39处CALL检查组](../../prototypes/ep7_volatile_hl/controller_sidecar/cohort.c)整理。
这是后续研究范围表，不是新增的通过结论；不降低G8的生命周期条件。

## 各读取点需要保护什么

|新增操作|真实原生读取|已有接合|尚须证明的区间/责任|
|---|---|---|---|
|fresh登记|刚返回node的+0 ID、+8 associated；固定池配置/引用计数；capture getter|三处3116返回桥，在caller发布node之前；只登记地址，不读capture的profile|创建器返回对象确实仍由当前caller持有；getter期间关联分配不能被未覆盖路径回收|
|sample / finish|已准入node的+0/+8；associated固定池；getter返回capture的+24053/+24083|三组填充返回桥、两个公共prewrite、token/epoch及busy检查|新增读取区间内node/capture不释放或换代；两个profile字节与该次population一致|
|立即source copy / 等待入队取值|associated+8 backlink、associated+0 ID，以及同一prefix/profile读取|602ac3de立即scope、602ac3f6入队前冻结值；固定slot及身份交叉检查|本次producer确实拥有该associated图像；backlink不是旧别名；所有影响这些字段/代际的销毁和写入被覆盖|
|capture release观察|原生registry row+12指针|6029be5d，释放pool handle前撤销所有匹配记录|该行在observer期间有效，其他retirement入口不能绕过撤销|
|associated回池观察|固定slot header引用计数|归零后、真正enqueue前的602973bc；固定池reset6029c692|覆盖同一池的重用入口；计数非零检查本身不产生锁|
|等待队列管理|固定manager的配置/count/index、固定backing中元素值|enqueue/pop/reset及3个service桥；前后状态与head核对；busy跨原生操作|队列不能经未覆盖入口并发修改；scope栈/任务存活成立|
|state / engine资格检查|state半字、固定17项callback/mask表、required mask|state提交、engine configure与workrecord pool reset前撤销|这些写入入口的完整覆盖和同一次检查期间的可见性；不是engine对象的引用计数|

`span()`仅检查非零、对齐和整数范围，不能证明分配extent或存活。`authorize()`与token
说明sidecar当前记录的资格，也不固定原生内存。固定associated backing能确定地址
范围，仍须区分该slot现在属于哪张图像。

## 现有保护能覆盖到哪里

`enter()`先确认已发布runtime、domain0/controller入口60289852及固定TCB/tid/stack，
再检查CALL组和busy。已接合销毁observer在外来任务、重入等失配时隔离，不继续原free。
busy只覆盖新增C读取和明确包围的队列操作，不覆盖整个原厂population/engine执行。
不匹配的非销毁准入永久关闭后续读取；这也不能撤销一个已开始的未接合原生free。

13个已列node free、capture release、associated回池/reset、population prewrite、
state和engine重建都有候选接合。**这份入口清单仍不是所有别名释放/重用的闭包**。
后续发现新调用边时，应先判断它是否能触及表中对象或身份字段，再决定是否补接合。

## 不再扩大的证明范围

- 冻结值进入等待ring后，正常pop只读固定队列数据并复制私有scope，不再读取旧node或
  capture。下游票据/job继续使用自己的值；无需为这份值延长原node到job完成。
- H/L不直接读取engine+64、workrecord[0]或type39描述符+8；这些原生指针的意义在于
  它们可能通向表中的释放/写入边。TOP三字副本与136字节下层描述符不构成H/L租约。
- node+4完成标志、坐标及capture其他曝光/时间字段不是本绑定的profile输入。
  只有其控制流进一步造成目标释放、重用、profile/身份变更时，才成为这张表的义务。
  延续[已有的局部写入分类](CAPTURE_LATE_MUTATIONS.md)，不要求整块capture恒定。
- 不从这些局部关系推出原厂所有callback唯一、所有mailbox永久存在或所有取消都已结束。
  与任务/消息存活有关的G2/G3条件仍由各自的实际接入承担。

后续[回调写入范围](CAPTURE_WRITE_WINDOWS.md)已执行602a334f及type39完成6029e8f1
的两个完整原生现场，确认所选路径仅写坐标/完成标志，不覆盖node+0/+8。这项局部
排除不覆盖其消息接收后的释放：source上游602ac1e1存在先发送event42、后立即copy
或等待入队的路线，仍要审查该区间及backlink身份。

下一段优先审查这些消息边，以及13个node free是否覆盖对应图像的所有已识别释放边。
只在新增结论涉及的原生窗口做验证；本表没有生产代码变化，不重跑主机或107对象编译。
放置、启动、cache和全栈仍另属G6。
