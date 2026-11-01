# E-P7 HSL 五组件离线研究容器

2026-11-01。按用户指定的 fishcu 原项目方式，已把候选004封装成保留五组件的研究
容器。大小111,017,984字节；主组件替换后原生加和校验有效，其余四个组件完整的
编码字节均未变。**这关闭容器序列化问题，不代表可刷机资格通过。**

[工具](../../tools/ep7_candidate_package.py)直接复用
[原项目build流程](../../patches/hsl/pen-f/build.py)使用的
[oly_container](../../tools/oly_container.py)：parse → replace_payload → reconstruct。
没有另写编码器或校验算法，没有运行PEN-F build.py中的SHA检查，也没有重新编译。
[实际报告](../../research/ep7/candidate-package-004.json)保留全部未通过项。

## 实际输出与核对

本地输出：`generated/ep7/research-packages/candidate-004/`，包含
`EP7HSL-NONINSTALLABLE.research.oly`、`NONINSTALLABLE.txt`、`report.json`。
大文件留在Git忽略目录，提交/推送仅含工具、文档和摘要报告。

|组件kind|容器地址|payload字节|原版本字段|处理|
|---|---|---:|---|---|
|0100|406a0000|26,214,336|1100|替换为候选004 decoded main，重算尾部加和校验|
|0101|421a0000|26,214,336|0100|完整编码组件逐字节保留|
|0106|43aa0000|45,219,776|0100|完整编码组件逐字节保留|
|010e|00000000|262,080|0001|完整编码组件逐字节保留|
|0102|467e0000|13,107,136|0100|完整编码组件逐字节保留|

所有型号字段保持1420，不使用PEN-F的E122文件名或两组件输出假设。组件地址与
MN103执行地址是不同坐标；main的反汇编基址仍为60020020。

本次核对包括：原厂包不修改重建的完整字节相等；decoded stock确属输入包main；
候选源码未偏离构建版本；实际ELF代码段与候选一致；复用安装清单重建101处patch，
加两段代码共103个不重叠跨度，整体候选字节相等；五组件重新parse；所有header和
trailer前28字节保留；最终落盘回读相等。输入挂载只读，未做SHA或其他哈希校验。

另以实际解析结果做三个定向负控制：只保留两组件、改成PEN-F型号、交换组件顺序，
均被E-P7组件检查拒绝。没有重跑无关host/生命周期测试。

## 资格边界

研究文件使用正常容器编码和加和校验；NONINSTALLABLE文件名是操作隔离，**不是
相机强制拒绝机制**。本工具不输出DCOLYMP目录，不提供移除安装禁令的参数。
不应把该文件改名放入更新器。原厂输入也不是已验证的本机备份或独立救援镜像。

当前仅运行主机侧容器处理；尚未执行原厂完整更新器、版本/型号接受性、写入分发。
S3处理链、S4加载/所有权/缓存/完整栈、恢复和真机验收继续未通过。后续先在严格
离线引擎中执行原厂局部校验路径，再研究更新器和恢复条件；正式可刷机包仍须经过
[最终资格审查](FLASH_READINESS_PLAN.md)。

## 复现

在现有工具链容器中将repo与工具链卷只读挂载，另给新的输出目录可写挂载：

```sh
python3 /repo/tools/ep7_candidate_package.py \
  --stock /repo/firmware_files/ep7-1100-catalog/OLY_E_142_1100_0000_0000.BIN \
  --decoded-stock /repo/generated/ep7/full-input/main.decoded.bin \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --out /outputs/candidate-004
```

输出目录必须不存在；不覆盖前次结果。已有研究包无需重复封装。
