# E-P7 1100 原生曲线页与单帧 HDR 挂点

2026-11-07，使用 015 decoded main 运行原生 GUI 事件探针，并与原厂 1100 指令窗口和表项对照。此处只记录原生路径和候选方案，固件中尚未接入 HDR 子页。

## 曲线 owner 与设置作用域

- 机器 4／状态 29 的入口 `0x60e5dae9` 将构造完成的 GUI041d container 发布到 `0x61fc436c`。container 的 +0／+4 为 parent／viewer，原生 vtable 分别为 `0x6118957c`／`0x61189ba8`。viewer+384 保存 parent。状态退出 `0x60e5db01` 销毁 container 并清空全局。
- parent+76 为 selector，半字 +86 为类别索引。曲线是原厂类别 3，parent+80 为内容。重建 `0x60e266a9` 先释放旧内容，类别 3 的 `0x60e26774` 以设置 ID 383 构造工厂 14。实际分配经 `0x60df005a` 请求 240 字节，构造入口 `0x60df008b` 安装 `0x61159ea8`。此 vtable 也用于 `0x60def0f4` 创建的另一类 Direct_Actuator，单独检查 vtable 会误接管。
- 原生曲线子控件 +216 是 ROM 行，半字 +220 是页数 2，+222 是当前页 0／1，+236 是构造设置 ID。INFO 原厂曲线分支测试 +236=383 或 893。GUI041d 类别 3 直接构造 383。扩展作用域应核对当前模式和 ROM 行，并确保收到输入的就是当期 parent+80。不要把 selector 类别增到 4 或将 +222 改为 2。
- 构造器 `0x60df00e1–0x60df0160` 根据属性 111 选择下表。每行 56 字节，按两页各七个 32 位字段排列。第 0 页为 `SH, HL, SH, HL, 3200, SH, HL`，第 1 页为 `MID, MID, MID, MID, 3200, MID, MID`。刷新 `0x60defe96` 由当前页更新子控件的属性选择，包含 +208／+212 的拨轮目标。

| 原厂作用域 | 公开模式 111 | ROM 行 | HL / MID / SH |
| --- | ---: | --- | --- |
| 普通共享 | 其余 | `0x611595a8` | 891 / 892 / 893 |
| COLOR1 | 54 | `0x611595e0` | 963 / 964 / 965 |
| COLOR2 | 55 | `0x61159618` | 966 / 967 / 968 |
| COLOR3 | 56 | `0x61159650` | 969 / 970 / 971 |
| COLOR4 | 64 | `0x61159688` | 1672 / 1673 / 1674 |
| MONO1 | 57 | `0x611596c0` | 998 / 999 / 1000 |
| MONO2 | 58 | `0x611596f8` | 1001 / 1002 / 1003 |
| MONO3 | 59 | `0x61159730` | 1004 / 1005 / 1006 |
| MONO4 | 65 | `0x61159768` | 1675 / 1676 / 1677 |

## 实际事件链

机器描述符 `0x611a3bc8`，事件表 `0x611a2888`。下列已核对事件在状态 29 都进入 handler 137 `0x60e5da87`，继而经过 `0x60e4d032` 调用 container 持有的 parent。原厂表无 0x9016 或 0x903e 直达项。

| 输入 | 状态 29 表项 | 作用 |
| --- | --- | --- |
| `0x9014` INFO | `0x611a2f6e` | `0x60dd55bb` 检查 modal 全局 `0x61fc1bac=0`，从 parent virtual+68 的 `0x60e26439` 转给 child。子控件 `0x60defafe` 使用 hash 表 `0x61159e28`，`0x61159e74` 指向 `0x60defcd8`。原厂根据属性 1088 将 +222 切换到 1 或 0，调用 `0x60defe96`、`0x60deffad`，再写 1088 为 694 或 384。父层和子层之后丢弃队列中的同类输入。 |
| `0x9015` INFO 释放 | `0x611a2f8b` | 经相同曲线子控件，未进入切页分支。 |
| `0x9031` 拨轮 | `0x611a30ad` | `0x60dd5467` 经 parent+64 转发到 child，最终进入 `0x60def91e`，第 0 页作用于高光。 |
| `0x9032` 拨轮 | `0x611a30ca` | `0x60dd5445` 经 parent+60 转发到 child，最终进入 `0x60def75a`，第 0 页作用于阴影。 |
| `0x900c` OK 按下 | `0x611a2efa` | `0x60dd5489` 建立原厂 hold。parent+16 置 3，+20 置待派发的 0x903e。 |
| `0xf802` hold timer | `0x611a3430` | `0x60dd5623` 仅在等待 hold 时递归调用 parent virtual0 派发 0x903e。转入 child hash 表 `0x61159e44` 指向的 `0x60defc4b`，根据当前 scope 的重置表调用原厂默认值与写入。COLOR1 分支实际调用顺序 SH／HL／MID。 |
| `0x900d` OK 释放 | `0x611a34fb` | parent+68 的 `0x60e26489` 查询 `0x60dd5874`，依赖原厂 pending／hold 标志。应保留该路径。短按退出及取消行为还需具备完整输入状态的探针。 |
| `0xf855` touch | `0x611a3ac2` | 子控件 hash `0x61159e7c → 0x60defe88` 调用 `0x60df0222`，读取 1088 和触控包。类型 12 进入 `0x60df0332`，会在满足原生按区时改 +222 和 1088。 |

拨轮原厂处理依赖当前编辑目标。对曲线而言 `0x60def75a` 在 `0x60def79c–0x60def79e` 取反 D1 再按符号选操作，`0x60def91e` 则直接按 D1 符号选操作。完整拨动计数的生产链与 GUI 包归一规则见 [UI_INPUT_BINDING.md](../../docs/ep7/UI_INPUT_BINDING.md)。实际正反向要依据接入的归一接口分别验证。不要把 GUI 包 D1 视为物理拨轮计数，或在非事件上下文重读 `0x61fc4fb8`。

原厂 0x9014 在探针中完成切页时返回 0，属性 1088 的通知由模型边界截断。HDR 子页在不写入属性时需请求原生重绘和损伤区域，不能假定原生 INFO 返回值会带来同步 redraw。原生两页仍需保留属性 1088 的光标行为，HDR 的切页不写 HDR 等级。属性 1088 的存储生命周期未在本探针执行。

## 绘制、清理及候选接合

1. 保留两页的原厂 `+222` 和属性 1088。可把第三页作为曲线 child 自有的 UI 状态，原厂保持 Midtone 背景状态直到离开 HDR。候选是借鉴 015 逐任务尾字段，显式扩大真正分配并在原生构造时清零一个独立字段。该方案仍需验证原厂 allocator 类、另一种共用 vtable 的构造、所有清理调用和回滚。若改用外部状态，必须在原生重建和析构时撤销，裸指针比较无法处理同址重用。原厂构造 `0x60df01be–0x60df01ec` 允许恢复 1088=694，若实现合同要求每次从高光／阴影页开始，还需在目标构造内同步初始化页索引与 native cursor。核对另一类对象仍沿用原行为。
2. INFO 仅从真正的子控件 hash 分支 `0x61159e74` 接入。第一次进入原厂 Midtone，第二次在 Midtone 打开额外页，第三次撤销额外页后由原厂切回。挂点继承 `0x60defafe` 的 248B 栈帧，child 位于 `sp+16`，共用跳表必须保留非曲线分支依赖的寄存器。该分支识别 INFO 按下，释放继续委托。真实重复包节流仍需结合原厂清队列／状态机验证。色轮类别 1 的 INFO 和 015 对 0x9016 的截获不改。
3. 双拨轮可在 child vtable 的 +60／+64 分别接入，先核对当期 owner、状态和第三页，其他情况委托完整原函数 `0x60def75a`／`0x60def91e`。HDR 页边界值停止，只有发生档位变动才写当前 scope。长按只在 `0x61159e44` 的已验证 reset 分支中改为写 HDR OFF，并保留原厂父层计时、释放和清理。第三页需阻止落入原生 H/M/S 的其他编辑入口，例如 child 方向键分支和触摸处理 `0x60df0222`。回退和退出不得拦截原厂导航。
4. `0x60e26ab0` 每次清空 viewer+4 的 334B 属性区与 viewer+340 的 44B descriptor，读取当期 selector／child／模式。类别 3 专用调用 `0x60e26bb3 → 0x60e27639` 写 descriptor 种类 13、曲线状态字节及 guide 资源 2778／2779。`0x60e276f8` 检查从属性 1088 读到的 384／383 来选高光阴影页，其他值进入 Midtone 分支。它后面仍会走公共 display property229 与 request278。候选从该专用调用分流，保持公共发布路径，通过原厂控件的隐藏语义关闭旧曲线。原厂消费端 `0x60d7b27c–0x60d7b2a7` 以属性区字节 170 为零时隐藏曲线相关控件的一个入口。还有同层的数值、提示和另一个显示服务的图形，需要继续验证全部清除。不能把未核对的空 descriptor 类型当作合法输入。
5. 文字可复用 015 `native_hsl/paint.s` 的原厂字形、CLUT 和整根损伤机制。需按真正曲线 owner 的几何和裁剪做布局，并验证 HDR 打开、恢复及退出没有残留。015 现有色轮标题坐标由其 owner 的 Color heading 推导，不适用曲线页。未证明安全画面分支、作用域存储和曝光／ISP 联合接通前，此方案仅供实现审查。

## 一组原生输入探针

[single-dr-curve-ui-probe.py](single-dr-curve-ui-probe.py) 复用现有严格 MN103 引擎与 OwnerMachine 边界。执行 015 解码镜像中的实际 parent 工厂、selector 和曲线 child 构造，使用实际 machine4/state29 ROM 事件表、handler、container 方法、parent 和 child 方法。外层 container、viewer 对象初值、设置服务、定时事件投递、内存分配和最终显示输出属于显式模型。设置写入记录用于证明路由，不能证明物理保存或验证真实设置值的步进。未模拟按键 GPIO、触摸、完整 LCD 绘制、HDR 第三页、原厂短按退出或相机像素。

```powershell
docker run --rm --pull never --network none --env PYTHONPATH=/repo/tools --mount "type=bind,source=$PWD,target=/repo,readonly" --mount type=volume,source=ep7-research-toolchain-20261030,target=/work,readonly rust:1.96-bookworm python3 /repo/research/ep7/single-dr-curve-ui-probe.py
```

结果为 `passed stock tone UI route`。构造 5,359 条指令。INFO 按下 693 条，释放 730 条，第二次按下 693 条。两拨轮分别 1,553、1,562 条，进入不同目标并输出原厂 descriptor 类型 13。OK 按下 379 条，只记录 pending。F802 执行 2,119 条，走真实内部重置并重绘。无 SHA、固件改写、刷机或实机测试。

## 仅在模拟器内接入的第三页实验

[single-dr-curve-ui-experiment.s](single-dr-curve-ui-experiment.s) 使用同一套探针的 `--experiment` 参数。脚本交叉汇编与链接临时 veneer，核对八处 015 preimage，随后仅改写模拟器进程内的 decoded image。脚本不写新镜像，不使用生产 linker 或 015 build wiring。新增代码和 12B 状态由模拟器映射。

| 接入位置 | 在模型中执行的行为 |
| --- | --- |
| INFO hash 指针 `0x61159e74` | 检查机器、状态、当前 parent+80、类别、曲线 vtable 和 COLOR1 ROM 行。首按交给原厂写 1088=694，第二按仅打开额外页，第三按清 owner 后交原厂写 1088=384。第三页中 +222 始终为 1，1088 始终为 694。 |
| child 拨轮指针 `0x61159ee4`／`0x61159ee8` | HDR 页按原生两输入的符号方向，每次归一事件增减一档，边界钳制。非 HDR 页保留原厂属性写入。 |
| reset hash 指针 `0x61159e44` | 只有原厂 0x900c→0xf802 的子控件 reset 分支复位实验值。普通页继续由原厂写 SH、HL、MID 默认值。 |
| touch hash 指针 `0x61159e7c` | HDR 页在进入 `0x60df0222` 前消费触控，保留选择、等级和 native cursor。非 HDR 页实际运行 `0x60df0332` 及原厂写入。 |
| 原生曲线 draw `0x60e26bb1` | HDR 页绕过原厂曲线生成，保留 descriptor 类型 13 和公共属性发布，已清空的八个曲线字节传到输出边界。实机显示服务对此组合的完整语义仍未证明。 |
| 曲线重建 `0x60e2677d` 与构造恢复 `0x60df01be` | 重建清实验 owner，工厂 14 的作用域内复用原厂 3200 分支初始化 +222=0／1088=384。重建测试实际释放旧 child，重建后保留模拟档位且下一次 INFO 回到原厂 Midtone。 |

在上节 Docker 命令末尾加 `--experiment`。最终运行得到 `passed noninstallable HDR input experiment`，走了同一套真实事件表和执行路径。进入第三页 1,204 条指令，INFO 释放 730 条。HDR touch 1,602 条且无设置写入，普通触控 2,702 条且执行原厂切页。两拨轮覆盖 0→1→2、上限停住、2→1→0；HDR 内 hold 1,750 条，复位档位且保留 H/M/S。原厂 hold 回归 2,146 条，执行三个原厂设置写入。重建 615 条，执行已分配 child 的原生析构／模型分配。

实验仅覆盖 COLOR1，档位是一个易失的模拟器变量。第三页没有 HDR 文案、真实存储、曝光控制和 ISP 链。INFO 包的物理生成与连续按住重复源未运行。模式切换、同址分配、GUI 退出时的全套撤销、短 OK、实际触屏和 LCD 清理仍需验证。探针保留原厂设置通知边界，第三次 INFO 之后没有把模拟器的同步返回等同于 LCD 已恢复。现有 015 色轮 INFO／Delete 路由和所有生产源码均保持原样。

静态复核可复用 `mn10300-elf-objdump -D -b binary -m mn10300 --adjust-vma=0x60020020`，输入 `generated/ep7/full-input/main.decoded.bin`，按需限制到 `0x60e266a9–0x60e26789`、`0x60df002e–0x60df03bb`、`0x60dd5250–0x60dd5787`、`0x60def75a–0x60deffe7`、`0x60e26ab0–0x60e26c03`、`0x60e27639–0x60e2786a`。ROM 行与事件／vtable 指针用小端整数直接读取。

## 非安装候选的设置接线

`native_single_dr/ui.c` 与 `ui.s` 使用设置模块的 `ep7dr_selected_level`、`ep7dr_stage_level` 和 `ep7dr_selection_status`。曲线 child 必须来自当前机器 4/29 的 parent、viewer、类别 3 和原厂 factory 14，且当前公共图像模式 111 与 child+216 的原厂行一致。普通公共模式 0/1/2/3/5/6/7/20/21 共享第 0 行，COLOR1–4 对应 1–4，MONO1–4 对应 5–8。额外页只在设置模块接受当前作用域时可用。拍摄初版仅准入 Natural 与 COLOR1–4，其他作用域可独立选择并显示不可用。

INFO 页状态保存当前 child 地址。离开额外页回到原厂 INFO 分支，原厂恢复 +222 和 1088。重建 `0x60e266a9` 和 parent vtable+40 析构 `0x611895a4` 在释放原厂 child 之前撤销这个地址，重建后的原厂构造回到高光／阴影。重建与退出保留由设置模块持有的所选档位。两只拨轮、实际长按链和触控的边界沿用上面的原厂路径。

额外页继续用原厂 descriptor 类型 13。发布前清除曲线专用字段，使用 viewer+186 或 +260 的原厂提示记录。类型 5 由原厂 `0x60e850f8 → 0x60e85186` 解析，记录 +8 是内联 UTF-16。原厂 `0x60d7b6b3` 用控件 50/51 或 52/53 消费两组记录，实际文本调用入口为 `0x60d4c9df`。两组控件适配原厂属性 426 的位置选择。文字用一行并列 OFF/200/400，方括号标出所选档位，旁边可显示 `ISO400+`、`ISO800+` 或 `N/A`。实际曝光准入仍由拍摄状态决定。

原曲线页的两组提示不能同时用于原厂说明和额外状态。原厂资源表的两组文字矩形在布局 0 分别为 `(113,435,507,40)`、`(20,435,600,40)`，布局 1 分别为 `(113,435,587,40)`、`(20,435,680,40)`。它们在两种布局中都重叠，原厂底部图标 54–56 也占用 y=439。其余文字控件 7 和 11 与原厂曲线或数值区域相交。原厂类型 4 通过 `0x60e84513 → 0x60d4bf04` 选择本地化资源 2778/2779，原厂语言字符串指针表 `0x61fc1530` 在运行时加载，decoded main 中没有可验证所有语言标题宽度的初始化数据。当前保留 H/S 和 Midtone 原厂说明。 [原厂资源表证据](ui-resource-origin-current.json)

使用已链接候选的 `.elf` 和 `.decoded-main.bin`，`single-dr-curve-ui-probe.py --candidate` 核对十处 UI 边的最终字节并直接运行候选。COLOR1 通过 INFO、两只拨轮、长按 `0xf802`、触控 `0xf855`、重建和实际 parent 析构。拨轮和复位走原厂 ACTIVE 读写并核对缓存别名内容。ISO400 下选择 400 显示 `ISO800+`，ISO500 下选择 200 和 Auto ISO 下选择 400 均显示 `N/A`。原厂提示消费者读到 `HDR [OFF] 200 400` 并切换两个对应控件的可见性。回放将公共属性、拍摄键值、GUI 分配、提示文字控件和实际显示列为显式边界，实机 LCD、实体按钮与跨开机保存仍待验收。

```powershell
docker run --rm --pull never --network none --env PYTHONPATH=/repo/tools --mount "type=bind,source=$PWD,target=/repo,readonly" --mount type=volume,source=ep7-research-toolchain-20261030,target=/work,readonly rust:1.96-bookworm sh -c 'python3 /repo/tools/ep7_single_dr_candidate.py --prefix /work/install/bin/mn10300-elf- --baseline /repo/generated/ep7/flash-build-015 --out /tmp/ui-candidate && python3 /repo/research/ep7/single-dr-curve-ui-probe.py --candidate /tmp/ui-candidate'
```

同版本参考定位了 Direct_Actuator、ROM 曲线设置表和原厂绘图入口。该项目的第三 INFO 页处于计划状态，本记录的机器路径由本地 015 探针和 1100 窗口独立确认。 [Caduceus E-P7 原生 tone 研究](https://github.com/cakelesscoder/caduceus-ep7/blob/main/docs/TONE_ENDS.md#4-the-tone-control-screen-ui-v-static-no-emulator)
