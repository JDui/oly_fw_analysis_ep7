# E-P7 冷态参数数组与原生临界区续接

2026-11-01。两条 GPIO 路径均完成五组参数数组的原生复制，60427dac 返回到
604276a7；随后原厂临界区及 6041c6b4 参数处理函数完整返回到 604276b3。
这两步新增 3012 条指令，当前停止点为：

`603f9f3f → read 62293d1c/2B，MDR 603fbece`

动态 setter 6042805e 尚未进入，27332B partial capture 保持原样，population
尚未恢复。该结果限于已有的未配置格式、无就绪设备及首次数组发布前场景。

## 五组数组的来源与复制

[数组探针](../../tools/ep7_candidate_geometry_array_sim.py)仅增加 72B 明确的首次
发布前 BSS 条件，五段均为只读。原厂启动清零范围覆盖这些地址；没有执行完整启动，
因此仍是条件，不能把其零值当成活动拍摄参数。

|源地址|480B 参数对象内偏移|大小|原生元素复制次数|
|---|---:|---:|---:|
|622a06b4|128|16B|8 halfword|
|622a06c4|144|16B|8 halfword|
|622a06d4|160|16B|8 halfword|
|622a06e4|176|16B|8 halfword|
|622a06f4|196|8B|8 byte|

原 getter 的两个循环真实执行，40 次 store 的计数及最终源/目的字节一致。
每条 GPIO 路径继续 305 条指令，停在 6006a922 对 8ff006fc 的读取。
[正式报告](../../research/ep7/candidate-geometry-array-sim.json)保留复制地址和寄存器，
[首次报告](../../research/ep7/candidate-geometry-array-frontier.json)保留原始停止点。

活动写入路径的静态证据已细化：60425ba3 只有在属性 9121 返回 1 时，才从输入
对象的上述偏移发布五组数组。调用点包括 60426eb7、60426ef8、604270d2、604271c8
和 60427201。回调参数 +4 来自 60419fc7 的原生构造，进一步连接到 603fa833
选择的四槽、每槽 480B 参数池。603fa59a 会写入 1792、−768、768 等默认值及
子记录指针，并不初始化上述数组偏移。活动记录的构造、回调传输及生命周期仍待执行；
本探针没有把整槽补零，也没有声称完成活动 writer。

随后[原生参数池探针](CANDIDATE_PARAMETER_POOL_SIM.md)执行了完整池初始化、
槽 1 领取、603f9e49 默认重置和 mask 发布；它生成的数组包含 768、32767、
−32768。这验证了默认记录的生产路径，活动 writer 和消费回调仍未执行。

## 原生参数发布与临界区

[临界区探针](../../tools/ep7_candidate_geometry_critical_sim.py)执行控制器原有
602ad983..602ad994 片段：它在栈上写两个零字段，调用完整 6042200b，经
603f3942 / 6041c686 把 4B 参数发布到 622a04a6。目的空间从 A5 开始，最终
`00000000` 来自真实构造和 memcpy；不是直接提供参数值。该片段每条路径 99 条指令。
其外层控制器分支和完整消息生命周期仍是切口。

随后复用已有 CPU0 单任务内核模型、TCB、ready list 和 task flags，只新增两个
明确的系统寄存器输入：8ff006fc=77777777、8ff00040=0。原厂 6006a922 进入正常
启动后的分支，实际执行 6003138f 关闭调度；6006a96b / 60031477 随后恢复调度。
中间的四字节复制、PSW 保存恢复和参数处理均为原指令，没有 API 成功替身。

另有 622a04a4 的 1B 前次结果采用冷 BSS 条件；622a04a0 的 4B 结果从 A5
开始，由原代码覆盖。当前参数的 enable 字段为零，原厂分支不进入 603fe72d 的
活动参数计算。临界区续接每条路径 1102 条指令，断言确认：

- 调度关闭、恢复各一次，未发生任务切换；共享锁和本地锁均释放。
- task flags 恢复 `000000`，dispatch flags 恢复 `00`，原 IRQ 掩码恢复。
- 6041c6b4 完整返回，四字节结果和前次结果标志由原代码写为零。
- 再次继续到上述 62293d1c 停止点；动态 setter 尚未进入。

[正式报告](../../research/ep7/candidate-geometry-critical-sim.json)新增 2402 条指令，
新增观测栈深 928B。它是这条独立调用路径的观测值，不是完整任务栈上界。
保留[缺少参数时的首次停止点](../../research/ep7/candidate-geometry-critical-frontier.json)
和[首次发布后续接](../../research/ep7/candidate-geometry-critical-published-frontier.json)。
首次停止时尚持有调度锁，不能误当作完成；正式探针已验证完整释放。

## 复现与下一项

```sh
python3 /repo/tools/ep7_candidate_geometry_critical_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

下一步追踪 62293d1c 的原厂初始化及状态更新，再继续配置构造、population 和
worker 生命周期。当前候选 004 与 fishcu 五组件研究包保持不变且不可安装；未做
SHA 校验、重编译、相机连接或刷写。活动拍摄、代码/RAM 归属、完整更新器及独立恢复
仍未证明。
