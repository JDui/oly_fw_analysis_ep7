# E-P7 原厂几何服务初始化与配置构造停止点

2026-11-01。候选004的原厂几何服务、请求字段、模式快照和两组属性缓存已在条件模拟
中完成初始化。配置构造6042760c推进1920条指令后，在601168ee读取未映射的设备状态
a272bcde停止；尚未到达动态setter6042805e，也没有继续capture population。

[探针](../../tools/ep7_candidate_geometry_sim.py)复用既有population现场、严格引擎及
反汇编解析器。[实际报告](../../research/ep7/candidate-geometry-sim.json)记录各段
指令、栈深度、原厂指针和最终寄存器。固件未重建或修改，无SHA和相机操作。

## 实际执行与输入来源

|片段|指令数|已验证结果|
|---|---:|---|
|60421330服务初始化|5217|6020d024实际查询148次，填充147个属性指针槽；reset/数组内容正确|
|602ad810..602ad86d控制器重置前缀|18|6223ed22等有证据的目标由A5实际写入，停在事件注册前|
|60421540..604215b4任务初始化前缀|131|局部对象实际清零及服务状态初始化，未进入接收循环|
|603b6297..603b62c8模式重置前缀|397|真实调用603b700e，三份24字节记录与ROM来源一致|
|602add13..602add5b请求字段构造|15|48字节请求仅+36/+37/+38变为1/0/1，其他字节保留A5|
|6042270f..6042273c请求字段消费|10|原厂代码写入request mode和两个flag|
|60173690设备属性缓存初始化|4336|117次原厂getter填充117行，key/subindex不变，全部指针匹配已注册bank|
|6042760c配置构造|1920|停在设备状态读取；未到达6042805e|

几何服务映射仅包含已审查初始化代码的直接写入地址和有界数组，初值为A5；地址间的
空洞不映射，也不添加可读取的guard填充。初始化后的零尺寸是重置状态，不能拿来
代替一次拍摄的动态配置。6042760c实际分配/初始化自己的84/16/480/76/26/36/4字节
栈对象；探针没有伪造76字节配置对象或跳到最终setter。

请求的三个控制器分支输入6223ed08、6223eca3、6223ed28是显式单次请求fixture。
原厂602add0a附近证明分配长度48，602add5b写命令400，队列来自60040d9a=5f；
dispatch hash表6054aaa0的401/604216ad与handler604226e2绑定已核对。
本节点只执行字段生产/消费片段，不宣称执行分配、队列传输、完整handler或状态转换。

模式初始化调用点603b62c1使用原厂常量3；603b700e检索6053348c的九行后选取
fallback第9行60533564。原生复制三份24字节快照至a27396d8..a2739720，清除每份
字节1..7，selector a2739720=0，packed flags a2739688=3。它是原厂重置路径的
真实输出，不是实际拍摄模式已确认。

设备属性缓存61f9ad74共117行、每行8字节、103种key，ROM来源60233034。这里复用
[既有启动数据搬运研究](UI_RESOURCE_ORIGIN.md)：60230800..6025eb50对应RAM
a1f98540及cached别名61f98540。只提供这936字节的原厂初始数据，117个指针初值
均为0。随后执行真实60173690[e0],16，D0=0来自原厂6017383b调用点；原生getter
逐行填入此前2293条属性记录中的数据指针。没有用探针直接填写结果指针。
启动NAND/ECC搬运、a1/61别名cache一致性仍是明确条件，未因表初始化通过而算作通过。

## 停止点的推进记录

|报告|配置构造指令数|明确停止点|
|---|---:|---|
|[最初](../../research/ep7/candidate-geometry-frontier.json)|1079|6020e0e3读取622a0780，缺请求模式|
|[接入请求](../../research/ep7/candidate-geometry-request-frontier.json)|1168|60555c80读取6223ed22，缺控制器重置|
|[接入控制器/任务前缀](../../research/ep7/candidate-geometry-snapshot-frontier.json)|1669|603b6fb7读取a2739720，缺模式快照|
|[接入模式快照](../../research/ep7/candidate-geometry-property-frontier.json)|1850|601736d0读取61f9b0ce，缺设备属性缓存|
|[当前](../../research/ep7/candidate-geometry-sim.json)|1920|601168ee读取a272bcde，缺设备状态初始化|

历史报告保留生成时的schema，不能把较早停止点改写为已通过。当前脚本固定各支持
场景的故障PC、地址、访问方向和宽度，任意其他fault、诊断或quarantine都会失败。
--without-request、--without-service-prefixes、--without-device-cache分别保留
前三类可选依赖缺失场景；模式快照缺失报告是当时执行的历史证据。

当前真实返回标签601654dc，查询编号D2=1215。已定位601168ba负责设置a272bcdc/dd/de，
但其内部还会查询设备状态；6011681d需要读取600226f7返回的8ff00198字节，再选择
设备表列。下一步追踪这些原厂初始化和数据来源，不能直接补一个零字节越过停止点。

原population栈单独保留，几何服务使用独立栈调用；没有把各前缀拼成完整启动时序。
27332字节partial capture在本节点完全不变，completion/seal、relay预处理、worker
构造/处理/撤销/ACK均未因本节点获得资格。S3仍未整体完成，候选004仍不可安装。
最终更新包继续按fishcu原流程重建，保留E-P7型号与全部未修改组件。

## 复现

```sh
python3 /repo/tools/ep7_candidate_geometry_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

使用既有离线Docker、只读repo和toolchain挂载。预期service_initialization_passed=true、
configuration_producer_passed=false、population_resumed=false及上述确定停止点。
