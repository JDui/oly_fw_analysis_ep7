# 本地运行：先跑主机测试，不连接相机

这是研究源码检查点，**不是 E-P7 可刷固件，也没有相机 UI 模拟器**。
下面命令只编译/执行自写的电脑端测试，输出 JSON 或 unittest 的 OK。
不需要原厂固件、不需要 MN10300 交叉编译器、不需要连接相机。

## Windows：使用 WSL2 / Ubuntu

在管理员 PowerShell 中（已装 WSL 可跳过）：

```powershell
wsl --install -d Ubuntu
```

按提示重启、打开 Ubuntu 并完成 Linux 用户初始化。
适用 Windows 11 或支持该命令的 Windows 10；详见
[Microsoft 官方 WSL 安装说明](https://learn.microsoft.com/en-us/windows/wsl/install)。
以下命令在 **Ubuntu/Linux shell** 中运行，不是在 PowerShell/CMD 中运行。
本次实际测试环境是 Linux、Python 3.12、GCC 14.2；未声称已在你的 Windows 上运行。

```sh
sudo apt update
sudo apt install -y git python3 build-essential
mkdir -p ~/src
cd ~/src
git clone --branch EP7 --single-branch https://github.com/JDui/oly_fw_analysis_ep7.git
cd oly_fw_analysis_ep7
git branch --show-current
git rev-parse HEAD
```

依赖：Python 3.10+（建议 3.12）、C11 GCC/标准 C 库。初次主机测试不需要 pip 包。
已有 clone 的用户先检查 `git status`，保留自己的修改，再 `git switch EP7` 和
`git pull --ff-only`；不要用强制 reset 覆盖本地工作。

## 最小 smoke test

```sh
mkdir -p generated/ep7
python3 prototypes/ep7_volatile_hl/check_host.py > generated/ep7/host-smoke.json
python3 -m unittest discover -s tests -p 'test_ep7*.py'
python3 -m unittest discover -s tests -p 'test_oly_container.py'
```

第一条执行六组严格 C11 测试，成功 JSON 中 `passed` 为 true、`flash_ready` 为 false。
Python 测试缺少私有固件或目标工具链时会明确 **skip 可选检查**；skip 不等于通过。
若任何命令退出非零，请保留完整错误，不要删除校验或强行忽略失败。

## 更完整的电脑端链路

```sh
python3 prototypes/ep7_volatile_hl/check_host.py --sanitize > generated/ep7/host-sanitized.json
python3 prototypes/ep7_volatile_hl/integration/check.py > generated/ep7/vertical-slice.json
```

第二条连接真实的 C 路由/编辑/文字格式化/快照/处理/回收代码，覆盖16个 operation slot。
相机输入准入、分配/处理、widget setter 是主机 fixture；不是相机运行结果。
ASan/UBSan 需要主机 GCC sanitizer runtime（Ubuntu build-essential 的 GCC 环境）；
报告禁用了当前测试环境中的 LeakSanitizer。TSan 多线程压力测试是额外高级检查，
不是入门命令，也不保证每个 WSL/容器内核都支持。

## 可选：你已有合法获得的原厂 1.1 文件

固件不在仓库中，工具不会自动下载。把它放在被 git 忽略的 `firmware_files/`：

```sh
mkdir -p firmware_files
# 自行放入 OLY_E_142_1100_0000_0000.BIN 后：
sha256sum firmware_files/OLY_E_142_1100_0000_0000.BIN
python3 tools/ep7_stock_audit.py --stock firmware_files/OLY_E_142_1100_0000_0000.BIN > generated/ep7/stock-audit.json
```

唯一支持输入 SHA256：
`9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`。
此命令只用 Python 标准库，校验容器/固定版本证据，输出 JSON，不输出改版镜像。
不要上传原厂二进制、个人相片、设备私有数据或有签名的临时下载 URL。

## 可选：目标 ABI / 反汇编检查（不是首次运行要求）

`target/`、各 native bridge 的 `check.py` 通常需要独立构建的 GNU GCC13.4.0
`mn10300-elf` 与 binutils2.45。工具二进制/构建树不随仓库提供。
[目标工具链说明](../../prototypes/ep7_volatile_hl/target/README.md) 和
[构建清单](../../prototypes/ep7_volatile_hl/target/build-manifest.json) 记录来源、版本、
选项和本次工具 hash。不同机器重建的二进制 hash 可能不同；须独立验证来源后审查
工具身份清单，**不要为了通过测试删除 hash guard**。这些高级脚本没有一键安装承诺。
即使检查成功，也只产生临时、未链接且未执行的对象；不生成可刷固件。

## 发回运行结果

提供 `git rev-parse HEAD`、`python3 --version`、`gcc --version`、执行的命令与错误/JSON。
先检查输出不含个人路径等不希望公开的信息。恢复研究时从 [HANDOFF](HANDOFF.md) 继续；
现已恢复电脑端研究，当前未进行刷写或实机操作。
