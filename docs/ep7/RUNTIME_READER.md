# CPU reader 接入共享 runtime

2026-10-31。保留已有16条指令的post-builder桥与bounded decoder，仅替换原独立core
外部符号。`native_observer.c`从setup+4/+12读出request/output，调用
`ep7r_apply(&ep7_native_runtime_slot, request, output, 976)`。

`ep7r_apply` acquire-load发布slot，然后使用 `runtime.boot->core` 调用已有
`ep7p_direct_apply`。它与worker登记和撤销使用同一个core、job registry和poll锁；
不创建第二份registry，不查询当前UI或最后一个job。stop只停止后续producer准入，
在途冻结job可继续处理。未发布、已撤销、未知request或私有锁拒绝均保持stock输出。

原生合同仍是同步调用：setup/output及request在返回前稳定，job free之前已撤销；
不能把整数lookup当作任意指针有效性或跨cleanup复用的证明。该接入不补齐G1捕获源、
queue/task退出闭包，也不实现native UI、启动安装和代码放置。

验证范围：

- [host](../../research/ep7/runtime-reader-host.json)：真实bootstrap/poll/core和发布slot，
  用既有native-layout fixture构造登记job；发布后和stop后均只改变预期H lane，
  撤销后及poison后输出逐字节保持。strict与ASan/UBSan通过，native读/锁操作仍模拟。
- [stock](../../research/ep7/runtime-reader-current.json)：通过AST复用旧seam_probe的
  33个witness，重新核对当前输入；没有执行旧SHA保护入口。call603b02d9→603b0068，
  native frame96；返回处重新建立flags，保留已有MDR/volatile寄存器保存方案。
- [target](../../research/ep7/runtime-reader-target.json)：原桥16指令、两处relocation、
  observer八个setup byte读取、四参数传递及RET28通过。observer文本88字节，
  runtime reader局部栈20字节。所选49个对象未发现loop/extended寄存器使用。
  首次audit把objdump分支目标`e0 <label>`误识别为寄存器，修正为仅移除明确的地址标注；
  实际寄存器operand仍检查，重跑通过。

当前集合剩余20个外部符号：捕获源接口及19个原厂地址。旧九对象检查器仍作为partial
集合，已更新接口名和scope；旧报告保持历史内容。所有结果均为源/host/对象或静态证据，
未链接/整体编译固件、未执行相机代码，没有SHA校验。

下一重点是安装期间和退出时的queue/task存活约束、capture源身份/排他，以及G4原生
资源，随后汇总G6完整stack budget、放置/重定位与启动顺序进入编译前审查。
