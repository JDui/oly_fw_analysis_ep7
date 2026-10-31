# G4：共享 core 的 UI session 与 viewer/owner 接合

当前显示候选链已具体连接：完整原厂viewer返回 → 核对本代MVC/content → 从已发布
runtime的同一个core取得H/L frame → 更新已捕获且仍在父列表中的专用text child。
request278的owner晚到时，也会从完整manager返回处再尝试这条链。H/L mask仍禁用；
真实输入provider、COLOR gating及失效归一未完成，没有相机显示、安装或固件构建结果。

## 两个完成点

原厂viewer `60e26ab0` 自建36字节帧，从parent virtual+28取得selector/content，
写viewer+388/+392；selector类别写halfword+396，property111写32位+400。随后提交
property229/334字节数据；显示请求改变时调用 `60ea12ca` 请求278。类别4/5跳过
原厂0–3专用绘制，仍保留原厂公共处理和显示请求。

`60ea12ca` 把请求放进0x1100事件，`60d0ffb4` 构造28字节消息，`60d0ffe0` 复制到
32字节事件环槽并提交写游标 `6246a6f2`。viewer返回不证明screen manager已完成，
入队返回也不是交付保证。因此接合不等待或猜测完成时间：

1. viewer完整方法前取得MVC hold，原厂返回后释放hold，再尝试刷新文本。
2. GUI041d完整入口登记MVC后尝试刷新；早于全局发布的首次draw只保留原厂行为，
   不从半成品graph取得frame。
3. 完整request278 manager返回、text attach/bind/set成功后尝试刷新。owner晚于
   MVC draw时使用已完成的缓存；早于该draw时等待viewer完成点。
4. 缓存中的selector/content/category必须与MVC完成记录相同。再读取实际property111，
   完整32位mode必须是54/55/56/64，并等于viewer+400。未知值的低16位恰好为54不能
   准入；也不使用调用者传入的模式开关。

两次值相等不是跨任务模式锁证明。事件/GUI串行性和完整旁路闭包仍在G6，输入provider
仍须在自己的真实事件作用域内建立资格。公共chrome仍只有原厂项目；新文字的可见性、
遮挡、原生触摸行为和LCD呈现尚未实机验收。

## 会话与共享 core

`ui_model/model.c` 经现有 `ep7r_get/ep7r_accepting` 绑定 `runtime->boot->core`，复用
`ep7p_ui_ops`，没有第二套H/L设置或core重置。首次绑定后runtime/core地址变化进入
quarantine；未发布、停止或不健康的runtime不能产生准入frame。slot的唯一存储定义
从contexts.c移到runtime.c，显示与pipeline共用同一实例，发布规则不变。

永久68字节model使用slot0和独立32位serial。同一个MVC内退出H/L再进入也要取得新
UI token，旧token不能编辑新会话；serial耗尽后不再open。H↔L及COLOR profile切换
使用sync，保留独立sector/ALL选择。原厂类别、unsupported mode、MVC撤销及私有child
销毁会close session，但不清core的H/L值或已有图像快照。poll争用只使本次frame不可用，
保留session/focus；UI路径不睡眠。主机normalized edit不是实际拨轮输入已经绑定。

## owner 更新和撤销

`ep7u_present` 先核对捕获owner的active/display_ready、固定GUI task、service/cohort和
service+416，再检查原owner形状、context6槽及列表。以独立ID7e10查询真实父列表，只有
返回相同attached child才读取其type8010、vtable60faec7c、ID、parent及allocator context。
关系变化或setter失败会锁存此owner不可显示，不创建第二个child；原parent继续负责
attached child的销毁。

更新期间保持text.busy，保存原allocator selection、切到owner context，调用既有
set_text桥后恢复选择。MVC hold覆盖mode读取、frame复制和文本更新。递归screen切换、
匹配MVC释放或同viewer重入会在原生释放/绘制前停止；已失效的登记viewer也不会委托
原厂去使用未知graph。

setter `60d4c9df` 对相同字符串返回1；变化时复制UTF16，调用 `60d04feb` 进入原厂
刷新流程，并清除+56/+60缓存。当前已核对其4096/8192标志方法和后续矩形通知调用，
没有另造重绘队列。分配失败返回0，可能已经释放旧字符串，因此关闭owner显示资格，
不能承诺低内存失败保留旧字符串或旧像素。

MVC撤销在busy保护内先close session、清文本，再忘记graph并继续原厂free；文本回调
不能趁parent身份已忘记绕过重入保护。owner切换/销毁及MVC hold开始即撤销旧receipt。
成功更新才写新的32字节receipt：MVC/UI/owner三个generation、viewer/child、mode/category。
receipt只表示setter接受，不是独立input lease或完整renderer_ready。

## 原生桥和验证

|接入|原厂地址及帧|新桥约束|
|---|---|---|
|viewer vtable61189ba8+0|60e26ab0，自身36|桥自身56；保留A0/D0/D1/A1输入/返回，held在+28、viewer在+32|
|property service getter|607f9062，caller4|桥自身20；+12输出初始化0，D0=111、A1为输出地址，调用virtual+8；NULL getter返回mode0|

新外部符号为 `ep7_stock_mvc_viewer_draw_unresolved` 和
`ep7_stock_property_service_unresolved`。MVC cohort增加实际viewer+0匹配，连同既有四
表项和四CALL核对；匹配不能代替冷启动安装、合法放置、cache和GUI排他。

- [原厂报告](../../research/ep7/ui-viewer-join-current.json)：115条指令、1个vtable词，
  覆盖缓存来源、property111、request278入队和setter刷新链；没有SHA。
- [组合主机报告](../../research/ep7/ui-viewer-join-host.json)：7组新增，复用6组MVC及
  6组content，strict/ASan/UBSan通过。真实core/bootstrap/runtime/session、MVC/content/
  owner/text lifecycle C参与；覆盖两种完成顺序、失败切页恢复、同core编辑/冻结快照、
  H/L/profile切换、同MVC重新进入、未发布/停止/非法mode/poll争用、owner失效、setter
  失败、重入及serial耗尽。native任务/分配/property/队列/绘制是mock，mask仅fixture开启。
- [目标对象报告](../../research/ep7/ui-viewer-join-target.json)：41对象、44个实际原厂
  外部符号，当前显示组合软件符号闭合；不包括未完成的input provider。viewer桥71字节/
  27指令，mode桥36字节/15指令；model512字节+BSS68，viewer C577字节+BSS32，
  owner C2275字节+BSS196。refresh/frame/present局部帧104/52/44；原厂被调链及中断
  总栈仍待G6。没有link、目标执行或整体固件编译。

入口：`ui_render/check.py`、`tools/ep7_ui_viewer_join.py`、目标检查器`--ui-viewer-only`。
当前owner/MVC/content目标模式也包括已接合依赖；早期独立host fixture在范围外mock
新回调。下一项是实际事件域/完整拨轮delta、input provider、COLOR gating和禁用归一，
随后与G1/G2/G3/G6汇合。G4/G6/G8仍未整体通过。
