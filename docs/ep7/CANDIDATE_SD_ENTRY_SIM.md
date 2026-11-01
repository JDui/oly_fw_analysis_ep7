# E-P7 SD 文件选择与更新消息入口

2026-11-01。候选004的原生 SD 软件路径完成1,624条指令的有限检查：文件选择
callback、各组pattern遍历、32字节消息构造和接收任务分流均执行原厂代码。最后
停在共享更新器60c964c1，参数为buffer a43a3ec0、111,017,984字节、mode0。
未执行物理SD、更新按键触发、flash写入或整机启动。

## 文件选择

ROM任务行60039370配置task88、entry60c95bab、priority45、stack2048。
该任务按60f2cbf0的11行表扫描；最后一行包含E/G/H/W四个pattern，先找到E就停止
本组后续查找。初始化数据中的真实指针来自60230800→61f98540搬运映射。
目录短名是`DCOLYMP    `，主程序pattern为`E142????BIN`，即8.3文件名形式
`E142xxxx.BIN`。本节点没有创建这个目录或输出安装文件。

60c95f05的原callback在文件系统已经匹配pattern的目录项中，调用原属性、FAT32
cluster和长度getter，再由60c95fd8解析四位后缀。实际执行下列顺序：

|输入短名|目录属性|选择结果|
|---|---:|---|
|E1421100BIN|0x20|选择cluster10，后缀0x1100|
|E1429999BIN|0x20|改选cluster11，长度111,017,984|
|E1421200BIN|0x20|保持9999|
|E142FFFFBIN|0x10|目录项被排除，保持9999|
|E1429999BIN，另一个cluster|0x20|相同后缀不替换已选项|

这些是明确的目录项输入；未模拟实际卡、通配匹配器或文件内容读取。9999只是此
选择器的十六进制排序值，不是固件build，也不构成版本升级或降级资格。

## 消息接续

原pattern wrapper60c95db0实际运行，底层search/read60c95e7a返回明确模型结果：
前十组无文件，E组返回上述包长。原task88随后构造32B消息，发送到queue119，
reply queue35、type1、mode byte0；模型只复制该消息，不补其padding。

ROM任务行60038bc8配置task18、entry60c96030、priority55、stack2048。原接收任务
从queue119取回相同32B，实际走type1分支60c96100，通过60c96114调用共享更新器。
其A0/D0/D1保持buffer/包长/0。本次只映射实际包的32B头供接收端读取，并在共享
函数入口停止；完整五组件内容验收沿用[此前更新器结果](CANDIDATE_UPDATER_SIM.md)，
没有再次解码整包，也没有把文件系统模型计为实际读取成功。

timer、watchdog、SD准备、文件查找/读取、queue交付、设备准备和通知为显式模型。
callback内部的属性/cluster/长度getter、排序、pattern wrapper、任务控制流、消息
构造和类型分流运行原生代码。无SHA、网络、USB或相机操作，固件/研究容器未改变。

初次探针的字节witness抄录和目录短名padding断言分别在执行检查时失败，修正探针后
完整运行exit0；没有据此修改固件或宽松化长度/路由检查。

## 剩余边界

任务配置和软件入口仍不能证明物理开机/按键条件、独立恢复、实际写入和回读。
不把PEN-F的设备操作照搬到E-P7。当前研究包继续标记不可安装；下一项检查基础
H/L GUI/worker改动及代码/RAM驻留，封装仍复用fishcu五组件流程。

[工具](../../tools/ep7_candidate_sd_entry_sim.py) ·
[机器报告](../../research/ep7/candidate-sd-entry-sim.json)。
