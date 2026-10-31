# G4：GUI041d 的 MVC 对象来源与退出接合

`ui_mvc` 已实现 GUI 完整入口之后的 container/parent/viewer/selector 登记，以及
GUI exit、parent destructor、viewer destructor 之前的匹配撤销。后续
[H/L 内容重建](UI_CONTENT_REBUILD.md)已在该来源内加入 content/index 登记和 busy
保护；[显示节点](UI_VIEWER_JOIN.md)已接入共享core的frame及native text更新。
尚未开放 H/L mask、替换输入资格provider或验证相机显示。

## 在完整入口返回后登记

原厂 `60e5dae9` 用 group8/key463 调用 `60e4cea8`，再把返回 A0 写入 `61fc436c`。
当前 key463 描述符为 `(463,0x34,0,0x84,0,0)`，没有动态修改该行的 callback。
实际调用链分配228字节 container、100字节 parent、124字节 selector 和408字节
viewer。container+0/+4 为 parent/viewer，+8/+12 是工厂编号0x34/0x84。
viewer 构造参数是含 parent 的8字节参数块，**不是直接传 parent 指针**；构造器
把参数块首 word 写到 viewer+384。

container 构造函数调用 viewer virtual0 完成首次 draw，之后才返回 container，
最外层 GUI entry 再发布全局。因此，仅在 viewer 工厂返回处登记，仍不足以证明
全局当前页面已发布。这里选择完整 GUI entry 返回后，把其原 A0 作为来源，核对它
等于实际全局，再核对工厂编号、parent/viewer vtable、viewer+384、parent+76 和
selector ID193/布局。来源是这次刚完成的调用，字段比较不作为任意指针检测器。

既能登记原4项 selector，也能登记上一批扩展后的6项；后者的 values 必须指向
自有 `ep7s_categories`。登记同时固定 mask 指针和 count，不追随后来替换的数组。
4项回退仍可保留原厂页面，本模块不会因记录成功而允许 H/L。

## 代际与撤销

永久76字节目标状态（原节点64字节，内容接合增加12字节）固定实际 GUI task 的
tid/domain/TCB/entry/stack。首次完整
构造登记 generation=1，此后成功的新构造递增；最大值后停止新登记。存储不允许
运行中重置或移动，TCB 比较不替代排他或同址任务重建证明。

`ep7m_current` 只供同一串行 GUI 操作使用，检查当前全局、container 两个对象、
两类 vtable、selector 关系/count/mask以及已完成重建的 content 指针。任何关系变化都使本代 `invalidated` 锁存；
把旧指针比特写回来不会恢复资格。必须经过撤销和新的完整构造，获得新 generation。
该返回值仍不是可跨调用、跨线程保存的 lease。

原厂退出顺序是参数块释放，然后 parent 析构/释放、viewer 析构/释放、container
释放，最后清全局。因此要在 GUI exit 开头撤销；另两个直接析构入口用于覆盖匹配
对象独立退出。parent 先销毁时也立即撤销 viewer 记录，避免 viewer+384 被继续读取。
无关对象的析构不清当前记录；尚未登记的构造临时对象可以走自己的原厂失败清理。

有记录时的再次 GUI entry、重入 GUI entry/exit、已开始后的 task/cohort 不一致，
以及 exit 前全局不再匹配，复用现有 quarantine 实现阻止继续分配或销毁。此行为
仅在 host 中用 longjmp 建模；原生 exception/debugger 行为仍未执行验证。

## 析构方法不是无副作用的查询

parent/child virtual+40 和 viewer virtual+4 **已经执行析构**，A0 返回可选的
deallocator；A0非空时再调用它，A0=0时调用默认 `60a4ec17`。例如 selector 的+40
先释放 mask，parent 的+40先销毁两个 child。新 H/L child 不能只在该槽返回一个
portable close 函数地址、却漏掉该层应完成的析构责任。旧接口文档已明确这一点。

|安装位置|原厂完整方法|原厂自身帧|新桥自身帧|
|---|---|---:|---:|
|611a3b50，GUI entry|60e5dae9|4|48|
|611a3bc4，GUI exit|60e5db01|8|48|
|6118957c+40，parent destructor|60e26130|28|48|
|61189ba8+4，viewer destructor|60e26a7c|8|48|

桥保留原输入与需要的返回寄存器，以 CALL `[],0` 调完整自建帧入口。cohort 读取
这四个实际词；当前还要求[四处重建 CALL](UI_CONTENT_REBUILD.md)以及
[viewer virtual0](UI_VIEWER_JOIN.md)匹配。没有写表、
放置新地址或把表项相等当作全局安装证明。其他构造/直接
销毁/selector reload 路径、GUI 排他和 heap 存活仍由 G6 关闭，当前不可安装。

## 初始 MVC 节点证据

以下报告保留初始实现的范围和尺寸；当前内容接合后的 C/目标尺寸及回归结果见
[显示节点报告](UI_VIEWER_JOIN.md)，不能把旧尺寸当成当前构建结果。

- [原厂检查](../../research/ep7/ui-mvc-lifetime-current.json)：98条精确指令、8项
  表数据，确认构造/首次draw/发布和 parent-before-viewer 退出；selector 分配证据
  沿用上一批。未做 SHA 或执行旧工具的哈希入口。
- [主机检查](../../research/ep7/ui-mvc-lifetime-host.json)：6组 strict/ASan/UBSan
  通过，运行实际 lifetime/cohort C，覆盖未安装拒绝、4/6项捕获、来源不匹配、
  先撤销再释放、地址复用、关系变化锁存、错误task/cohort、重入及generation耗尽。
  原厂构造/draw/free是边界fixture，未进行原生执行。
- [目标检查](../../research/ep7/ui-mvc-lifetime-target.json)：11对象通过；lifetime
  1692字节代码/64字节BSS，cohort66字节，四桥183字节/65指令/9重定位。
  begin/complete/current 局部帧36/32/20；总栈还需原厂被调链与中断预算。
  14个外部符号均为实际原厂函数/数据地址。首次目标检查器的语法和局部变量冲突已
  修复后重新通过，没有因检查器失败跳过验证。

入口：`ui_mvc/check.py`、`tools/ep7_ui_mvc_lifetime.py` 和目标检查器
`--ui-mvc-only`。没有整体固件编译或相机运行。H/L content/rebuild候选已接入；
viewer和UI session已接合；下一项是实际输入资格与COLOR gating。
