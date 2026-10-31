# G4：复用原厂 selector，准备实际六项存储

`ui_selector` 已实现 ID193 原厂 initializer 完整返回后的存储扩展。新的六个值是
`[0,1,2,3,4,5]`，有实际12字节 mask 分配；H/L 两项初始 mask=1，仍不可选。
本批不开放 H/L 页面，也不把 count=6 当作已实现内容对象或 viewer。

## 复用原有分配与导航

factory1 表项 `61140364 → 60dde1b4` 分配124字节 selector，构造函数
`60dde2fa` 安装 vtable `6114f7e4`，随后调用 `60dde690` 查找 ID initializer。
ID193 的方法词在 `6114f334`，原值为 `60de150c`。该 initializer 调用原厂 loader，
从 `6114efa0` 读 count4/values6114e050，准备8字节 mask、记忆索引和 prev/next 回调。
原厂 list descriptor、记忆索引、callback 和 stock category 0..3 的值均继续复用。

新桥首先调用完整原 initializer，再交给私有 post-boundary C；它不是通用的任意
selector 指针升级 API。C 要求实际 initializer 词已指向本桥、当前是 GUI task，
并核对刚完成对象的 ID、vtable、count4、index<4、原 values、范围0..3与两个回调。
来源与124字节存活仍来自这个构造调用，不是字段比较自动证明的。

扩展只做以下变动：

1. 用原厂 mask allocator `60a4ec0d` 申请12字节；NULL时返回，原对象逐字节保留。
2. 复制旧4个 mask，保留原有禁用状态；第4/5项置1，值数组放在自有永久只读存储。
3. 更新对象+88 mask、+92 values、+106上界5、+84 count6；索引与回调保持。
4. 用原厂数组释放入口 `60a4ec21` 释放旧8字节 mask。原厂 selector 析构函数
   `60dde221` 本来就释放+88，因此后续拥有的是新12字节数组，无需另一套析构算法。

临时峰值多12字节，完成后 mask 净增4字节；独立值数组12字节。原厂 prev/next
按实际 count 遍历、非零 mask 跳过，仍调用 `60dde357/60dde3aa`，不新增导航算法。
存储发布与旧数组释放要求同一串行构造区间，不能用于并发读写的任意 live reload。

## 失败与尚未接合的边界

此处保证的是**新增12字节分配失败**时退回原4项。原厂 loader 对它自己的8字节
mask 分配没有 NULL 检查，正 count 时会直接写零；本批没有修复该既有路径，也
没有证明系统永不耗尽。原厂初始化没有正常返回时，新 C 根本不会执行。

当前没有改 initializer 表、原厂 descriptor 或固件，没有 category4/5 内容对象、
public54/55/56/64 gating、viewer 绑定或输入准入。后续必须在真实 MVC lifetime 内
绑定六项 selector、H/L child 和已显示的 text viewer，才允许将新 mask 清零；离开
COLOR/关闭页面/失败时还须禁用并归一焦点。不能以这个存储模块开启 `renderer_ready`。

G6 还须关闭其他直接 initializer/reload 调用、GUI 排他与 heap 生命周期，并安置
新常量和代码。方法词匹配只证明观察到那个值，不替代完整安装组和生命周期证据。

## 验证

- [原厂检查](../../research/ep7/ui-selector-storage-current.json)：81条精确指令、
  5项工厂/initializer/descriptor/析构数据，覆盖新增依赖和原厂 mask 路径。
- [主机检查](../../research/ep7/ui-selector-storage-host.json)：4组 strict 与
  ASan/UBSan，通过实际扩展 C 验证资格检查前拒绝、分配失败全对象不变、保留旧
  mask/索引/回调且先发布后回收、拒绝重复/不支持状态。原厂函数和任务为 fixture。
- [目标检查](../../research/ep7/ui-selector-storage-target.json)：7对象通过；扩展
  C与只读值合计531字节、局部帧44；3个桥76字节、25条指令、4项重定位。
  initializer桥自身56字节帧，原方法自建12；数组调用各使用原厂要求的4字节帧。
  保留原 initializer 的 A0/D0/D1/A1 返回。5个剩余符号均为实际原厂地址。

检查入口：`ui_selector/check.py`、`tools/ep7_ui_selector_storage.py`、目标检查器
`--ui-selector-only`。初次检查的 include 路径和新模式反汇编分支漏接已修复后重跑；
最终结果均通过。没有 SHA、原生执行、导航真机验收或整体固件编译。
