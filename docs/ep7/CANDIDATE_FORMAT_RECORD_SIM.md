# E-P7 原厂诊断缓冲区与格式记录复制

2026-11-01。[探针](../../tools/ep7_candidate_format_record_sim.py)继续原厂冷初始化，
执行两次固定池分配、诊断记录初始化及格式状态记录复制，再恢复原快照 producer。
[正式报告](../../research/ep7/candidate-format-record-sim.json)覆盖原有两条 GPIO 输入，
新增 55234 条指令；每条路径为冷初始化后缀 26872、记录重置前缀 240、producer 505。
最大新增观测栈深 564 字节，仍不是完整栈上界。

当前严格停在 6030b752 读取 a273104a/2B，MDR 60309e5c。这里的原厂 getter 用历史
索引选择 a2731098 起的 980B 记录。完整快照、几何构造与 capture population 尚未
完成；原 27332B partial capture 保持不变。候选 004 与 fishcu 五组件研究包未改。

## 原厂冷初始化后缀

[共用 helper](../../tools/ep7_candidate_diagnostic_buffers.py)复用已审查的固定池布局，
从此前 60556bb2 的实际寄存器/栈现场继续，60556b1e 完整返回后才执行核心前缀与
ready 发布。6055761a 两次调用原厂 60022700 → 600228b6，各申请 16384B；没有替代
分配器或手填返回指针。实际分配 CPU0/class2 的槽 0、1，返回 61bd6d40、61bdad80，
stride 16448；原厂 counter=2、bitmap=3，指针和两个初始游标均核对通过。

两份 payload 从 A5 开始，原厂各初始化 1024 条 16B 记录：首字节 3f、+8/+12 两个
word 清零，另外七字节保持 A5。全部 2048 条记录逐字节核对，槽后 64B guard 未映射。
原厂分配器的本核中断级屏蔽及恢复也已核对。

本场景显式依赖原厂 BSS 范围内的 8B 空池 counter/bitmap 和 8B 空 buffer 指针。
分配期间临时提供 8ff006fc=0、8ff00040=0 的既有 pre-kernel 锁模型，随后移除。
因此“完整冷初始化已执行”仅针对这个有条件场景；真实池占用、完整启动时点、多核
并发和代码/RAM 所有权仍归 S4，未由本节点证明。

## 格式记录与真实诊断写入

源记录 a2788cf6 的三字节已由原厂冷初始化写入（halfword 100、byte 0）；其余七
字节只在已定位 BSS 清零和 cached/uncached alias 一致的条件下取 0。目标 a2788cec
缺失的七字节从 A5 开始，保留已有三字节，不把活动状态视作已知零。仅合并两个
来源完整的 10B region 以允许严格 halfword 读取；邻接未知字段继续未映射。

606d4593 实际执行到 606d4645，在此之前的五次 halfword store 将 +70 源复制到 +60
目标，得到 00006400000000000000。原 producer 的五次 getter copy 随后逐项核对
源/目标地址与数值。另有八字节状态写入位置从 A5 开始，由原厂重置代码填写。
606d4593 余下状态写入和模式 helper 未执行，完整 reset/startup 顺序仍待接通。

诊断路径实际调用 605576bb 和原厂时间戳函数，记录首八字节为 `init    `，参数为 0。
9890014c 的只读固定输入 3fffedcb 经原厂减法产生 00001234，确实写入第一份日志的
+8 word；游标为 [1,0]，第二份日志首记录保持原初始化内容。时钟频率、真实经过
时间和外设中断没有被该输入模型证明。

## 复现与后续

```sh
python3 /repo/tools/ep7_candidate_format_record_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-004 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103-mulqu
```

保留[未增加最终断言前的停止点](../../research/ep7/candidate-format-record-reset-frontier.json)。
正式报告固定精确 fault，并核对诊断记录、游标、五项原厂复制和 capture 不变。
下一步追踪 a273104a 历史索引及 980B 记录的原厂初始化/发布，不把索引补零当作
有效拍摄记录。没有 SHA、无关测试、重编译或相机操作；S3/S4/S5 整体资格仍未通过。
