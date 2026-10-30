# E-P7 H/S/L 研究环境与虚拟机方案

日期：2026-10-30。状态：**设计与只读清点；尚未创建 VM，也未做本方案的验收**。
本方案服务于 [HANDOFF](HANDOFF.md) 中的 E-P7 研究，不提供可刷固件或相机模拟器。
当前范围不包括安装大型组件、连接相机、刷机或编译可刷固件。

## 结论和边界

建议先复用现有 Docker Desktop 的 Linux 环境，做不依赖私有输入的单项主机检查；
需要独立系统快照、离线保存和交叉工具链研究时，再建设一台 Ubuntu 24.04 LTS
Hyper-V 研究 VM。Hyper-V 的管理功能是否已启用尚未确认，不以现有 WSL 运行作为
已经具备 Hyper-V Manager 或已创建完整 VM 的证据。

必须区分以下三层：

1. **Linux 研究/构建环境**：在 x86-64 上运行分析脚本、自写 C 测试和交叉工具。
   VM、WSL 和容器解决环境隔离与复现问题，不改变目标 CPU 或模拟相机。
2. **MN10300 指令模拟**：已有 GNU libsim 加仓库封装，可在受限内存映射、
   寄存器初值和外设替身下执行部分指令。现有高层封装和已有启动场景主要针对
   PEN-F；它们不是现成的 E-P7 完整模拟器，也不能直接把 PEN-F 地址当作 E-P7 地址。
3. **相机与 ISP 仿真**：当前不存在完整 E-P7 板级、传感器和 ISP 模型。不能用 VM、
   主机 C 测试或有限指令回放，推断相机能启动、可安全恢复或 JPEG 色彩正确。

## 本机只读调查

以下是 2026-10-30 的一次性观察，空闲资源会变化；开始建设前应重新查看：

| 项目 | 观察 | 含义 |
| --- | --- | --- |
| 系统与 CPU | Windows 11 专业版，64 位；Ryzen 9 5900X，12 核 24 逻辑处理器 | Windows 版本适合考虑 Hyper-V；任务不需要嵌套虚拟化 |
| 内存与磁盘 | 物理内存约 127.9 GiB；C: 当时约空闲 908 GiB | 建议先分配适量资源，并为快照、导出和其他应用预留空间 |
| 硬件虚拟化 | 固件虚拟化字段为 True，系统显示已有 hypervisor | WSL 2 已运行；当前查询的其他 CPU 虚拟化字段与此信息不一致，不把它们当成 SLAT 等能力的最终结论 |
| WSL | 仅列出运行中的 docker-desktop，版本 2；未看到独立 Ubuntu 发行版 | 不要直接修改或注销 Docker Desktop 管理的发行版 |
| Docker | Desktop 4.52.0、Engine 29.0.1，Linux amd64；服务端报告 24 CPU、约 62.8 GiB 可用内存 | 是现成的 Linux 容器路径；此数值不是固定的额外物理内存，WSL 和 Windows 应用共享主机资源 |
| 本地镜像 | 存在 rust:1.96-bookworm，约 2.2 GB，linux/amd64；已知交接记录该镜像有 GCC 12.2 和 Python 3 | 可先复用，不需为初始检查下载镜像；本轮未启动容器复核内部版本 |
| 工具链 | Windows PATH 未发现 cc/GCC；此工作树下没有 toolchains 目录 | 无法直接在 Windows 上假定可以运行 C 测试，也不代表另一台机器或旧环境没有交叉工具 |
| Hyper-V 管理功能 | 普通权限的 Windows 可选功能查询要求提升；当前会话未发现 Hyper-V PowerShell 模块/命令 | 是否安装、启用及能否创建 VM 均待确认；本轮没有提权、启用功能或重启 |

微软将 Windows 专业版与 SLAT 等条件列为 Hyper-V 前提；已有 hypervisor 时，
应在后续建设前结合系统信息与 Hyper-V 管理功能重新确认，而不是据上表推断
全部通过：[微软硬件要求](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/host-hardware-requirements?pivots=windows)。
Docker 官方说明多个 WSL 2 发行版共享内核，Docker 不要求另装用户发行版：
[Docker WSL 2 后端](https://docs.docker.com/desktop/features/wsl/)。

## 推荐结构与资源

### 阶段 0：现有容器，最小成本

Windows 上保留当前仓库；从选定工作内容制作独立的源码副本，仅将副本只读挂入
临时容器。关闭容器网络，测试临时文件留在容器内存文件系统。报告由标准输出获取，
不将整个工作树、私有固件或 Docker socket 挂入容器。这个方案可验证自写代码的主机
行为，但没有独立 VM 的系统快照，Docker 的内部 WSL 状态也不是相机状态。

### 阶段 1：可回滚的研究 VM

当确实需要系统级隔离或保存工具链时，首选 Hyper-V 第 2 代 VM，来宾选
Ubuntu Server 24.04 LTS x86-64。选择 24.04 是为了延续现有
[QUICKSTART](QUICKSTART.md) 的 Ubuntu/Python 3.12 路径，并有微软的 Hyper-V
兼容性文档；它并非最新 LTS，也不要求替换已有 Docker：
[Ubuntu 发行列表](https://ubuntu.com/project/docs/release-team/list-of-releases/)、
[微软 Ubuntu 虚拟机支持表](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/supported-ubuntu-virtual-machines-on-hyper-v)。
创建时保留 Secure Boot，使用适合 Linux 来宾的 Microsoft UEFI Certificate
Authority 模板并实际验证启动；如果有兼容问题，按官方说明排查，不预先声称已通过。

建议的起始配置：

| 资源 | 初始方案 | 调整条件 |
| --- | --- | --- |
| vCPU | 4，交叉工具构建先使用 make -j4 | 有明确耗时需求且主机空闲充裕时增至 8；它们与 24 个主机逻辑处理器共享 |
| 内存 | 8 GiB，构建 GNU 工具链时可调至 16 GiB | 同时运行 Docker 和 VM 时观察实际占用，保留 Windows 与其他程序余量 |
| 虚拟磁盘 | 动态扩展 VHDX，最大 100–120 GiB，按需实际增长 | 单独预留快照差异盘及至少一份完整导出的空间；检查实际空闲，不把虚拟上限当预分配空间 |
| 显示/设备 | 不配置 GPU 直通、USB 相机直通、串口或其他硬件直通 | 远程图形桌面不是初始要求；只有另行明确授权的独立阶段才考虑设备连接 |
| 网络 | 初始化时若必须联网，仅用于获取所需系统包；研究运行时移除或断开 VM 网卡 | 离线验收必须确认无可用网络接口；不把仅关闭浏览器当成离线 |

若 Hyper-V 管理功能不可用，先继续用已有 Docker 完成阶段 0；只有需要单独 Linux
用户环境时，才考虑另建 WSL 发行版。WSL 可导出/导入，但并不等同 Hyper-V VM
检查点；不要把 docker-desktop 当作可自由重置的研究发行版。
[微软 WSL 命令文档](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)。

## 依赖与复用

| 层次 | 依赖/已有方案 | 证据边界与当前限制 |
| --- | --- | --- |
| 主机检查 | Python 3.10+、C11 编译器、标准 C 库；已有 Docker 镜像据交接具备所需程序 | 首先记录实际 python3 和 cc 版本；不需要原厂固件、交叉编译器、IDA 或 Wine |
| 一般研究 | Git、Python 3.12、GNU make/C/C++ 编译环境；Pillow 仅供确需图像资源模块时使用 | 离线前预先保留所需版本及依赖；不必一次安装全部工具 |
| E-P7 目标对象检查 | 参考 [target README](../../prototypes/ep7_volatile_hl/target/README.md)、[ABI 说明](../../prototypes/ep7_volatile_hl/target/ABI-NOTES.md) 与 [build manifest](../../prototypes/ep7_volatile_hl/target/build-manifest.json)：GNU GCC 13.4.0、binutils 2.45、mn10300-elf；构建 GCC 所需 GMP、MPFR、MPC 按既有清单提供 | 这是 C-only、freestanding 的编译/汇编与反汇编路径，既有记录没有目标链接、目标执行或固件安装。GCC 与相机原生调用约定的差异须继续通过明确桥接处理 |
| 指令模拟 | 复用 [GNU MN103 模拟器与封装](../tooling/EMULATOR.md)、现有 strict patch 和 runner；不另造 CPU 模拟器 | 现有脚本的模拟器构建、准备和原有 PEN-F 回放内置 SHA 校验。当前无 SHA 校验约束下，不能直接按现有脚本运行该阶段，也不能删除其保护来制造通过 |
| E-P7 原厂静态研究 | 仅在未来有合法本地输入、目标反汇编器与独立审查的条件下研究；固件和工具不随仓库提供 | 现有多个 stock/目标检查器依赖内置 SHA 校验；当前不得直接运行这些路径或把文件名、型号、大小当作精确输入证明 |

GNU 的 [GCC 构建前提](https://gcc.gnu.org/install/prerequisites.html) 和
[GCC 13.4 MN10300 选项](https://gcc.gnu.org/onlinedocs/gcc-13.4.0/gcc/MN10300-Options.html)
用于核对依赖和选项。保持仓库现有 base MN10300、freestanding 和明确 ABI 边界，
不要因模拟器或编译器存在就擅自启用 AM33/AM34 特性、补齐原生地址或假设兼容。
以后如需在不做 SHA 校验的前提下重现目标/模拟器流程，须先确定可接受的输入身份
证据和独立审查方式；在此之前该项标为阻塞，不修改或绕过现有校验代码。

## 数据共享、快照与回滚

建议分成三类数据，默认不共享正在修改的原始工作树：

| 数据 | 位置与传递 | 快照/保密规则 |
| --- | --- | --- |
| 自写源码 | 固定时间点制作独立源码副本，放入 VM 自己的 Linux 文件系统；原始工作树保持不动 | 清楚记录分支、工作树状态、未提交和未跟踪内容；仅将本次需要的文件打包，避免丢掉正在进行的修改 |
| 生成结果 | VM 内独立输出目录；审阅后单向导出到主机单独目录 | 回滚前先导出要保留的结果；已导出的文件不随 VM 回滚，也不能覆盖其他工作 |
| 私有固件、照片、设备信息 | 初始阶段不传入；以后确有必要时单独、只读、按最小范围提供 | 不提交、上传或与普通日志混放；检查报告、追踪和反汇编也可能包含私有信息 |

离线传递优先使用为本项目单独制作的只读虚拟介质导入；需导出时可用专门的
交换虚拟盘或受控的仅主机共享目录，传递结束后断开。交换盘的格式和宿主/来宾
读写支持须事先验证。若使用共享目录，它位于 VM 外，**不会随 VM 检查点自动回滚**；
若使用额外虚拟盘，是否被检查点包含取决于实际配置，不应假定会或不会回滚。
传输只读固件不等于核实固件身份。

推荐在关机且写入完成后建立命名检查点，例如：干净 OS、基础依赖、
经审阅的工具链候选。以后每次大改前记录来宾的包版本和文件变化，回滚前导出
成果。Hyper-V 有标准与生产检查点：前者可包含运行时内存，后者面向文件系统一致性；
它们都不是独立备份。另将关机状态 VM 或检查点导出到单独位置，并在不覆盖原 VM 的
情况下验证导入和启动。不要手工删除差异磁盘；检查点的建立、合并和恢复应通过
Hyper-V 管理工具处理。参见[微软检查点说明](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/checkpoints)。

## 离线复现的保存清单

1. 保存合法来源的系统安装介质、VM 的完整导出、来宾系统与已装包版本清单；
   记录构建机架构、Python/编译器/make 版本、环境变量、编译选项与本项目文档版本。
2. 以独立目录归档本次完整源码副本；记录分支、干净/脏状态，以及实际使用的
   已跟踪和未跟踪文件。单独保存未提交变更，不依赖仅包含已提交内容的 Git 导出。
3. 容器路径可提前使用 Docker image save 保存现有镜像，之后以 image load 恢复；
   镜像标签可能变化，标签名称本身不足以证明不同机器上的镜像相同。
   参见 [save](https://docs.docker.com/reference/cli/docker/image/save/) 和
   [load](https://docs.docker.com/reference/cli/docker/image/load/)。
4. 若未来需要自行重建交叉工具或模拟器，分别归档上游源码、依赖、仓库补丁、
   构建参数和日志，并遵守 GNU 组件的许可证。已有目标工具链清单只是参考：
   当前工作树没有对应工具树，不能声称已保存或已能离线重建。
5. 记录实验输入范围、预期返回边界、实际命令、退出码、跳过项及结果用途。
   报告明确区分源文件副本、工具版本、模型前提和测试输出；不包含私有二进制。

本轮避免 SHA 哈希校验。保留原始介质、记录来源和版本、必要时对本地副本做逐字节
比较，可支持“这些副本彼此相同”的检查，但不能由文件名或这些记录独立证明其为
预期原厂版本，也不能替代现有脚本的输入保护。离线可运行与来源身份已经证实是
两项不同的验收结果。

## 按证据层次调试与测试

| 层次 | 有针对性的操作 | 能说明什么 | 不能说明什么 |
| --- | --- | --- | --- |
| 主机 C fixture | 先用 sidecar 的 host-only 严格 C11 检查；只有改动涉及内存或未定义行为时再选 ASan/UBSan | 在列出的自写 fixture 下测试路由与生命周期逻辑 | 相机上的对象存活、排他性、释放路径及真实任务调度 |
| 目标静态检查 | 未来在满足前述输入/工具条件后，对自写目标对象做汇编、符号和反汇编检查 | 指定工具与选项下的对象格式、调用帧和未解析符号 | 已链接、运行、安装，或与相机原生 ABI 整体兼容 |
| 有界指令模拟 | 未来从既有 GNU engine 及 runner 出发，先用自写合成代码和明确映射验证单个边界；E-P7 场景须单独研究和审查 | 明确初始寄存器、RAM、权限、指令数与停止地址下的有限指令结果 | 相机完整启动、真实定时、中断竞争、MMIO 行为或 ISP 像素 |
| 板级/真实相机 | 模型缺失时记录为未知；实体相机验证留待另行授权和独立恢复条件 | 后续可按经过审查的条件建立硬件证据 | 当前没有设备结果、可刷性、救砖能力或图像色彩校准结论 |

已有 GNU 模拟器有已知数据对齐盲点：部分未对齐访问可能被接受，尽管真实处理器
要求自然对齐；模拟器也未完整再现未知指令、标志位、外设、中断调度、NAND/ECC、
缓存时序和 ISP。必须把每个 stub、合成调用者、入参来源、内存区权限和 fault
记录在结果旁。未映射访问、未知指令、超时应停下报告，不用默认成功值掩盖。
PEN-F 的既有地址、ROM 和启动模型均不能直接推广到 E-P7。

主机调试时优先复用现有 fixture：先查看严格检查输出，确有必要再用与脚本相同的
源文件和标志构建带调试信息的临时主机测试程序，通过来宾的 GDB 定位自写 C 代码；
若涉及 Python 脚本则使用 Python 调试器。两者都只调试 Linux 进程。MN103
实验则先使用现有 runner 的有限指令轨迹、寄存器和 fault 记录；仓库模拟器的
构建配置禁用了 GDB，因此不能假定已经有目标远程调试服务。只有某个边界确实
需要交互式调试时，才另行评估 GDB 的目标支持与环境依赖。

### 最小无哈希主机检查示例（以后执行）

先将所需的自写源码复制到独立的 Windows 目录，保留仓库内
prototypes/ep7_volatile_hl 的相对路径；替换下例路径。此命令只运行现有
controller sidecar 的 host-only 模式，网络禁用，源目录只读；实际镜像及其工具
可用性须在执行时核实。它不访问私有固件，不运行目标代码：

~~~powershell
$ep7Stage = 'C:\path\to\ep7-source-copy'
docker run --rm --pull never --network none --read-only --cpus 4 --memory 2g --tmpfs /tmp:rw,exec,nosuid,size=512m -e PYTHONDONTWRITEBYTECODE=1 --mount "type=bind,source=$ep7Stage,target=/work,readonly" --workdir /work rust:1.96-bookworm python3 prototypes/ep7_volatile_hl/controller_sidecar/check.py --host-only
~~~

成功时记录标准输出、编译器版本及退出状态，确认报告表明未做哈希检查、
未访问相机、未执行目标且 flash_ready 为 false。需要 sanitizer 时才按同一脚本
的说明添加参数，并记下其泄漏检测限制。仓库中的其他部分（包括 QUICKSTART
所列通用 host 检查）会计算或校验 SHA，本轮不要直接运行；不能把 sidecar 的
通过结果扩展为整个研究项目全部通过。

如果以后在独立 Ubuntu VM 中执行同一项 fixture，无须在 VM 内再安装 Docker。
把对应源码副本放在来宾的独立目录，确认已安装 Python 与 C11 编译器，再从该
目录运行：

~~~sh
cd ~/ep7-source-copy
python3 prototypes/ep7_volatile_hl/controller_sidecar/check.py --host-only
~~~

## 分阶段建设与验收

以下均为未来执行的待办，当前不代表已经完成：

- [ ] **0：现有容器路径。** 清点单独源码副本，确认本地镜像与 Python/cc 可用；
  离线运行上面的单项 host-only 检查，保存输出及限制。不需要新增 VM。
- [ ] **1：研究 VM。** 确认 Hyper-V 管理功能和宿主要求，再创建独立 VM；
  核对 Secure Boot、资源上限、单独磁盘、关机检查点及系统版本。导出一份备份，
  不覆盖原 VM 地验证导入/启动。断网后在来宾直接运行同一最小主机 fixture
  并记录结果，无须在来宾安装 Docker。
- [ ] **2：目标工具准备。** 确认来源、保存介质和现有构建参数，并解决无 SHA
  约束与现有 guard 的冲突。完成此前不声称工具链已重建，也不运行受阻检查器。
  若未来运行，结果只验收到目标对象与静态 ABI 约束。
- [ ] **3：有界 MN103 指令实验。** 解决相同的来源与 guard 问题，复用既有引擎，
  审查合成输入和运行边界；单独证明某项 E-P7 假设后才建立 E-P7 专用 fixture。
  不以 PEN-F 结果代替该证明。
- [ ] **4：硬件与 ISP 证据。** 先解决 HANDOFF 中的安全放置、原生生命周期与
  同步、updater 接受和独立恢复路径等阻塞。真实设备实验须另行授权，另有计划、
  原始证据和验收；此阶段不属于本次建设。

各阶段记录“完成 / 失败 / 跳过 / 受阻”及其前提。断网、恢复和一次最小检查通过，
只验收研究环境可用，不等于原厂输入身份、相机执行或 H/S/L 视觉效果已经验证。
