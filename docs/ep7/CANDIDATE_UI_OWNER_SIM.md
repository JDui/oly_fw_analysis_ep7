# E-P7 原生文字控件与 owner 撤销

2026-11-01。候选004实际链接的screen/cleanup/bulk/destructor桥及原厂文字控件路径
通过定向检查，共16,637条指令，观察最大新栈深408B。未修改固件、重新编译对象或
重跑host测试全集；候选和fishcu五组件研究包保持不变。

## 实际执行

请求278完成是显式输入边界：服务2880B、owner1360B和当前GUI任务均按已审查布局
提供；不把模型当成原屏幕管理器的完整构造过程。之后执行候选screen_leave、原厂
factory60d337b2、文字构造/资源初始化、attach60d02beb、find60d02cc2、bind60d0487a
和setter60d4c9df。控件为180B，原生头部type8010/ID7e10、parent和双向链表节点
全部回读正确。候选取得generation1、ready和bound，原服务上下文fe81恢复。

原setter依次写入UTF16「H 01 +3」「L ALL -2」。真实长度、分配大小、文字复制和
generation输出均检查；第二次相同文字没有分配、释放或绘制通知。screen桥保持
原管理器模型的D0/D1/A0/A1返回值，各调用保持SP及callee-saved寄存器。

只对一个重要错误边界注入失败：原setter先释放旧文字，新分配返回NULL。实际机器码
返回0、文字指针清零，候选active/display_ready关闭、busy释放，generation输出
未写；child及parent membership仍保留给正常清理。后续有效文字更新返回0，没有
重试分配，也没有重新打开编辑资格。

分别运行完整原cleanup60d43d4b与bulk60d42d69：候选引用先撤销，generation变2，
随后原厂布局、字符串、180B child和12B链表节点释放。每次free前检查候选owner/
text引用已经清零；释放的payload立即从严格模拟器撤去，后续访问将产生fault。
两条路径都返回、链表归空、全部模型分配回收；有效文字的迟到更新均拒绝。
cleanup后原destructor60d7ab79也返回正确的原deallocator60cfe5c9，无重复释放。

## 边界与首次失败

底层new/alloc/free、绘制通知和两把GUI锁为显式模型；锁只允许单任务成对获取/释放。
原GUI消息队列和10个timer为空输入，原清理代码实际检查这些数组。未执行renderer、
pending消息竞争、真实分配器或LCD。MVC尚未注册，当前文字调用也不证明编辑receipt、
COLOR门控或完整GUI编辑链。

实际冷清零桥先运行；16KiB GUI栈及resident helper复用已有输入契约。408B是当前
调用链观察值，不是完整GUI/IRQ栈上界。owner/service存活和request278完成仍是模型
条件，不能用头部/表地址匹配替代真实生命周期。

最初cleanup在原GUI锁cell61fb2a28处停止；明确上述锁及空队列模型后完整返回。
首个CLI又因探针把子清理计数点写成自带prologue的60d02bfe而拒绝：原CALL实际到
60d02c03，frame32。修正探针计数地址后完整exit0，固件代码未变。未执行SHA或相机操作。

本节点关闭条件输入下的原生控件挂接、文字更新、OOM停用及撤销后释放问题。
下一步接通基础H/L编辑会话与现有原生输入证据；worker、驻留、物理更新入口和恢复
条件仍单独保留，当前包仍不可安装。

[工具](../../tools/ep7_candidate_ui_owner_sim.py) ·
[机器报告](../../research/ep7/candidate-ui-owner-sim.json)。
