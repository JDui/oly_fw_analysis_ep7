# E-P7 研究检查点 / 恢复研究

恢复日期：2026-10-30（Asia/Shanghai）。用户已要求继续推进研究测试。
**本轮推进电脑端捕获身份接合；未进行刷机或相机操作。**

## 本轮恢复后的增量

- 在既有 controller sidecar 中实现 `ep7c_resolve_live`，无需额外 token map。
  仅限调用方已证明存活且持有独占 controller 区间的节点；不接受以裸地址查询
  结果替代存活证明。旧裸地址遇到复用会查出新 token，这一限制已有可执行用例。
- 定向验证 COLOR4 快照冻结、忘记/复用、state33 重入、退出/重进、状态不一致
  poison 与全部8个槽位。严格 C11 和 ASan/UBSan 通过，无 SHA 校验。
- 现有检查器新增 `--host-only [--sanitize]`，不依赖原厂固件或目标工具链。
  见[执行报告](../../research/ep7/controller-sidecar-live-join-host.json)与
  [接口契约](../../prototypes/ep7_volatile_hl/controller_sidecar/README.md)。
- 本轮修改没有交叉编译；原生 node→token 调用点、对象存活/排他性证明及完整
  释放路径绑定仍待解决。旧交叉编译报告不代表此次源码已验证。

## 编译前路线与本轮推进

已建立 [G0–G8 完整编译前计划](PREBUILD_PLAN.md)。本轮首先完成
[生命周期证据清单](LIFECYCLE_HOOK_INVENTORY.md)：13个 node free、3个非 node free、
两处状态服务 call；源 witness 核对通过，不代表本次原厂字节重验或原生闭包。
新工具 `tools/ep7_lifecycle_inventory.py` 无需固件/交叉工具链，不执行 SHA 校验。

独立聊天“EP7 固件研究虚拟机环境设计”（gpt-6.1-terra / max）同步负责环境设计，
输出 `docs/ep7/VM_ENVIRONMENT_PLAN.md`。本聊天继续负责 G1/G2 身份/生命周期。
当前工作区没有私有原厂输入与目标工具链；下一步机器码资格审查需要准备这些输入。
未开始固件整体编译、打包或相机操作。

## 后续软件接合节点

实际 vertical slice 已接入 controller sidecar：register/resolve/authorize/seal/copyout
→节点撤销/33重入→后续 UI 修改→16个 fresh-job operation；捕获快照保持不变。
提前 copyout 的新节点不能晚 seal，NULL snapshot 路线仍完成原厂处理/清理 fixture，
输出保持中性。strict 与 ASan/UBSan 通过，见
[执行报告](../../research/ep7/sidecar-vertical-slice-host.json)。
这是主机按值传递契约的集成，未实现原生 metadata/descriptor handoff。

环境设计已由 Terra/max 完成，见 [VM_ENVIRONMENT_PLAN](VM_ENVIRONMENT_PLAN.md)。
当前正在从官方目录取得1100原厂输入及 GNU binutils2.45 源码；下载尚未验收。
旧 SHA guard 保留；新增的可选无哈希记录和结构检查入口不宣称历史逐字节身份。

## 原厂主程序可用于下一步研究

主程序首组件已完整提取，型号/构建/结构、加法和与自身编码回转通过，无SHA。
整包仍在下载，尚未完成五组件验收。当前字节扫描取得global node的4个、wrapper
queue的8个、async descriptor/callback各1个字面引用候选；这些还不是已反汇编的
指令边界或生命周期结论。见 [输入准备与复现](RESEARCH_INPUTS.md)。

## 原暂停检查点（历史记录）

以下记录保留原检查点范围；其中“未实现 token lookup”已由上面的主机实现更新，
其余原生绑定与固件安装阻塞仍然存在。
当前检查点内容以本分支提交为准：`git rev-parse HEAD`。
上一公开基线是 `9ff36d84fb6ac6f7e7c7b1b98833660cdbbf9099`；本检查点在其上保存已审新增工作。

先看 [QUICKSTART](QUICKSTART.md)。主机 smoke 不需要私有固件或交叉工具链。

检查点独立复核在不含固件/目标工具链的干净源码测试树运行：321项 E-P7测试
得到 OK（313项通过，8项可选检查明确跳过）、9项容器测试通过；六组 host smoke、
strict+ASan/UBSan 和实际软件 vertical slice 通过。skip 不是目标检查通过证据。

## 已保存的实际工作

- 原厂 E-P7 1.1/1100、model1420 的精确输入和五组件只读校验；原样 encode
  回转逐字节相等。SHA 见 QUICKSTART；仓库不含该固件。
- 实际 C H/L 状态、逻辑事件、UTF16 文本、每图快照、fresh-job decoder/direct
  reader、revoke/free 已在主机贯通；native 边界是明确的 fixture。
- MN10300 自写 ABI 桥已交叉编译/反汇编核对，未链接成目标程序、未执行或安装。
- 私有 poll-only 锁、startup ownership/quarantine、state-service 双调用点桥。
- `controller_sidecar/`：真实 controller-local C 回调、generation/token、单次捕获
  与复制；**原生 node pointer→token 接合、初始化和全部支持释放 hook 未实现**。
- `text_rollback/`：限定新建、未挂父 text class 的 cleanup→destructor→deallocator
  适配器。资源/对象资格与原生 allocator context provider 仍是未绑定契约。
- [metadata allocation](METADATA_ALLOCATION.md) 精确记录寄存器/返回帧接口；
  不是已实现 transport，也不允许凭 tag/kind19 读取未证明存在的扩展尾部。
- [packaging/recovery](PACKAGING_AND_RECOVERY.md) 核对本机 checksum 路径；
  无改动 roundtrip 不等于改包接受、可启动、同版本升级或可救砖。

## 仍然阻断相机可用版本的事项

1. 安全代码/数据放置、链接、短调用 trampoline/relocation、cache/栈空间和启动安装。
   没有证明某段全零/FF 就可注入，没有生成 E-P7 修改后的升级镜像。
2. 原生 category4/5、对象/字体/布局资源、输入焦点/完整拨轮次数、创建失败与回收绑定。
   `renderer_ready` 不能因为 host 文本测试通过而开启。
3. 捕获源→metadata→job 的实际身份/extent/lifetime handoff；所有支持的释放/取消路径、
   state33 重入、旧指针复用等。已复制的图像快照与 node admission 是不同生命周期。
4. GUI/capture producer/CPU reader 的任务域和同步、真实 runtime 分配/初始化、原生契约。
5. E-P7 完整 updater acceptance、版本/组件限制、可独立恢复的路径和专用实机测试。
   未证明救砖能力；无首次 native boot/HSL 实拍/像素校准。当前授权不包括刷机。

## 暂未纳入发布的探索

停止时以下仅是私有 scratch 或未完成思路，**不是随 clone 可执行/已审的实现**：

- 更新器更深层 component/model/write-dispatch 路径（72 witnesses 候选）；
- UI allocator context 两字节 accessor 绑定（77 witnesses 候选）；
- 不扩大 metadata、以既有 image identity 绑定快照的替代路线：刚开始，未独立复审；
- node pointer→current token join、代码放置/target-size 分析未完成或未开始。

恢复时先审这些候选与当前源码是否一致；不要根据本交接把未审结论补写成事实。
下一优先顺序是 identity/lifetime 接合与安全放置/恢复资格，而不是继续堆测试数量。

## 结果解释

主机测试成功说明被执行的自写代码在该 fixture 下工作；交叉编译只说明 ABI/对象
检查符合所设约束。两者都不证明 firmware 可刷、相机启动、JPEG/HSL 实际效果。
H/L 当前易失、重启归零；stock S 语义不应被改写。没有安全用户试刷日期承诺。
