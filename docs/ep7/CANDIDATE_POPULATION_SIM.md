# E-P7 原厂 capture 模板复制与 population 停止点

2026-11-01。候选004已从602a7ea0的实际patched prewrite入口执行到模板复制完成，
27332字节与原生初始化后的模板逐字节相同。再接入1084条原厂配置默认记录后，
population完成40次属性查询，停在尚未提供的动态状态622a064a；完整population未通过。

[探针](../../tools/ep7_candidate_population_sim.py)与
[实际报告](../../research/ep7/candidate-population-sim.json)复用
[属性初始化节点](CANDIDATE_PROPERTY_SIM.md)。没有重编译/修改固件、SHA或相机操作。
当前验证从独立克隆现场切回controller任务，不能作为连续启动或实际拍摄时序的证明。

## 实际执行

|片段|指令数|结果|
|---|---:|---|
|6005e309打包capture配置默认值|581,230|原厂typed packer搬运1084条记录，RAM实际范围153008字节与ROM数据/对齐一致|
|6005d987注册capture配置|64,545|新增1084个不同索引，和上游1209条合计2293条，无覆盖或额外填充|
|真实CALL602a7ea0至602a7eb0|49,697|实际lookup/prewrite各执行，60300055复制6833个word，源与目标全字节一致|
|从复制后真实寄存器继续population|2,429|40次getter后在604288d5读622a064a半字停止|

本节点共697,901条指令，最大新增观测调用深度344字节，不是完整controller栈上界。
长打包调用按100000×5+81230分段原状态resume，保留全部trace；没有重启或模拟复制成功。
上游297381条属性/模板初始化仍作为依赖执行，没有重复运行广泛主机测试。

新增配置bank的ROM header60096f90、records60096f98、terminator600be008，RAM
624ea400，原厂对象capacity262144。探针核对6005dc5a/6005dc6b/6005dc7c的真实绑定，
只映射实际153008字节范围；同一个原厂packer原生设置endpoint a2715ab8，其他
endpoint字段不变。头部与对齐空隙保持A5，记录payload与ROM逐字节相同。
没有导入或声明实机NVM/校准数据，新增bank不改变原来的四组默认值。

原capture fixture扩展到有原厂copy证据的27332字节前缀，并改为可写A5初值；
41984字节池槽剩余部分仍未映射。TCB由原厂ROM行核对为controller73、entry60289852、
stack4096，CALL mask f0/frame20来自既有population ABI。实际prewrite observer执行
一次后才开始复制；6833次60300061写入覆盖整个目标前缀。复制过程中保留同一原厂
CALL frame，从602a7eb0的真实寄存器继续，没有手工拼接成功的capture字段。

## 已关闭与仍保留的停止点

[最初的复制报告](../../research/ep7/candidate-population-frontier.json)只带上游1209条
属性：复制通过，随后35条指令在缺失810a时进入原厂诊断60061808。这个报告保留其
当时schema；当前工具--without-capture-defaults可复现该场景。810a确实属于新bank，
header60097af0、count1、width2、ROM默认值0，不是探针伪造的getter返回值。

接入新bank后，40次原生lookup依次完成，最后一项为c36a。随后原厂604288d5试图读取
622a064a，准备写capture+24178；第二个读取622a0648准备写capture+24180。真实返回
标签为602a8315。报告同时固定故障PC、地址、宽度、访问方向和未映射状态；不是仅以
“任意memory fault”作为预期结果，也不将诊断/quarantine误计为正常返回。

已定位状态来源：6042133f..60421364的原厂初始化片段会清零这组状态；
6042844e..60428481的动态更新片段从配置对象A2+48/+50更新622a0648/622a064a。
探针核对这些getter/reset/setter原厂操作数，但尚未执行完整状态初始化和配置更新。
当前保持该状态未映射，没有用BSS零值或一组猜测的拍摄尺寸绕过它。

下一步追踪动态配置对象及其选择/更新路径，建立这两个字段的可追溯输入，再继续
第一段population及第二段602a8dbd。之后接通relay两段预处理、worker分配/处理/撤销
和ACK。当前没有调用完成/seal observer掩盖中途停止，未把部分population结果交给
下游worker。之前独立的队列票据传输证明不因这次重填充成为完整拍摄链证明。

模板BSS清零的条件、真实NVM/拍摄状态、池分配、任务调度、多核、加载/所有权、完整栈
和恢复条件继续保留。候选004仍不可安装，最终更新包仍按fishcu原项目流程封装。

## 复现

```sh
python3 /repo/tools/ep7_candidate_population_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

沿用已有离线Docker只读repo/toolchain挂载。正常结果是template_copy_passed=true、
population_passed=false及上述明确停止点，不能把命令成功退出理解为population通过。
