# 第二段 capture 完整返回与 finish 拒绝

2026-11-01。第二段原生填充现已正常返回实际调用者602a44ba，并经过候选finish
观察器。当前原生raw mode/selector仍为0/0，既有token属于重填充场景；核心finish
返回false，未封存旧sidecar。该结果不构成有效COLOR或新捕获代际证明。

证据：[复现工具](../../tools/ep7_candidate_postpopulation_finish_sim.py)、
[执行报告](../../research/ep7/candidate-postpopulation-finish-sim.json)。候选004与
fishcu五组件研究容器没有改变；没有SHA、固件重编译或相机操作。

|执行路径|实际结果|新增指令|
|---|---|---:|
|6029d0b0..d1cc，零输入|属性8441及三个完整原生helper生成状态1666/1684/1686 = 0/1/0|181|
|同片段，全位输入|相同PC路径和状态结果|181|
|6029dd7a..dd94|原getter读取模型sample25，原store生成三个halfword25/0/0|8|
|暂停的第二段继续至602a44ba|原生尾部、512B清零及候选finish观察器正常返回|9388|

合计9758条新增指令，观察最大新栈深404B，不能视为整个controller栈上界。新增
11B均为原生store目的；tail debug gate采用4B明确冷BSS条件。新增8B模拟输入：

- command+72 flags分别为0和ffffffff，原消息来源仍未证明。
- 请求对象+1914 halfword分别为0和ffff，原生产者仍未接通。
- 原getter6006773f读取的最近服务sample设为25。没有执行传感器采样或转换，
  不声明物理单位与真实相机读数。

只做了一组针对输入依赖的比较。当前原生1678/1696/1998/1695均为0；属性8441
读取0，602a7060在读取其输入+8之前返回。flags的相关bit判断亦不在当前路径中。
两个输入组合都由真实指令产生相同状态，不能推广为其他模式/所有组合已验证。
6029d089的开头格式处理和后续controller工作没有执行；完成的是明确边界片段。

只有这些原生产片段完成后，才恢复之前暂停的消费者栈和寄存器。原602a9f16写入
temperature字段，原605e61d7调用已经原生搬运的4700115e清零512B。相对上一节点，
capture只有offset14406从0变为25；其余tail写入与现值相同。

真实候选_ep7cn_population收到node19510000和finish=1，_ep7c_finish_population
进入一次并返回0，回到602a44ba时SP恢复190107b0，私有锁释放。原sidecar首条记录
仍为attempted=1、sampled=0、sealed=0、begun=1、post_begun=1，没有创建新token
或把旧COLOR前缀升级为有效快照。不能仅凭正常返回声称H/L拍摄完成。

下一步追原生COLOR属性设置及新capture/node代际。完整消息来源、调度/异步别名、
worker、代码/RAM驻留和备份/恢复仍保留；研究容器继续不可安装，最终仍复用fishcu
parse → replace_payload → reconstruct，而不是另写封装格式。
