# E-P7 GUI 编辑、原生文字与共享冻结

2026-11-01。候选004的GUI输入、H/L内容、显示确认和共享core冻结现已在同一条件
上下文接通。新增GUI链443,699条指令，46次原生私有锁操作全部使用ID133并返回0；
观察最大栈深820B。固件及fishcu五组件研究包未变，无SHA或相机操作。

## 结果

复用实际132个静态信号量初始化、原create133与runtime发布过程，跳过该旧工具
已覆盖的edit/rollback测试。切换到显式GUI任务现场后，原文字控件创建完整执行。
GUI模型通过实际begin/complete和rebuild调用取得同一runtime，没有直接填私有
MVC、session、receipt或H/L设置。

|实际事件/操作|原生文字setter的结果|共享core结果|
|---|---|---|
|进入H|H 01 +0|COLOR1初值0|
|9032，完整delta +3|H 01 +3|H[0]=3|
|同一dispatch内重投|仍H 01 +3|拒绝，未重复改为6|
|9031，完整delta +2|H 03 +0|选择第3色区|
|9032，完整delta −2|H 03 -2|H[2]=−2|
|切换L|L 03 +0|保留同一56B内容对象与色区|
|9032，完整delta −4|L 03 -4|L[2]=−4|

每次检查原viewer写出的selector/content/category/mode缓存、匹配的MVC/session/
owner三项generation、receipt和H/L masks。完整原预处理、原事件归一、实际安装
的拨轮JMP与候选dispatch包装均执行。engine模型在原container指令60e4d0f5进入，
真实vtable lookup/CALLS60e4d0ff调用候选parent桥，保留原返回PC60e4d101；changed
后执行候选viewer桥和原viewer60e26ab0。模型不直接调用core编辑API。

最后通过同一core的实际capture API，以raw11/selector1冻结COLOR1，25B结果为
profile0、H=[3,0,−2,0…]、L=[0,0,−4,0…]，其他色区逐字节为0。该结果连接GUI到
核心冻结；它不替代另行完成的capture/node关联或worker/CPU证据，也不证明照片像素。

GUI exit实际撤销session和receipt、遗忘对象图；随后实际H/L内容destructor/free
和原文字owner cleanup回收全部模型分配。撤去container/parent/selector/viewer/
masks映射后，迟到refresh没有对象访问或新分配，冻结结果保持不变。

## 模型范围

复用此前owner的request278完成、任务/TCB、分配/释放、绘制通知及单GUI锁契约。
MVC构造边界提供228B container、100B parent、124B selector、408B viewer和12B
masks；初始category2且content=NULL。原stock内容创建、替换前的stock销毁和整个
GUI041d创建链未执行；6项selector也属于该对象图输入，不将此例描述为完整原生
COLOR界面进入证明。

property服务读入口实际执行；虚拟读方法输入111=54、426=0。轮值服务和日志为
模型；engine本体由上述投递与changed后draw契约代替。原viewer缓存和分类分支
实际执行，公共header准备60e26c03、输出60ea4c1c/60cfeca9仍是绘制边界，因此没有
LCD、布局或物理拨轮方向的验收结论。

两把GUI锁仍为单任务模型；core的poll/signal133是真实原厂机器码。820B包含模型
选定的256B engine投递帧，不是原engine、renderer或IRQ完整上界。完整并发、代码/
RAM驻留、物理更新入口和独立恢复继续保留，不撤销包的不可安装标记。

本次CLI直接exit0。后续只补充了报告中初始NULL内容的边界说明，未重复运行已通过
案例。新增工具复用owner/native-input和static-kernel工具，未另建模拟器或编译环境。

[工具](../../tools/ep7_candidate_ui_editor_sim.py) ·
[机器报告](../../research/ep7/candidate-ui-editor-sim.json)。
