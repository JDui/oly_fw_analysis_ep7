# 生命周期 hook 证据清单（编译前 G1）

日期：2026-10-30。依据仓库已保存静态探针与研究记录；本轮未读原厂字节、未做 SHA 校验。
本轮查明的是本地证据清单的一致性，不是新增固件反汇编或完整释放闭包。

## 节点释放义务

|原生 call 地址|路径|审查义务|
|---|---|---|
|`0x602a31b1`|allocation/population failure cleanup|state33 内撤销/排他性待绑定|
|`0x602a4461`|consumer cleanup; capture retirement conditional on node+44|state33 内撤销/排他性待绑定|
|`0x6029f1c2`|shared node queue drain|共享队列/替代回调可达性待排除或覆盖|
|`0x602a4220`|event43 first queue drain|state33 内撤销/排他性待绑定|
|`0x6029f6ba`|alternate callback event55 old node|共享队列/替代回调可达性待排除或覆盖|
|`0x602a29ab`|event42 associated+6==1 conditional completion|条件分支资格待排除或覆盖|
|`0x602a2a00`|event42 normal completion flags0x18|state33 内撤销/排他性待绑定|
|`0x602a2a48`|event4d conditional completion flags0x30|条件分支资格待排除或覆盖|
|`0x602a2ab5`|event4c normal completion flags0x18|state33 内撤销/排他性待绑定|
|`0x602a427d`|event43 second queue drain wrapper[0]|state33 内撤销/排他性待绑定|
|`0x602a44d8`|event4c helper446d completion|state33 内撤销/排他性待绑定|
|`0x602a2cb9`|state34 event42 completion|离开33前同步撤销未证明，不能直接豁免|
|`0x602a2d0d`|state34 event4c completion|离开33前同步撤销未证明，不能直接豁免|

以上13项均没有安装 hook。原生 call 操作数与文档描述来自已有探针；具体 wrapper 的
寄存器保存、栈、flags、MDR 和 hook 放置仍须逐点设计，表中地址不是补丁清单。

## 必须分开的其他生命周期

- `6029f6c2` / `6029f6cb`：callback envelope / arguments。
- `602a4286`：四字节 wrapper；真正 node free 是前面的 `602a427d`。
- `602ac4d2`：metadata free（见 KIND19_METADATA_LIFETIME），不属本次三组节点 witness 集合。
- `602a2b6f` / `602a2b77`：另一 envelope / arguments 路径（文档证据，本次未在清单核对）。
- capture pool 释放与 node free 不是同一事件；已按值复制的 H/L snapshot 也不应随 node 清除。

## 状态边界与裸指针限制

两个已有 service seam：`60289c5e`、`60289d02`，原调用均为
`6028a882,[d2,d3,a2,a3],32`。观察必须在原 service 返回之后；它本身可能释放节点或请求新状态。
每次实际 old33 commit（包括33→33）撤销；255 不提交。初始化也必须建立独立新 runtime。
只有在该完整契约成立时，state34 的节点 free 才不会留下仍然有效的旧33 sidecar。

`ep7c_resolve_live` 解决当前 registry 内的查询，不证明调用者持有活对象。
把 event/queue 中的旧地址交给它，在地址复用后会取得新 token；这是本轮路线审查保留的硬边界。
所有原生 prefix 读取必须先有独立存活/排他性证明和 sidecar authorize，不能用反向读取来证明自己。

## 下一项具体研究

1. event4c 分支把 node 放入新分配四字节 wrapper，再入 queue6223e2f0；event43 drain 先 node
   后 wrapper。需证明普通 completion 与 drain 的排他性、取消/退出何时清空，以及重复通知归属。
2. global6223dd54 与 async descriptor6223df64（callback6029e8f1）保留别名；追踪使用结束、
   取消和重新赋值，不从“普通 event 表完整”推断这些通道已关闭。
3. 同一 controller 处理程序的顺序并非跨任务/中断锁；补齐 deferred service、secondary cancel
   及重入边界后，才决定可用 callsite wrapper。
4. G2 的 metadata/descriptor 不能重新查当前 node token；要输送持有的能力或按值快照。

本机当前没有原厂输入和目标反汇编器，因此这些新的机器码结论仍待输入准备，
不通过删除旧 SHA guard 把缺失重验包装成通过；本轮只运行不依赖二进制的清单检查。

## 本次可复现检查

```sh
python tools/ep7_lifecycle_inventory.py
```

该工具只 AST 读取四个已有探针的字面指令 witness，不导入探针、不读固件、不执行目标代码。
它逐项核对13个 node free、3个非 node free、2个 service call，并检查所选三组 witness
中的全部 heap free 已分类；清单漏项或指令变化会失败。它不能发现这些窗口外的释放。

[执行结果](../../research/ep7/lifecycle-hook-inventory-check.json)；
[结构化清单](../../research/ep7/lifecycle-hook-inventory.json)；
[总计划](PREBUILD_PLAN.md)。

依据：[原五处与共享队列](EXPANDED_NODE_FEASIBILITY.md)、
[普通完成反例](NODE_DISPOSAL.md)、[状态/新增释放](NODE_STATE_TABLES.md)、
[状态观察](NODE_STATE_GUARD.md)、[metadata ACK](KIND19_METADATA_LIFETIME.md)。
