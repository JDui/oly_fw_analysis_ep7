# E-P7 启动/恢复公开资料与 fishcu 方案复用

2026-11-01。用户要求网上查找、优先复用现有方案，并允许更积极地推进实验版本。
本次判断取代此前“必须先获得完整启动 ROM 和独立恢复证明才能继续”的项目门槛。
完整恢复保证不能靠软件模拟补出；未知项保留为台架风险，不再阻止减少改动和制作候选。
本次没有相机写入授权，也没有执行相机操作。

## 核验到的公开资料

|来源|能支持的结论|不能据此推导|
|---|---|---|
|[fishcu alpha-20261017](https://github.com/fishcu/oly_fw_analysis/releases/tag/alpha-20261017) 与 [安装说明](https://github.com/fishcu/oly_fw_analysis/blob/alpha-20261017/releases/alpha-20261017/INSTALLATION.md)|PEN-F 项目机实际安装、原厂恢复、再次安装；原厂恢复包沿用相同更新流程|任意损坏均可恢复；PEN-F 按键、E122 文件名或两组件包适用于 E-P7|
|[fishcu RECOVERY](https://github.com/fishcu/oly_fw_analysis/blob/main/docs/boot/pen-f/RECOVERY.md)|区分软件 SD 更新入口、实机观察及独立恢复；没有宣称不可破坏的 ROM 救援或普遍回滚|独立于 main 的 E-P7 救砖已经证明|
|[fishcu CODE_SPACE](https://github.com/fishcu/oly_fw_analysis/blob/main/docs/safety/CODE_SPACE.md) 与 [editor_storage/layout.ld](https://github.com/fishcu/oly_fw_analysis/blob/main/patches/hsl/pen-f/src/editor_storage/layout.ld)|已加载段的空白尾部放代码/可变状态；H/L 行与 axis 使用 uncached 别名；保留有限归属证据的边界|FF 自动等于无人使用；物理缓存、所有 DMA 或后续重加载全部安全|
|[E-P7 改机作者的一手报告](https://www.reddit.com/r/M43/comments/1xgjfz0/first_steps_to_homebrew_firmware_on_ep7_i_want_to/)|报告修改资源组件帮助文字并成功刷入；回复称未找到恢复模式|修改 main 后仍能恢复，或独立启动路径已逆向完成|
|[azqeurio dbv0.3.0](https://github.com/azqeurio/om-c-firmware/releases/tag/dbv0.3.0)|声明 E-P7 快门/AF/按键增强；有多个其他机型实测记录|E-P7 实测已完成。该版本测试列表未含 E-P7，当前 main 树仅 README，无实现源码可直接复用|

检索包括 E-P7/EP7 bootloader、recovery、E1429999、SD 更新等组合。官方公开用户
资料给出的是正常更新途径；本轮未找到可核验的 E-P7 启动 ROM、维修刷写或独立救援
说明。“未找到”不代表不存在。OFU 页面访问返回 403，没有据搜索摘要推定其实施细节。

fishcu 的实际推进方法是有界检查加实验性真机验收，并提供原厂恢复包及诚实的限制。
我们复用这套工程方法和现有容器实现；不会把其他机型的成功写成 E-P7 的保证。

## 具体复用：原厂加载区初始化私有状态

fishcu 的 PEN-F storage 链接脚本把 `.hsl_axis` 放在 6069b7b8，访问地址 a069b7b8；
transport rows 在 6069b590，访问地址 a069b590。其 `.persist_source` 自带零初始化。
复用的是“加载镜像承载初始状态、统一 uncached 访问”的办法，地址重新按 E-P7 选取。

新候选设计：

|区域|地址|含义|
|---|---|---|
|代码 0|60048040..6004dc00|缩小原候选 bank0 上界，禁止与状态重叠|
|状态镜像|6004dc00..6004fc00|原厂输入全 FF；输出为 8192 个零字节|
|状态访问|a004dc00..a004fc00|所有 C BSS 符号链接在这一 uncached 别名|
|代码 1|600c8040..600cffc0|沿用原候选 bank1|

GNU 链接器生成 `.ep7_private`，VMA=a004dc00、LMA=6004dc00，包含 BSS 和零填充。
复用 objdump/objcopy 检查并提取，不引入新 ELF 解析器。原厂早期复制
60030000..600d0800 → a0030000 同时装入代码和零状态；镜像内存储初值，不再运行
新增清零器。实际 ELF、原厂输入、合成镜像和可写状态边界逐字节核对，不做 SHA。

因此删除安装项 600201fe、600229b9、60022c28：整个启动前缀保持原厂字节，CPU2
大池保持 32 槽，私有状态不再占末槽。冷清零汇编仅留作旧候选历史，不再参与构建。
四 COLOR 的易失 H/L、色轮编辑、捕获冻结和照片 CPU 处理路径保留。

## 本轮有限验证与后续出口

1. 重新编译/链接当前 106 个源文件，检查 98 项补丁、两个代码段及一个初始化状态段。
   源文件清单和链接布局变化，整编一次比增加跨清单对象复用机制更直接。
2. 使用既有 GNU 模拟器：加载区从毒值开始，执行原厂 loader；检查代码与 8 KiB 零状态
   真正来自新镜像，未用单独清零成功桩。缓存别名在此为明确的共享内存模型。
3. 在新地址上复用已有生产 semaphore133、GUI 编辑/冻结、worker 处理/释放探针；
   针对重定位验证，不重新展开未修改的 ISP、所有原厂初始化或完整 111 MB mode2 运行。
4. 按 fishcu parse → replace_payload → reconstruct 生成五组件包，保留全部独立版本。
   单独报告实验包资格、实际硬件未知项和原厂恢复参考的适用范围。

仍待真机验证的内容包括物理 SD 入口、冷启动/缓存/次核行为、显示、实际照片、全栈
余量以及实际故障后的恢复。已知加载/写区间检查只排除已列出的冲突，不是穷尽归属证明。
再次加载同一早期区域会重置状态；首版只承诺冷启动后的易失值，不宣称运行中任意重载安全。
