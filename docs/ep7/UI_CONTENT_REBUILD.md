# G4：独立 H/L 内容对象与原生类别重建

`ui_content` 已实现独立56字节内容对象、18槽专用 vtable、四处重建调用的桥，以及
分配失败回退和原生销毁接合。它填补 parent+80 的对象所有权层；后续
[UI session与viewer接合](UI_VIEWER_JOIN.md)已连接共享core及文本更新，真实输入资格
和 COLOR gating 尚未接合，H/L mask 仍由现有 initializer 设为禁用。
没有开启 renderer_ready、安装 hook、生成修改固件或执行相机代码。

## 修复的具体路径

原厂 `60e266a9` 先销毁 parent+80，再读取 selector 当前类别，只有0–3有创建分支。
4/5从 `60e2670d` 返回时 parent+80已清零，而 `60e26270`、`60e26697` 等转发路线
会直接解引用它。单独扩展 selector 或只增加 H/L 文本都不能解决这个问题。

本次对整个 main 的 CD/DD 相对 CALL 编码候选扫描找到了四处调用，补出前一节点
清单没有列出的 `60e269f0`。其上游从事件结构栈+22读取目标类别，多次调用 selector
导航方法后重建；事件结构的物理输入来源仍须继续核对，不能据此宣称 H/L 触屏可用。
没有找到包含完整原函数地址的绝对32位字面量。这是有限编码扫描，不是全部间接/
计算跳转、内存写入或控制流闭包证明。

|原厂 CALL 地址|已核对的调用位置|保存组 / caller frame|
|---|---|---|
|60e261d4|parent 初始化，selector 已创建|f0 / 28|
|60e26201|selector previous 回调之后|f0 / 28|
|60e26226|selector next 回调之后|f0 / 28|
|60e269f0|按事件目标类别导航之后|f0 / 28|

四处均转向同一12字节桥，继承原28字节帧：0–11留给被调函数，12–27是原调用
保存的 D2/D3/A2/A3；桥不另建帧。实际原函数入口保持不改，GCC veneer 以原 f0/28
调用它。既保留完整原厂重建，又避免修改入口后递归调用自己。

G6必须为该桥证明合法放置，入口需位于四个 signed16 CALL 距离的交集
`60e1e9f0..60e2e1d3`。这只是距离条件，不是该范围内有可用空洞的证明。

## 构造、回退与销毁

MVC 登记现在同时保存当前 content 指针、最后一次完成的类别和 busy 状态，目标
存储由64增至76字节。`ep7m_hold_content` 只接受本代已登记且关系未变化的 parent，
把 native allocation/destruction 覆盖在 busy 期间。匹配 parent/viewer/GUI 退出或
递归重建在释放对象前进入现有 quarantine。正常释放 hold 前重验对象关系和类别。
未知 parent 仍走原厂函数；本代关系已失效的 parent 不再转交原厂去使用未知对象。

类别4/5当前 mask 非零时，恢复最后完成的 selector+86和原厂 RAM `61fc26ae`，
保留旧 content。模块不写 mask；“mask允许导航”也不被宣称为 renderer 资格证明。
待真实 renderer/gating 接入后，才会有生产代码开放这两个位置。

从原厂类别进入 H/L 的路径先 scalar-new 56字节，清零全部新空间，再调用原厂
48字节 base initializer。该 leaf 还会清 `61fc1bbc`，保留这一原生初始化效果；
不能将它混同于另一输入门槛 `61fc1bac`。新对象前48字节是 native base，后8字节
是 MVC generation 和 category。它没有借用 stock S child、parent/viewer 尾部或 NVM。

分配失败不销毁旧 child，不改变 parent+80，也不调用原厂重建；两处类别索引恢复
到旧值。成功时，新对象初始化完成后才销毁旧内容并发布到 parent+80。H↔L复用同一
私有对象，只改私有类别。回到0–3调用完整原厂重建，保留原厂工厂与其失败语义；
**本批没有修复原厂类别工厂自身的低内存失败路径**。

新 vtable 中未接入的事件/值方法返回0，pointer 方法返回NULL，不调用 S 编辑
handler。+40是完整析构桥：先核对已登记的唯一私有 child 并撤销记录，再调用
原厂 base destructor `60dd50d8`，保持 A0=0 的默认 scalar-delete 约定。
未知/重复私有析构在读 child 前拒绝。parent 撤销后仍以永久保存的 GUI task/cohort
核对析构，不回头读取已经失效的 parent/selector。

析构桥自身32字节，C调用的0–11出参区与12处保存的对象参数分离。GCC dispose
veneer 按原厂协议先执行 virtual+40，再调用返回的可选 deallocator；A0=0时调用
`60a4ec17`。它没有把析构槽当成无副作用的“查询”。UI session close 已在后续
[显示节点](UI_VIEWER_JOIN.md)接入此撤销点。

## 原生符号和安装组

MVC cohort 现在要求原四个 entry/exit/destructor 表项和四个实际 CALL 编码同时匹配。
CALL 要求 opcode CD、保存组f0、帧28，符号扩展 displacement 后的目标等于桥地址。
它不修改任何表/指令，也不能代替冷启动安装排他、完整旁路审查或硬件 cache 同步。

|新增原生外部符号（省略 GCC 前导下划线）|原厂地址|
|---|---|
|ep7_stock_mvc_rebuild_initial_call_unresolved|60e261d4|
|ep7_stock_mvc_rebuild_previous_call_unresolved|60e26201|
|ep7_stock_mvc_rebuild_next_call_unresolved|60e26226|
|ep7_stock_mvc_rebuild_touch_call_unresolved|60e269f0，名称是候选路径标签，物理输入仍待核对|
|ep7_stock_selector_remembered_unresolved|61fc26ae，16位 RAM|
|ep7_stock_mvc_rebuild_unresolved|60e266a9|
|ep7_stock_mvc_scalar_new_unresolved|60a4ec03，CALL [],4|
|ep7_stock_mvc_scalar_delete_unresolved|60a4ec17，CALL [],4|
|ep7_stock_mvc_base_init_unresolved|60dd5083，leaf [],0|
|ep7_stock_mvc_base_destroy_unresolved|60dd50d8，leaf [],0|

其余符号沿用 [MVC 生命周期](UI_MVC_LIFETIME.md)、[selector 存储](UI_SELECTOR_STORAGE.md)
和当前任务桥。所有这些地址仍等待 G6 的来源、放置、重定位及安装绑定。

## 初始内容节点的定向验证

以下保留该节点的范围和尺寸；当前接合后的组合检查见[显示节点](UI_VIEWER_JOIN.md)。

- [原厂报告](../../research/ep7/ui-content-rebuild-current.json)：96条精确指令、
  一张18词 vtable、全 main 直接 CALL 候选扫描通过；没有 SHA 校验。
- [主机报告](../../research/ep7/ui-content-rebuild-host.json)：6组内容场景和复用的
  6组 MVC 场景，通过 strict/ASan/UBSan。覆盖默认禁用、malloc失败保留旧对象、
  成功时构造先于旧对象销毁、H/L复用、返回原厂、parent先销毁、重复析构、
  native边界重入、对象关系失效、第四处 CALL 帧错误和未知parent原厂委托。
  原生 allocator/析构为边界 mock，开启 mask 仅用于 fixture；没有相机接受性证据。
  初次检查修正了 fixture 的 longjmp 循环变量和 sanitizer 下短 CALL 标记布局，
  未关闭或放宽距离/内存检查。
- [目标报告](../../research/ep7/ui-content-rebuild-target.json)：13对象通过，24个
  外部符号全为实际原厂地址；43条新桥指令、18个 vtable 重定位核对通过。
  content C599字节/BSS8，桥加 vtable203字节；MVC C1987字节/BSS76，cohort204字节。
  rebuild C局部帧40、私有析构回调16；整条原厂调用链与中断总栈仍待 G6。

入口是 `ui_content/check.py`、`tools/ep7_ui_content_rebuild.py` 和目标检查器
`--ui-content-only`。`--ui-mvc-only` 也包括当前必需的 content/cohort 符号闭合。
UI session、同一runtime core和viewer/owner已在后续显示节点接合；下一项为真实
输入资格和 COLOR gating/禁用时焦点归一。G4、G6、G8仍未整体通过。
