# 基础 H/L：新 COLOR4 捕获的取值与延迟交接

2026-11-01。使用已由原生allocator、population和event4b邮箱产生的新节点，
完成backlink发布后的H/L取值、延迟FIFO及重填充撤销检查。新增55,434条指令，
最大观察新增栈深368字节。[探针](../../tools/ep7_candidate_selected_handoff_sim.py)与
[报告](../../research/ep7/candidate-selected-handoff-sim.json)保留准确边界。

本节点按基础H/L首版收敛后的契约范围执行。原selected handler中的曝光/格式
处理尚未完整运行；不为metadata+48/+50/+52填入任何结果，也不继续原失败栈。
使用独立现场进入该handler实际的602a2901..602a2906两条发布指令：D2来自实际
邮箱中的新node61b21fc0，A3为原handler约定的node+8。只有associated+8的4字节
从原只读夹具开放为写目的，初值不改，其余对象边界保持不变。

## 实际检查

|场景|结果|指令|
|---|---|---:|
|associated仍引用旧node|候选返回false，输出保持CC，新封存代际不变|8,610|
|原厂backlink发布|写入实际新node61b21fc0|2|
|实际新代际取值|ID2/af6037c0得到COLOR4冻结H0=5、L0=-3|9,049|
|实际patched等待队列入队|返回4，使用原FIFO第二个位置|9,916|
|capture重填充前撤销|实际候选撤销排队快照|8,813|
|正常原生出队|32字节scope携带ID2和冻结值|9,625|
|撤销后原生出队|同一个associated正常出队，scope全部清零|9,419|

FIFO的count/tail/head按0/1/1 → 1/2/1 → 0/2/2迁移，两条出队分支完全相同；
撤销不会丢失原厂队列元素或改变顺序。两份27332字节新旧capture逐字节不变，
私有锁正常释放。冻结值仍是拍摄采样时的5/-3，没有读到后来改成的当前设置-3/2。

这关闭了原生新capture与候选取值/FIFO契约之间的具体间隔。不能据此声称完整
selected handler、controller调度、并发释放闭包或最终照片像素已通过；原曝光/
格式处理作为明确边界保留，未用API成功stub替换它。队列出队祖先栈仍使用已有
探针的显式调用契约。后续集中验证GUI与已修改worker消费边，不扩大未修改原厂
内部字段的初始化重演。候选004和五组件包未变，无SHA或相机操作。
