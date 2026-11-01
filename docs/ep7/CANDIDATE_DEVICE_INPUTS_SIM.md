# E-P7 有界设备输入与几何配置分支

2026-11-01。两组明确的离线寄存器输入已通过原厂GPIO采样、直接引脚采样、设备重置
和1215状态查询。仅改变logical GPIO80的bit4，原厂查询分别返回1/0，几何构造也走
到两个不同的原厂状态读取。当前两个分支都保留明确停止点，尚未完成配置或population。

[探针](../../tools/ep7_candidate_device_inputs_sim.py)与
[报告](../../research/ep7/candidate-device-inputs-sim.json)复用
[设备输入边界节点](CANDIDATE_DEVICE_STATE_SIM.md)的真实故障寄存器/栈。原厂固件和
候选004均未改写，没有API成功stub、SHA、重编译或相机操作。

## 输入及原生执行

原厂601aa228表给出的九个logical port为102、80、81、89、94、144、91、145、143。
地址来自原厂60024078指针表，全部精确映射为只读4字节region。输入保留相同的
无关bit，仅GPIO80的bit4在两次独立克隆中取0/1，其余八个bit4为0。
原厂GPIO采样从60022085真实fault现场resume，读完九个port后到6011813d，停在
后续事件注册前；两个bitmap/shadow实际变为0000和0200。没有跳过getter或直接写
入采样结果。初始两个OR字节依赖已记录的BSS清零条件。

另一组五个输入word为98e00058/5c/60/64/68，均提供76543210，即bit31为0、
其余bit带干扰值。完整60118545→600668b4实际组合出0，原生写入a272bcec和
621db5a4。接着执行完整601168ba，内部256查询也执行，a272bcdc/dd/de从A5变为
00/01/00。这里只验证给定稳定输入的读/组合逻辑，外设时序和读副作用未模拟。

原厂601aa1e8的1215记录为key1215、index1、polarity1。通过真实601168ed[f0],24
分别得到1和0，并核对完整返回SP/PC及原生锁状态；没有用fixture替代API返回值。

|执行片段|GPIO80=0|GPIO80=1|结果|
|---|---:|---:|---|
|GPIO采样真实resume|635|635|九个原厂getter顺序正确，两个byte的bitmap/shadow一致|
|五引脚采样60118545|32|32|完整返回，五bit结果0由原厂写入|
|设备重置601168ba|183|183|完整返回，内部256查询及三个flag符合给定输入|
|单独验证1215查询|305|304|实际返回1/0|
|原几何配置真实resume|318|321|进入不同分支并在确定未映射状态处停止|

本节点共2948条新指令。寄存器输入、板型输入0/设备列2及继承的默认属性都是明确
模拟场景，不能作为这台相机的测量值或整机启动证明。

## 配置继续执行的边界

两次均恢复最初几何构造停止时的真实栈，再从601168ee处的真实寄存器resume。
仅恢复该调用的栈，不回滚原厂初始化产生的RAM状态，也不重置配置函数从头再跑。

|GPIO80 bit4|1215返回|配置的新停止PC|读取地址/宽度|真实返回标签|
|---:|---:|---|---|---|
|0|1|6016bff6|62221d80，2字节|60165665|
|1|0|60163281|622211e2，1字节|601655f2|

6016bff6会比较半字状态是否为2；60163281先读一个flag，为0时还需622211dd。
这两种状态尚未提供，不能以未知零值越过。探针固定每个分支的fault PC、地址、
宽度、读方向和MDR，任意诊断、quarantine或其他fault都会失败。

两个分支均未执行动态setter6042805e。capture全27332字节保持不变，population
没有续接，也没有触发sample/seal、relay预处理或worker。新增观测深度1076字节
来自完整配置调用栈基准，仍不是任务栈上界。

下一步追踪62221d80与622211e2/622211dd的原厂初始化/生命周期，再继续配置对象
构造；有效拍摄状态、完整事件注册、IRQ/多核和真实NVM继续保留。候选004仍不可安装，
最终容器沿fishcu原项目parse→replace_payload→reconstruct方式处理E-P7自身组件。

## 复现

```sh
python3 /repo/tools/ep7_candidate_device_inputs_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

预期native_device_sampling_and_reset_passed=true；两项geometry_configuration_passed
均false，geometry_resumed=true、population_resumed=false。报告完整记录14个输入word。
