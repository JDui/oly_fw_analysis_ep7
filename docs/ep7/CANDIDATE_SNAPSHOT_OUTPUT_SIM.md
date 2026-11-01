# E-P7 冷态快照回调返回与几何配置续接

2026-11-01。原输出构造器、60426f83 回调和 6041a20a 外层包装函数均已执行返回，
到达真实任务调用点 60409ecb，SP 为 1901076c。两条 GPIO 路径都通过。
[快照报告](../../research/ep7/candidate-snapshot-output-sim.json)新增 1322 条指令；
随后[几何配置报告](../../research/ep7/candidate-geometry-resume-sim.json)又新增 1086 条。

这是上游明确的未配置格式、无就绪设备、首次帧发布前的冷态结果。它关闭了这个
场景的完整回调返回待证项，没有关闭活动拍摄、真实任务交接或安装资格。

## 输出对象与实际执行

[输出探针](../../tools/ep7_candidate_snapshot_output_sim.py)只为 6229fb98 中原代码
明确写入的 160B 提供 A5 目的空间，不扩大为完整可读对象。最后成员之前的九个空洞
`123、145、155、160..165` 保持未映射；更后的区域也未因此放开。

|阶段|每条 GPIO 路径的指令数|结果|
|---|---:|---|
|原输出头部与 memcpy|240|header=1、word+124=0；121B 从实际格式栈记录复制，字节一致|
|输出继续|85|停在冷 fallback 对象 a2788dec 的 +12 指针读取|
|提供命名冷 fallback 条件后继续|88|停在 622a094c/8B 坐标记录的首项 halfword 读取|
|提供命名未发布坐标条件后继续|199|四个 halfword 实际复制；原输出构造器和回调返回|
|外层包装函数继续|49|原状态 setter 发布 0，完整返回 60409ecb，SP 恢复正确|

除输出 160B 外，六处原生转换结果 store 只增加 10B A5 目的空间，原
603f9f4c 状态 store 只增加 2B。转换中间值 `(83,74)` 与原厂整数乘除路径一致，
不是相机测量值；最终输出模式字段由原分支写入。四 halfword 复制、原输出构造器
返回 6042705e、回调返回 6041a224 和包装函数最终返回均有精确断言。

仅新增以下 12B 冷 BSS 条件，不作为活动记录：

- a2788df8/4B：606d5f1a 因原 state+53=0 选择 a2788dec fallback。其标志 1 和
  两个 −32768 已来自原冷 reset；这里只补其未发布指针为 NULL 的启动条件。
- 622a094c/8B：原厂四 halfword 复制的坐标记录。活动 writer 604288f9 在
  6028f3ef 被调用，会写 byte+0 与三个 halfword+2/+4/+6；该活动来源仍未执行。

原 124B 快照指针仍为 6229fc48，selector 为 `00 02`。包装函数的完整返回不表示
已经执行任务循环中的后续交换、消息收发或相机启动；上游 receive/log 调度切口保留。

## 恢复原几何配置

[续接探针](../../tools/ep7_candidate_geometry_resume_sim.py)仅在上述包装函数真正
返回之后恢复之前暂停的 configuration 栈、寄存器和原调用框架。没有构造新的
配置输入。两条路径在 60419f58 都得到原 getter 返回的 6229fc48 指针，各继续
543 条指令，统一停在：

`60427ec6 → read 622a06b4/2B，MDR 6005c8df`

原动态 setter 6042805e 尚未进入。27332B partial capture 保持原样，population
未恢复。续接新增观测栈深 880B；这是目前这条独立配置调用路径的观测值，不是完整
任务栈上界。

静态追踪已定位下一项来源：60425ba3 中的循环在 60425d03 从输入对象 +128 写
622a06b4，在 60425d0d 从 +144 写 622a06c4，在 60425d1b 从 +196 写 622a06f4；
对应八组 halfword/halfword/byte。604270d2 调用该生产函数，但其源对象与完整生命周期
尚未接通。下一步执行真实来源，不能把这些数组默认当作有效零配置。

后续[数组与原生临界区续接](CANDIDATE_GEOMETRY_ARRAY_SIM.md)已在明确首次发布前
条件下完成原数组 getter、控制器参数发布及临界区返回，继续到 62293d1c 状态读取。
活动数组来源仍未通过，未把这些冷态结果提升为有效拍摄参数。

## 复现与保留的停止点

```sh
python3 /repo/tools/ep7_candidate_geometry_resume_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

保留输出[首次指针停止点](../../research/ep7/candidate-snapshot-output-frontier.json)、
[坐标记录停止点](../../research/ep7/candidate-snapshot-output-fallback-frontier.json)、
[包装函数 store 停止点](../../research/ep7/candidate-snapshot-output-coordinate-frontier.json)、
[首次完整返回](../../research/ep7/candidate-snapshot-output-wrapper-frontier.json)和
[首次配置续接](../../research/ep7/candidate-geometry-resume-frontier.json)。最终只针对
新加入的返回、来源复制和停止点断言复核，没有重跑容器大循环或无关主机测试。

候选 004 和 fishcu 五组件研究包保持不变、不可安装。没有 SHA、固件重编译或
相机操作；活动帧、代码/RAM 所有权、完整生命周期、更新器及恢复仍待证明。
