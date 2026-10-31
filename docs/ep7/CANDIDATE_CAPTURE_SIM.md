# 候选控制器冻结与原生延迟 FIFO

2026-11-01。S3 的 controller/source adapter 与延迟 FIFO 子节点通过。
[探针](../../tools/ep7_candidate_capture_sim.py)复用 S2 实际发布的 runtime、已有严格
引擎和控制器 fixture 格式；[报告](../../research/ep7/candidate-capture-sim.json)
记录 23 段调用/208,056 条指令，包括原生 helper 搬运。生产固件与模拟器均未修改。

## 真实执行链

1. 核对原厂 task row `60039664` 的 ID73、入口 `60289852`、4 KiB 栈；明确切换
   TCB fixture 后执行候选 state observer。实际任务创建/调度和原厂 state commit
   未执行。引擎 callback/mask、associated pool/node/capture registry 是已有格式的
   现场数据，完整 native population 函数未执行。
2. 按既有加载证据，将 decoded `6143ca00` 的 6,144 字节提供为已驻留的
   `a143ca00` source alias。实际执行 `60020297..600202af` 的启动复制循环，
   **10,756 条指令**后目的 `47000800` 的全部字节与源一致，再设为只读可执行。
   后面的 `47001052` 是原厂复制 helper，不是 memcpy stub；flash 读取/cache 未模拟。
3. 执行候选 fresh 登记、实际 patched lookup/prewrite sites `602a7ea0` 和
   `602a8dca`、候选 sample/finish 与 source snapshot adapter。原生 lookup
   `6029b9d1` 由已有 GNU 模型执行，ID1 实际定位 `6223d190` 的 24 字节 registry
   行并读出 capture 指针，不再用主机函数代替 lookup。
4. COLOR2 的 H0=5、L0=−3 在 sample 时冻结；finish 前改为 H0=−3、L0=2，
   snapshot 仍是原值。其余 22 项保持零。
5. 从原厂初始化前缀 `602abe7b` 执行候选 wait-reset 和真实 FIFO initializer，
   得到 tag182、capacity25、element4、空 count/head/tail。
6. 实际 patched enqueue `602ac3f6` 执行原生 `6020b98b` 和复制 helper：返回 4，
   slot0 写入 associated，count/tail/head 为 1/1/0。实际 patched pop `602ac5e8`
   执行原生 `6020b9ff` 和复制 helper：返回同一 associated，计数变为 0/1/1，
   32 字节 scope 正确取得冻结 snapshot 和 available 状态。两段分别 14,786 和
   9,625 条指令。

pop 的原生 CALL 实际建立自身 24 字节 frame；外围两层 ancestor return word 是
明确的栈 fixture，不表示外层 controller service 已端到端运行。最大观测栈深相对
本次 caller SP 为 **368 字节**，不替代完整 controller/IRQ 栈界。

## 三个关键撤销边界

- **排队后再次 prewrite**：候选在 capture 重填前撤销对应等待项，原生 pop 仍返回
  原 associated 并维持 FIFO 顺序，但 scope 全零，不把过期快照传给 producer。
- **过早 source copyout**：未 seal 时先观察一次，随后补齐 prewrite/sample/finish
  仍不产生快照；不能在后续时刻重新采样当前设置。
- **节点释放后旧 backlink**：真实 `ep7cn_free` 撤销后取消 node 内存映射，再由
  associated 发起 snapshot 查询；正常返回 false、不读 node，输出未改写。

这关闭了之前 controller 原生 lookup、等待队列搬运仍由 host mock 替代的执行空缺，
但不关闭所有异步别名、真实分配/释放来源、并发排除或地址复用证明。

## 后续与复现

下一步连接 queue4b 的真实消息发送/接收及 materializer/worker，保留 post-send
通知和失败回收。当前仅到延迟 FIFO 交接，不能说整个 S3 或相机拍摄链已经通过。
加载/所有权、完整栈、更新器接受性和独立恢复条件继续保留，候选不可安装。

```sh
python3 /repo/tools/ep7_candidate_capture_sim.py \
  --candidate /repo/generated/ep7/offline-candidate-003 \
  --tool-prefix /work/install/bin/mn10300-elf- \
  --engine /work/ep7-mn103-sim-87ffb882-complete/build/ep7-mn103
```

沿用禁网容器、只读仓库/工具卷；无 SHA、API 成功 stub、对象重编译、更新包或相机操作。
