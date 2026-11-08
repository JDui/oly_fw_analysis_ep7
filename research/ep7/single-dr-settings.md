# E-P7 1100 单帧 HDR 设置作用域与持久化

> 2026-11-08 / 019 更正：用户在 018 实机反馈 0010。`622484fa` 是持续的会话
> 状态，不是操作中的 busy。`602b35a4` 首入置 1 后在 `602b36d4` 返回，直到独立
> `602b36d7` 才清零；旧记录把后者误认为前者收尾。当前实现以两个函数实际执行
> 区间的 epoch 保护，保持原厂标志原值。CPU 0/1 回放执行外层真实分支／置位／返回，
> 并在标志为 1 的情况下完成 UI、设置和成像快照验证。其余旧增益方案记录仅作历史。

2026-11-07。基于原厂 1100 decoded main 的静态对照和定向 CPU 模拟。确认了原厂曲线的作用域、bank 复制和关机保存路径。九个候选 ACTIVE 单元通过原厂读写、整份 bank 复制及相关复位验证。本轮没有修改固件、接入机身或计算 SHA。

## 原生曲线作用域

`60df00e1–60df0160` 通过属性服务读公开 Picture Mode 111。`54,55,56,64,57,58,59,65` 分别选后八行，其余模式选首行。表 `611595a8` 每行 56 字节，两页各七个 u32。第一组为 `(SH,HL,SH,HL,3200,SH,HL)`，第二组为 `(MID,MID,MID,MID,3200,MID,MID)`。`60defe96` 把行中的属性号更新到当前编辑器子项。首行适用于已经进入原生曲线页的其他模式，不能用它给特殊模式授予成像资格。

| 作用域 | 公开模式 111 | 属性 HL / MID / SH | 设置打包分支 | HDR 存储候选（ACTIVE part 1） |
| --- | --- | --- | --- | --- |
| 普通共享 | 编辑器默认分支 | 891 / 892 / 893 | `602b7d6c` | 894 |
| COLOR1 | 54 | 963 / 964 / 965 | `602b814e` | 963 |
| COLOR2 | 55 | 966 / 967 / 968 | `602b823c` | 966 |
| COLOR3 | 56 | 969 / 970 / 971 | `602b832a` | 969 |
| COLOR4 | 64 | 1672 / 1673 / 1674 | `602b8418` | 1672 |
| MONO1 | 57 | 998 / 999 / 1000 | `602b850d` | 998 |
| MONO2 | 58 | 1001 / 1002 / 1003 | `602b8591` | 1001 |
| MONO3 | 59 | 1004 / 1005 / 1006 | `602b8615` | 1004 |
| MONO4 | 65 | 1675 / 1676 / 1677 | `602b86a0` | 1675 |

第二处交叉证据是 `602b8916` 调用 `602b7b71`。后者使用 `60460458` 分支表，通过 `602b2237` 从上述属性读三项，封装为 HL/MID/SH 的 144/148/152 字节偏移。返回后 `602b8af3`、`602b8b00`、`602b8b0c` 将三项分别写到有效镜像 384、694、383。`60e083d5–60e085a0` 的 SCP 渲染读取这三个镜像，原厂调试调用明确按 high/low/mid 打印。设置打包调用中 `602b2237` 的参数 `d1=2` 属于另一套上下文 API，不能解释为 ACTIVE part 2。静态结论也与同 build 的 [Caduceus 曲线研究](https://github.com/cakelesscoder/caduceus-ep7/blob/main/docs/TONE_ENDS.md) 的 COLOR 及普通组映射一致。

## 为什么筛选这些候选单元

`604a8420` 的 70 个模式／子模式过滤表逐行检查过。三项普通属性与三个有效镜像每项均被选择 70 次，其中 43 次用 part 1、27 次用 part 0。这六个属性的 part 1 已有原厂语义。24 个 COLOR／MONO 曲线属性各在 70 张表里出现一次且始终选择 part 0。原厂模式加载 `602b97c5` 和定制加载 `602b9890` 遵循描述符的 part 参数，后者没有表项时用 part 0。对应更新 `602b982a`、`602b9960` 同样遵循描述符或回退到 part 0。

普通组的独立候选 894 与 891 在已查的复位列表中同进同出，且它在 70 张过滤表始终用 part 0。894 原厂 property map `604d6c14` 指向 typed key `f632` index 0，默认表 `604a8774` 给值 3200。原厂有以 894 为 ID 的对象，例 `6092c3fe`／`6092c407`。这里的依据是已追踪的 **part 选择与复位路径**，而不是原厂属性本身闲置。894 与八个 COLOR／MONO 候选都在 015 H1 的属性范围 927–962、1655–1666 之外。

`602b972b`、`602b9778` 根据列表对指定属性的两份 ACTIVE 单元写回原生默认值。`602b3930` 的自定义清除路径经 `602b9a32` 将 `604ac68c` 表中的属性两份一并复位，再在 `602b39aa` 整份写回银行。

| 原厂属性表 | 数量 | 普通源 891–893 / 候选 894 | COLOR/MONO 源 HL / 候选同列 |
| --- | ---: | --- | --- |
| `604aa91c` | 27 | 无 | 无 |
| `604abc28` | 2 | 无 | 无 |
| `604abc2c` | 6 | 无 | 无 |
| `604ab744` | 626 | 有 | 无 |
| `604aa952` | 1785 | 有 | 有 |
| `604abc38`、`604ac68c` | 各 1322 | 有 | 有 |

`602b962f` 逐个初始化属性 0–1768 的两份 ACTIVE 并复制到九个内部银行。不能用 COLOR1 的 964 part 1 替代普通组单元，因 626 项复位包括普通曲线而不包括 COLOR1。HDR 页局部复位应只写该页对应的 HDR 单元，原厂曲线页仍沿用原有属性处理。

ACTIVE part 读写为 `602cc0a7` / `602cc0d0`，索引 `1769 * part + property`。相对调用与绝对指针扫描后复核了相关入口。除上述过滤、复位和整体传输外，`602b3419/342c/343a/344f/346c/34a5/3846/3859` 使用固定的其他属性与 part 0。`602b9c75` 的双份写入仅由 3009/3010 调用。`602bf32e/3f2`、`613da114/266` 走诊断枚举，`613dc0c9/de/10c` 的 `Set_CameraBankInfo` 等工程命令可任意读写有效索引。这个盘点覆盖已识别的普通调用路径和工程入口，仍不能证明其它组件或未识别的间接调用的可达性。

## 整份保存、读取与切换

`602cbb21` 初始化在 `602cbbb9/602cbbcc/602cbbdf` 通过 `6005e947` 解析 `85d4/8b64/8b54`，写 `62253590/94/98`。`602cbffe`（bank→ACTIVE）和 `602cc03a`（ACTIVE→bank）复制全部 3538 个 u32。`602b3926` 是自定义保存经 `602b3874/602b38a7` 后的整份写回点，`602b3408`、`602b3835` 是自定义读取的整份复制点。未修改的 015 定向模拟有这两条底层复制循环的运行证据，测试目标为既有 H1。

`85d4`（32,040 个 u32）、`8b64`（3,560 个 u32）和 `8b54`（1,780 个 u32）均在 Mode 设置组 7 内。组头 `60096f90` 类型 7，记录从 `60096f98` 开始。按 `6005e309` 同样的类型对齐计算，三条记录的工作区 payload 依次为 `624ea8dc`、`6250ba00`、`62509e30`。组对象根 `a2711a9c` 由 `6005dc1e` 写入，`6005dc28–6005dc86` 绑定工作区 `624ea400`、容量 `0x40000`、后备 `a2a78000`，第二后备指针置零。未使用记录声明长度与 bank 步长的差值。

- 关机路径 `601e7305–601e7319` 清零 44 字节描述符，再写 operation 1 及 offset +8 使能位，调用 `6005f099`。`6005f1ed–6005f1fa` 取组 7 对象，调用 `6005c5be`。后者比较工作区及后备的 `[+8, capacity−4)`，变更时递增原生代数 `6005c811`，由 `6005c7e7/6005c7f3` 计算 16 位加和，最后从 `6005c643` 交给 `6005bc79` 原生存储后端。`602cc6d8` 也会通过 `602cc715` 发出包含组 7 的保存请求。
- 读取 `6005f400/6005f406` 取同一对象并调用 `6005c524`，用 `6005c3bb → 6005c78a` 核对类型与完整半字和，再由 `6005c550` 复制后备到工作区，`6005f445 → 6005d6aa` 重新注册。`6005d76a–6005d77b` 用组 7 ROM 描述和工作区 `624ea408` 绑定记录。
- 关机保存的比较范围和校验范围覆盖上述 ACTIVE 与 bank 单元。九个候选在 ROM 默认 ACTIVE 和各 bank 初值均为零。复位可能写入非零原厂默认值，例如 894 写 3200 或 COLOR2 的 HL 写 3。后续编码须用独立标记和精确枚举值匹配，使初值、旧 015 数据及原厂复位值均解为 OFF。无需另设 flash writer。

普通 bank 模式切换仍有两个条件需要闭合。`602b33ec` 可先载入 bank 0，`602b3408` 随后才载入目标 bank，设置写抑制到 `602b3529` 才置位，`602b3587` 清除后才有 `602b3597` 的变更回调。`602b3823/3835` 有另一组前后整份复制，`602b3a9f` 也可在 `602b3ac1` 抑制前改写 ACTIVE。不能只查 `62257b04` 就把 ACTIVE 的选中 HDR 与当前测光状态绑定。成像侧应在已提交的 bank/模式及新曝光锁定之间取得逐张快照，需要先证明串行化或显式处理这些中间窗口。物理持久化、升级前用户数据实读和配置备份导入均未实机验证。

## 曝光提交与设置切换的交界

`60039664` 的任务表行 ID 为 `0x73`，入口为 `60289852`，`6028a1c8` 用来识别本控制器任务的 ROM 半字 `600409be` 也为 `0x73`。`6042d674+8` 的 `StlRdy2` 状态入口 `6029cf0b` 在 `6223daca != 1` 分支经 `6029d01b` 进入 `6029d089`。该函数在 `6029d5d7–6029d5da` 将当前采集命令 `+60` 指向的曝光 metadata 设为 type-7 engine `+4`，普通成功路径在 `6029d68e` 提交 engine。提交返回 0 且 `6223daca=0` 时，`6029d7cd` 才从同一当前命令取捕获 ID，调用 `602a7ea0` 填充捕获记录。015 H1 读取位于这次填充中的后置 getter，虽可供成片使用，但晚于本次采集增益提交。`StlLiveTake` 状态入口 `6029f6f5` 对应另一条命令路径，经 `6029f847–6029f850` 绑定同一形状的 metadata 后，在 `6029f91f` 调用 `602aa5ba`。两处 metadata 附着都能定位到原厂控制器，尚无证据说明它们与 GUI 设置写入共享原子提交。

`622484fa` 是会话状态。`602b35a4` 的首入分支在 `602b35d2` 置 1，再在 `602b3637` 进入 `602b3363`，最终在 `602b36d4` 返回且保留 1；`602b36d7` 是独立的结束函数，不能把它误作前者收尾。公开进入函数调用点为 `602af922/602afbd9`，退出调用点为 `602afbf1`。此外，`OlyHfwUserSettingManager::changeModeConflict` 的 `60826b5e` 直接调用 `602afbfc`，后者在 `602afc32` 只查前述晚到的写抑制，再在 `602afc5d` 调用 `602b36f1`，经 `602b3794` 进入同一个 `602b3363`。这条路径可在 `622484fa` 未置位时到达 bank 整份复制。HFW 包装器另在 `60826b55/60826b81` 设置／清除 `61fa7538`。对其 getter `6076ba0a` 的相对调用扫描只找到 `6087eaa2`，该 HFW 分支可跳过自身后续处理，未与控制器的曝光附着入口建立互斥。SDK `loadCustomSetting` 在 `60826ef4/60826f07` 检查 `TAKE_CBS_SHOOTING_PICTURE` 与 `getActiveReleasePermission`，随后才派发命令 596。该准入检查也未覆盖上述直接 HFW 模式切换入口。

这构成可核对的原生守卫覆盖缺口。只检查 `622484fa` 或 `62257b04`，即使结合两者，也可能把中间 bank 的 HDR 字与尚未提交的原生曲线作用域配对。当前证据未显示该交错已经在机身出现，也未证明全部已排队曝光命令由同一设置锁串行。应将 HDR 选择与原厂命令绑定在已提交的设置快照上，再由采集与成片各自消费同一冻结值。不能在 `602a7ea0`、`602a91ee` 或 ISP 侧补读 ACTIVE 作为这次曝光的选择。本节仅补充静态窗口与调用引用核对，未重复运行存储或 015 仿真。

## 采集验证用的临时档位

首轮采集验证由 `native_single_dr/settings.c` 为 Natural 与 COLOR1–4 提供五个独立的对齐 32 位槽。槽初始为零，`ep7dr_stage_level` 只接收公开模式 1、54、55、56、64 及档位 0、1、2。`ep7dr_selected_level` 为编辑器读取同一槽，拒绝时返回 −1。写入与取样限制在 core 0。目标编译产物中，每次槽写入或读取各为一条 32 位 `mov`。入口不读写 ACTIVE 档位，存储探针中的标签仍为隔离验证格式。

`ep7dr_select_scoped_level` 在 `6029d68e` 提交前核对当前命令、type 7 engine、`6223d488` mode 10 以及两处指向同一 metadata 的引用。原厂 `602a6583` 构造 mode 10 描述符，`6029d3c4–ca` 把它附到 engine。原有 H1 公共属性桥读取公开 111。通过与 `602a7ea0` 一样的 `6005e971` typed getter 再核对实际输入，Natural 要求键 `9481` 为 2，COLOR1–4 要求它为 11 且键 `f6b1` 为对应的 1–4。原厂在 `602a8583` 和 `602a85c0` 写入捕获记录 +24053/+24083。某些模式经键 `9d11` 覆盖原模式，本轮只接受上述原始键。

| 提交前要求 | 原厂成片输入及证据 |
| --- | --- |
| Gradation `8eb9=0` 和强制 Auto `9961=0` | `602a8044/5a` 写捕获 +24018/+24020。ROM 属性 105/159 默认均为零。若 +24020 非零，`603e65a9–bb` 把 job +5524 设为 2，否则使用 +24018。随后 `60354efb/eff` 将该字节传至 ISP 请求 +1797。控制器在 `6029c772–7f` 也将 `9961` 锁存到 `6223daa2`，准入时要求该字节为零。 |
| 开发分支键 `eee1=0` | `602a8811/1a` 写捕获 +24799，值 1 会改走另一条成片路径。ROM 属性 686 默认为零。 |
| 特殊拍摄键 `e911=0` | `602a8360/69` 写捕获 +24134，`602a8a95–a9` 可据此把 +24776 设为 11。该分支是 `603ea9d7` 生成非零 ISP +1808 的前提。ROM 属性 600 默认为零。 |
| 普通 JPEG `8141=1`、`8231=0`、`52b1=0/1` | `602a7ee7–602a7fff` 生成捕获 +24012 和格式选择 +23920。对照[记录格式证据](single-dr-shot-eligibility.md)。 |
| 单拍及普通快门 `6223dabc=0`、`6223dbea=0` | 使用曝光提交时控制器当前值。其命令来源与条件见[控制器字段证据](single-dr-shot-eligibility.md)。 |
| 原厂 strobe 信息与普通计算形状 | `602a781a–3c` 将 byte `6223dac6` 及两个 halfword `6223dac8/ca` 打印为 `strobe_info`。准入要求三项为零。`602a2374`、`6029f57a` 将 `6016e369` 的返回值锁存到 `6223daca`，其中 `6016e39b–3b1` 对已准备的闪光分支返回 1。提前检查 metadata+0 bit7、+32 word 和 +44 halfword 为零，与下层增益输入的普通形状一致。这些观察未覆盖全部附件和热靴状态。 |

取样前后均检查有效属性、原生模式、Gradation、记录格式、上述开发分支键和当前命令。旧方案曾同时检查 byte `62257b04`（`602cc6c6/cf`）、byte `622484fa`（`602b35d2`）和 word `61fa7538`（`6076ba01/0a`）；019 已确认中间一项是持续会话状态，不能作为 busy。其他标志与双读也不能证明提交至原生后续捕获记录填充之间没有设置变化。控制器另一处 `602a2535/3e` 读取 `8141` 后，结果只经过 `603f0a2c → 6061da06` 检查媒体容量，未锁存供 `602a7ea0` 使用。曝光提交后的 `602a7ee7` 仍重新读取当前画质。逐张记录应携带已经返回的档位和作用域，后置原厂字段可以核对是否发生偏离。固定 ISO 和 JPEG 作业身份由采集侧另行判断（此为旧增益路线历史要求）。

用现有 MN10300 工具链编译并运行定向模拟，执行实际档位代码和 getter 桥。属性服务由检查入参和原生返回帧的夹具代替。验证了初始 OFF、COLOR1/2 隔离、Natural、错误档位和作用域、原生模式不匹配、非零 Gradation 或强制 Auto 锁存、替代开发路径及 RAW-only 拒绝。模拟也检查非零 strobe、连拍或快门字段会拒绝。该验证仅覆盖设置入口，完整原厂采集与 ISP 行为仍须用相同拍摄身份联动核对。

## 定向复现

以下探针只读本地 decoded main。原生窗口可使用既有 Docker 工具链的 `mn10300-elf-objdump -D -b binary -m mn10300 --adjust-vma=0x60020020 --start-address=<起点> --stop-address=<终点> /repo/generated/ep7/full-input/main.decoded.bin`。优先查看 `602b7d6c–602b7d96`、`602b814e–602b8728`、`602b8aee–602b8b18`、`602b33c9–602b3416`、`602b962f–602b96ac`、`601e7305–601e7320`、`6005f1ed–6005f1fe`、`6005c5be–6005c64c`、`6005f3f9–6005f44c`。

```powershell
@'
from collections import Counter
from pathlib import Path
from struct import unpack_from

main = Path('generated/ep7/full-input/main.decoded.bin').read_bytes()
base = 0x60020020
assert len(main) == 26214336 and main[0xb6:0xb8] == b'\xfc\xdc'

def read(fmt, addr):
    return unpack_from(fmt, main, addr - base)

scopes = (891, 963, 966, 969, 1672, 998, 1001, 1004, 1675)
owners = (894, *scopes[1:])
for index, high in enumerate(scopes):
    shadow = high + 2
    middle = high + 1
    expected = (shadow, high, shadow, high, 3200, shadow, high)
    expected += (middle, middle, middle, middle, 3200, middle, middle)
    assert read('<14I', 0x611595a8 + 56 * index) == expected

ordinary = (383, 384, 694, 891, 892, 893)
part_zero_only = (894, *(high + delta for high in scopes[1:] for delta in range(3)))
observed = (*ordinary, *part_zero_only)
parts = Counter()
for index in range(70):
    mode, sub, table, count, padding = read('<HHIHH', 0x604a8420 + 12 * index)
    assert mode and count in (1337, 1338) and padding == 0
    present = Counter()
    for item in range(count):
        key, part, flags = read('<HBB', table + 4 * item)
        if key in observed:
            assert part in (0, 1) and flags == 0
            parts[key, part] += 1
            present[key] += 1
    assert all(present[key] == 1 for key in observed)
assert read('<H', 0x604a8768) == (0,)
for key in ordinary:
    assert (parts[key, 0], parts[key, 1]) == (27, 43)
for key in part_zero_only:
    assert (parts[key, 0], parts[key, 1]) == (70, 0)

lists = ((0x604aa91c, 27), (0x604abc28, 2), (0x604abc2c, 6),
         (0x604ab744, 626), (0x604aa952, 1785),
         (0x604abc38, 1322), (0x604ac68c, 1322))
for address, count in lists:
    ids = read(f'<{count}H', address)
    assert (894 in ids) == (891 in ids) == (892 in ids) == (893 in ids)
    assert all((key in ids) == (963 in ids) for key in owners[1:])

assert read('<HH', 0x600b90c8) == (0x8b64, 3560)
assert read('<HH', 0x60097da0) == (0x85d4, 32040)
for key in owners:
    assert read('<I', 0x600b90cc + 4 * (1769 + key)) == (0,)
    for bank in range(9):
        assert read('<I', 0x60097da4 + 4 * (3538 * bank + 1769 + key)) == (0,)
print('9 UI rows, 70 filters, 7 reset lists and 9 cells across 9 bank defaults matched')
'@ | python -
```

上述静态脚本执行成功，退出码 0。另用现有严格 MN10300 runner 执行 [定向存储探针](single-dr-settings-probe.py)，结果为 [通过](single-dr-settings-probe.json)。它用 ROM 原值及已证实的工作区地址构造隔离 RAM，只用模拟 CPU 执行原厂设置指令。九个候选经过原生 ACTIVE 读写，COLOR1/2 分别保留 200 和 400，回读旧 bank 得到 OFF，再从 bank 2 恢复完全相同的 14,152 字节。原厂 `602b960d` 走完整 626 项部分复位，普通组回到原厂默认 3200 并解为 OFF，COLOR/MONO 与相邻 015 H1 字均保留。另把原厂全复位表中 COLOR2 的一项交给同一个 `602b9778` 循环，实际写回默认 3 并解为 OFF，同时保持 COLOR1 和 H1。探针标签仅用于隔离验证，现有 015 生产代码未修改。关机写入为静态证据，完整设置生命周期、bank 切换调度和后备写入均未模拟。

```powershell
$ep7Root = (Get-Location).Path
docker run --rm --pull never --network none `
  --mount "type=bind,source=$ep7Root,target=/repo,readonly" `
  --mount type=volume,source=ep7-research-toolchain-20261030,target=/work,readonly `
  rust:1.96-bookworm python3 /repo/research/ep7/single-dr-settings-probe.py `
  --main /repo/generated/ep7/full-input/main.decoded.bin `
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```
