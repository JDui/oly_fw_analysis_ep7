# 严格指令引擎与 E-P7 定向原生回放

2026-11-01 更新：[MULQIU 修正与descriptor回放](CANDIDATE_DESCRIPTOR_SIM.md)确认 GNU
原有 imm8/imm16 无符号乘法误用符号扩展，独立两行补丁按松下手册修正。后续用
`/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu`；旧二进制保留作历史
复现。6条定向指令通过，原厂descriptor正常返回；下面是最初构建的历史证据。

2026-10-31。已有 GNU libsim、仓库 strict patch 和 C runner 已在现有 Docker 环境
实际构建并用于 E-P7 原厂指令片段。六个定向场景全部通过。**这是指令模型回放，
没有完整相机仿真、启动回放或新固件整体编译。**

## 复用与输入来源

复用 `build_mn103_emulator.py` 的版本和 configure 参数、`mn103_strict.patch`、
`mn103_runner.c`；没有新增 CPU 指令实现。已有 patch 已包含手册对应的 MAC 传送模型，
未知访问、trap/syscall 会停止。模型对未定义 N/Z 标志使用确定性保留策略。

新入口 [ep7_build_sim.py](../../tools/ep7_build_sim.py) 接受显式本地源码归档和两份
独立获取的 GNU 源文件。它比较完整 `interp.c`、`mn10300.igen` 字节，检查版本日期、
归档路径和必需依赖，再以零 fuzz、零 offset 应用已有补丁；增量准备只接受原文或
精确补丁结果。旧 PEN-F 构建器、prepare 的 SHA 门槛和 `firmware()` 身份检查未修改。

[来源记录](../../research/ep7/strict-sim-source.json)固定到
[上游镜像提交 87ffb882](https://github.com/RTEMS/sourceware-mirror-binutils-gdb/commit/87ffb882e0f4d73401a0746177ffabb8e8bbe4ac)。
最终归档由 Git 导出68个路径选择项，22,244,450字节、6,898个成员；两份独立参考分别
29,701和79,154字节。未计算SHA，也不把两份文件相等称作整个归档的密码学身份验证。
第三方源码、Git镜像、下载和二进制均在忽略目录或私有volume，未提交。

构建中实际遇到并修正了三个输入问题：整包下载超时后改用Git；Windows默认导出
CRLF被字节检查拒绝，改用临时`core.autocrlf=false`重新导出；源码子集补齐了
`libctf/swap.h`和`gdb/version.in`依赖，入口现会在构建前检查它们。旧全局Git设置不变。

## 实际环境和重现

[构建报告](../../research/ep7/strict-sim-build.json)：复用`rust:1.96-bookworm`、
GCC12.2宿主及既有MPFR构建。4CPU/8GiB、禁网构建，没有系统安装或新建VM。
私有volume仍是`ep7-research-toolchain-20261030`，最终可执行文件为：

`/work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103`，8,845,992字节。

源码选择项见来源记录。先从固定Git版本导出LF归档，并取得同版本的两份完整参考文件，
再按现有挂载关系（仓库只读到`/repo`，私有volume可写到`/work`）运行：

```sh
python3 /repo/tools/ep7_build_sim.py \
  --archive /repo/toolchains/mirror-inputs/binutils-gdb-87ffb882-selected.tar.gz \
  --reference-dir /repo/toolchains/mirror-inputs/mn103-87ffb882-reference \
  --work /work/ep7-mn103-sim-87ffb882-complete \
  --mpfr-include /work/src/mpfr-4.1.0/src \
  --mpfr-lib /work/gcc-build/mpfr/src/.libs --jobs 4
```

未删除早期失败构建目录`/work/ep7-mn103-sim-87ffb882`；它不是可用引擎。
最终目录的`ep7-build.json`、configure/build/harness日志保留实际结果。远程clone
不附带私有volume，不能由这份报告推断另一台机器已安装工具。

## 最小回放结果

运行协议仍复用 `penf_emulator.execute`。新增调用方式必须同时指定`engine=...`和
`record_hashes=False`；不改变原有默认调用的哈希记录，也不调用PEN-F的固件加载入口。
内存范围、权限、别名、停止地址、步数和超时检查仍走原实现。

[探针](../../tools/ep7_sim_probe.py)先核对39条原厂指令及current-task cell配置，
然后执行六个场景、八次短引擎调用；[报告](../../research/ep7/strict-sim-probe.json)：

|场景|实际结果|
|---|---|
|未映射地址取指|memory_fault，execute访问，完成指令0|
|syscall指令|instruction_fault，完成指令0，未派发主机服务|
|MCVF为0和1的MAC保存/恢复|各10+13指令；16字节帧；MCRH/MCRL/MCVF/MDRQ恢复；IRQ mask保留；帧外无写入|
|TCB+48为1|原厂查询返回0，保留pending word；含合成CALL共13指令，SP恢复|
|TCB+48为0|返回pending并清零该word；含合成CALL共15指令，SP恢复|

CPU ID、root cell、当前TCB指针、TCB和栈使用明确合成输入；执行的helper/query代码
来自当前E-P7原厂解码文件。没有执行任务创建、IRQ入口、调度器、异步外设或整个bootstrap。
未重跑PEN-F全集、业务sanitizer或107个生产对象；生产固件代码和对象预算没有变化。

## 对编译准入的影响

后续可用同一引擎检查真正的原生加载/所有权片段，在未知MMIO或回调处停止，沿用上游
已有的load/execute/reload方法。无需继续为每段指令单独实现模拟器。

本节点只落实执行工具并验证其最小用途，未关闭启动前缀装载者、代码/RAM所有权、
TCB flag有效期、context恢复或完整栈关卡。模型中的MAC回转也不证明相机芯片的
flag流水线、cache或IRQ时序。G6/G8保持未通过，没有固件升级文件或相机操作。
