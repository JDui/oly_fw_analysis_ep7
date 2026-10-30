# 当前本地 MN10300 研究工具链

2026-10-30；binutils2.45、GCC13.4.0已实际构建完成，不是仅下载源码。
GNU镜像列表包含中科大镜像：[官方列表](https://www.gnu.org/prep/ftp.en.html)。
源码从该HTTPS镜像获取；与已从GNU主站取得的部分直接逐字节比较一致，MPFR/MPC
旧下载已完整，因此这两份档案是完整文件比较。未做SHA或签名验证，不声称该比较
建立了GCC/binutils完整档案的历史身份。[来源记录](../../research/ep7/toolchain-source-acquisition.json)。

## 存储与隔离

复用本地rust:1.96-bookworm的Debian/GCC12.2宿主。源归档位于被忽略的
`toolchains/mirror-inputs/`；Linux构建树与安装位于专用Docker volume
`ep7-research-toolchain-20261030`，容器内/work/install。没有系统安装、相机设备挂载
或运行中的构建容器；构建过程禁网，binutils限4CPU/4GiB，GCC限4CPU/8GiB。
宿主已装GMP6.2.1开发包、zlib，MPFR4.1.0/MPC1.2.1从固定源版本在树内构建。

[构建脚本](../../tools/ep7_build_tools.sh)复用既有配置，分binutils/gcc两步。
没有运行目标程序，没有生成升级包。源码和二进制不入git，私有volume不能视为远程
clone自带的工具链。脚本在已有Makefile上可继续make，不会删除既有构建树。

```powershell
$ep7Root = 'C:\Users\Muxinzheng\Documents\ChatGPT\EP7-FW'
docker run --rm --pull never --network none --cpus 4 --memory 8g --mount "type=bind,source=$ep7Root/toolchains/mirror-inputs,target=/sources,readonly" --mount "type=bind,source=$ep7Root/tools/ep7_build_tools.sh,target=/build-tools.sh,readonly" --mount type=volume,source=ep7-research-toolchain-20261030,target=/work rust:1.96-bookworm sh /build-tools.sh gcc
```

首次先把末尾gcc换成binutils。仅在归档完整、相应工作空间属于本研究时执行。
配置和构建日志在volume的/work/logs中；旧hash-pinned检查器与历史报告保留不动。

## 当前目标对象验证

用安装后的工具重新编译sidecar、transition、observer、bridge、core、decode、memory
七个对象，使用C11/O2/freestanding/no-builtin/no-setlb/no-liw及既有目标头文件。
符号集合检查通过：只留下 `_ep7_controller_sidecar_unresolved` 和
`ep7_stock_state_service_unresolved` 两个外部符号。resolve_live扩展已包含在此轮
目标编译中，先前“修改未交叉编译”的状态仅适用于旧检查点。

[执行报告](../../research/ep7/controller-sidecar-current-target.json)；
[当前显式工具路径检查器](../../tools/ep7_sidecar_target_check.py)。该检查器不运行
主机fixture、不计算SHA，不宣称通过旧工具hash身份门槛。

```powershell
docker run --rm --pull never --network none --mount "type=bind,source=$ep7Root,target=/repo,readonly" --mount type=volume,source=ep7-research-toolchain-20261030,target=/work,readonly rust:1.96-bookworm python3 /repo/tools/ep7_sidecar_target_check.py --tool-prefix /work/install/bin/mn10300-elf-
```

没有链接目标镜像、测量真实栈余量或安装hook。两个外部符号、原生生命周期/任务域、
UI资源及代码放置仍未绑定；这不是“新固件已开始编译”的完成证据。
下一步可用此环境做必要的ABI/尺寸研究与反汇编，不需要再创建独立VM才能推进。
