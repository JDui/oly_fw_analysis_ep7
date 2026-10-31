# E-P7 HSL 首个离线候选

2026-11-01 后续：[当前可刷机包目标](FLASH_READINESS_PLAN.md)正在推进。
当前候选为 **offline-candidate-004**：修复[原生接收入口绑定](CANDIDATE_MESSAGE_SIM.md)，
复用全部107个对象重新链接/合成，通过实际消息发送、通知、接收及空轮询。相对003
仅两个CALL重定位字节改变，布局不变；[增量报告](../../research/ep7/offline-candidate-004.json)
记录结果。003此前已修复[原生发送gate返回地址](CANDIDATE_QUEUE_GATE_SIM.md)漏检，
重编译1个对象、复用106个，相对002两个立即数字节改变。
仍不可安装。下文保留首个002候选的构建结果和原有边界。

2026-10-31。用户已明确选择先编译不可安装的离线候选，检查整体链接与布局，
保留全部未通过项。此选择修改 PREBUILD_PLAN 的离线 G8；不批准安装或实机执行。

## 构建范围与顺序

1. 复用 `target/sources.txt` 的 107 个实现源、`ep7_installation_manifest.py` 的
   101 项修改及 `ep7_native_bindings.py` 的地址表，不添加模拟实现来消除缺失符号。
2. 原厂 decoded main 只读；先核对长度、101 项修改前字节、加载表及两个候选代码区
   的填充值。此核对只确认输入适配，不证明空间所有权。
3. 用现有 MN10300 GCC 13.4 / binutils 2.45 编译全部实现并保留对象、日志和 `.su`。
   对象检查不是最终交付；必须整体链接成功，再合成独立 decoded main 候选。
4. 整体链接禁用 relaxation 和 build ID；实际输入段决定对象在两区的分配。
   拒绝未知分配段、非零初始化可写数据、未解析符号、越界与段重叠。
5. 从 ELF 提取两个代码段；按既有清单计算 101 项替换。核对 36 座最终 veneer、
   实际 CALL/JMP 解码和修改范围之外的字节不变。候选输出落盘后按字节回读。
6. 保存 ELF、map、链接脚本、符号/布局与未决项报告、解码研究镜像及禁安装说明。
   生成物放在被 Git 忽略的 `generated/ep7/offline-candidate-*`；提交代码、文档和
   不含原厂镜像内容的摘要报告。关键准备与构建结果分别提交并推送。

不重复运行未改动的 host/ASan 全套。新增验证只针对最终链接、重定位与镜像合成。
不做 SHA/其他哈希校验。没有新的升级 packer；本批不需要生成厂商升级容器。

## 显式候选假设

|区域|离线采用的范围，结束不含|已知限制|
|---|---|---|
|代码区 0|60048040..6004ffc0，32,640 字节|早期复制请求覆盖；FF 与有限引用分类不证明可覆盖|
|代码区 1|600c8040..600cffc0，32,640 字节|同上；引用和其他组件所有权未闭合|
|私有 BSS|a1dd4d00..a1dd8d00，16 KiB|domain2 大池末槽 payload 候选；冷清零和首次分配前保留未取得完整资格|

正式地址表中的 `__ep7_private_uncached_start` 继续保留 `address=None`；仅本候选的
链接脚本采用 `proposed_address`，报告明确记录该覆盖。两个代码区的前后保留边界
不写入，私有 RAM 不作为 decoded main 内的文件段输出。`.bss` 为 NOLOAD，仍依赖
现有冷清零桥，不通过 ELF 装载器偷偷补充原厂并不存在的初始化步骤。

ELF entry 选择自有冷清零桥仅用于工具识别；实际原厂启动仍由 600201fe 的候选修改
进入。不得把 ELF entry 或链接成功描述成可启动性证明。

## 必须随产物保留的未通过项

- G1 捕获身份、释放/重填充与异步别名的完整覆盖；G2/G3 取消、任务/队列存活及排他。
- G4 GUI 串行所有权与旁路；显示效果和拨轮交互尚无真机验收。
- G6 代码/RAM 所有权、3 处启动前缀上游装载、早期复制失败、次核/缓存可见性、
  冷保留时点及完整任务/IRQ 栈上界。当前完整栈上界仍是未知。
- G5 持久化明确不在本次易失候选中；G7 更新器完整接受性、独立恢复和实机资格未通过。

产物固定标记 `installable=false`、`hardware_executed=false`；无 `.BIN` 升级包，
不连接相机、烧录或发布 Release。以上项目不会因为链接/合成通过而自动转为已验证。

## 实际构建结果

**首个完整离线候选已编译、整体链接并合成成功。**
[结构化报告](../../research/ep7/offline-candidate.json)对应本地
`generated/ep7/offline-candidate-002/`。源码版本 `7386faa`，107 个实现对象来自
`96c611d` 的本次完整编译；复用前检查实现源、头文件、汇编宏和编译配方相对该版本
无差异，编译器版本相同。没有重新编译未变的对象或重跑业务测试。

|最终分配|起点..结束，不含|实际字节|候选容量|剩余字节|
|---|---|---:|---:|---:|
|代码/只读常量 0|60048040..6004da7c|23,100|32,640|9,540|
|代码/只读常量 1|600c8040..600cdce3|23,715|32,640|8,925|
|BSS，NOLOAD|a1dd4d00..a1dd6c94|8,084|16,384|8,300|

链接后代码/常量共 46,815 字节，比未链接合计多 15 字节对齐空间。109 个外部符号
全部解析，其中私有 RAM 是上述显式候选覆盖；84 个修改目标/adapter 均位于输出代码段。
独立 `readelf -h -l -S` 检查为 little-endian MN10300 ELF32，两个 R/E LOAD 和一个
文件长度为零的 RW BSS LOAD，没有 RWX 段。ELF entry 为 `6004bb92`，对应冷清零桥。

101 项修改原跨度 546 字节，36 座已链接 veneer 的完整 30 字节、原返回地址、frame
和 adapter 位移符合既有宏；73 处最终 CALL/JMP 经 GNU 解码符合目标。两段代码与
101 项修改共 103 个写入跨度，无重叠；其外字节保持原样。合成镜像为 26,214,336 字节，
实际改变 46,279 字节，落盘回读相等；只读原厂输入保持不变。没有哈希或相机执行。

保留首次失败：`offline-candidate-001` 已完成 107 源编译，但严格孤立段检查拒绝
六个汇编对象的空 `.text`。`7386faa` 显式接收剩余只读段并断言总大小为零，保留
`--orphan-handling=error`，随后复用对象完成本候选。失败报告与日志未删除。
构建后只关闭 Git 行尾警告的命令级输出，不改全局配置、链接规则或固件实现。

本地主要产物：

- `EP7HSL-NONINSTALLABLE.elf`：103,056 字节，完整自有实现及原厂绝对符号。
- `EP7HSL-NONINSTALLABLE.map`、`offline-layout.ld`、`symbols.json`：实际链接与分配。
- `EP7HSL-NONINSTALLABLE.decoded-main.bin`：解码研究镜像，没有厂商更新头尾或封装。
- `object-inventory.json`、`objects/`、`report.json`、`NONINSTALLABLE.txt`：对象、栈资料与限制。

## 复现

使用现有隔离镜像 `rust:1.96-bookworm` 和工具卷 `ep7-research-toolchain-20261030`。
将仓库只读挂载到 `/repo`、工具卷只读挂载到 `/work`，一个新的空输出目录可写挂载到
`/output`；容器 `--network none --env PYTHONDONTWRITEBYTECODE=1`，执行：

```sh
python3 /repo/tools/ep7_offline_candidate.py \
  --decoded /repo/generated/ep7/full-input/main.decoded.bin \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --source-revision "$(git -c safe.directory=/repo -C /repo rev-parse HEAD)" \
  --output /output
```

需要复用本次对象时追加 `--reuse-objects-from /repo/generated/ep7/offline-candidate-001`；
工具自动核对记录的实现源版本与当前编译器。仅实现C/ASM变化时复用现有partial-object
编译器刷新对应对象；header/宏/编译配方、编译器或源顺序变化会拒绝复用。
输出目录非空也会拒绝，
不覆盖前一次结果。后续安装研究直接使用上述实际布局，仍需逐项关闭保留的未通过项。
