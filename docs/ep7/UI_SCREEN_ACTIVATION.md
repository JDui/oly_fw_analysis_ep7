# G4：request278 显示切换与独立文本资源

已定位目标显示容器在原厂 screen manager 中的来源和切换顺序，并实现112字节的
独立文本资源构造器。它复用原厂字体/样式/布局，不写原厂描述符；尚未安装显示切换
或撤销 hook，也没有显示新文本。

## 三个编号不能混用

|含义|值及证据|
|---|---|
|显示请求|**278**，分发表 `60fa9e04 + 278*4` 指向 `60d389ee`|
|widget factory type|`6111`，该分支把D0设为24849并调用 `60d337b2`|
|原厂 owner descriptor ID|`0112`（274），描述符 `60fa8cf4` 的第二个halfword|

最终 service vtable `60faaab4` 的 +784=`60d37b53`。事件处理器 `60cff6ef` 将
D1中的显示请求转入D0，然后调用这个方法。其完整入口自建64字节帧；内部
`60d37b58` 另有原厂直接CALL入口，不能把两个入口的栈责任混同。

screen manager 使用 service+2032 作为重入标记；两字节 service+1378/+1379
记录context6的两个分配槽。它选一个空槽并设置service allocator selection，
进入request278分支，使用descriptor `60fa8cf4` 创建1360字节的目标owner。
这个busy字节不是跨任务锁；本批没有据此关闭GUI串行性要求。

## 新旧 owner 的时间关系

1. factory返回的new owner保存到D2；NULL时失败返回0。
2. `60d38a6f → 60cffbe0` 把new owner写入 **service+416**，返回old owner，保存到A3。
3. 对new owner调用+148进行bind/子控件填充，再调用+364首次绘制。
4. 如果有old owner，切到其allocator context，依次调用+368、+152、+0和返回的free。
5. 恢复service+416=new owner，释放old owner对应的context6槽。
6. 调用new owner+76，清除service+2032，返回1。

因此，new owner的bind回调期间，old owner仍然存活。若在bind完成处登记new owner，
随后的old cleanup只能撤销匹配old owner的记录，不能无条件清掉“当前owner”。
单槽实现的更小入口选择是：显示切换调用前撤销旧显示准入，等**完整request278调用
返回1后**再登记service+416；同时覆盖目标owner的bulk cleanup和析构，以处理其他
退出路径。该方案不要求在新旧owner并存期间持有两个已准入的显示句柄。

这仍是待实现的具体接合方案。原厂manager没有逐项检查factory初始化和bind的返回，
其返回1也不是所有child资源成功的证据；登记时必须保留实际来源、当前service/owner
关系、已完成阶段和列表资格。该request编号还不能直接当作MVC parent/session或
H/L输入资格，后两者有各自的生命周期。

## 专用文本资源构造器

`text_lifecycle/native_resource.c` 从已核对的原厂index53复制94字节descriptor和
16字节双布局；使用独立的 `struct ep7_text_resource`，布局位置为该对象+96。
只有descriptor+2/+3的ID变为 `0x7e10`，+4..7改为自己的layout指针；descriptor
其余字段保持原厂值，最后两个padding字节置0。静态断言要求32位指针及112字节extent。

|链接符号|原厂地址/范围|
|---|---|
|`_ep7_stock_hl_text_descriptor_unresolved`|`61032ea8`，94字节|
|`_ep7_stock_hl_text_layouts_unresolved`|`61031b84`，16字节|

保留font1、style、flags9和原厂空导航表 `61030a5c`。双布局为
`(20,435,600,40)` / `(20,435,680,40)`，目前只是有依据的初始几何；尚未证明与H/L
页面其他元素的遮挡、缩放、绘制顺序和实际字形效果。构造器不会自动挂接或使控件可见。
实际创建继续使用上一节点接好的当前列表ID冲突检查。

调用者必须先拥有独立、对齐的112字节存储，并由安装流程验证支持版本和源映像地址；
准备之后不得移动这个对象，或在原生调用可能读取期间改写它。构造器是数据准备原语，
不能用其存在代替 owner qualifier、资源存活、安装顺序或 renderer_ready 条件。

## 验证边界

[当前原厂证据](../../research/ep7/ui-screen-activation-current.json)核对创建/切换顺序的
100条精确指令、3项分派数据，并复用既有资源解析器核对所选源及两组布局。
[目标对象报告](../../research/ep7/text-resource-target.json)包含17个对象，剩余13个符号
为11个原厂函数和2个原厂数据地址；构造器72字节、局部栈8字节。没有原生链接或执行。

本次只对新的静态关系和目标对象做检查，没有为简单字节复制另写镜像实现式测试，
也没有重跑未改动的16项主机生命周期测试。沿用上一节点通过的strict/ASan/UBSan
结果。未做SHA、整体固件编译或相机试验。

下一步实现完整screen manager调用前/后桥与匹配owner的撤销，接入资源和已有native
text lifecycle，再连接MVC的H/L viewer及输入资格。G4/G6/G8仍未整体通过。
