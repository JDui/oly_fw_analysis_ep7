# 当前原厂输入准备：无 SHA 的结构证据

日期：2026-10-30。官方目录下载已完成，111017984字节；五组件结构、原生加法
校验和及无改动回转均通过。整包主程序与先前完整首组件逐字节相等。原厂文件、目录签名响应、解码结果
只留在 git 忽略目录，不进入提交。

## 获取与准备

复用既有公开目录客户端，固定期望版本，省略可选下载哈希记录：

```sh
python tools/om_firmware_catalog.py --model-id 1420 --model-name E-P7 --expect-version 1100 --no-hash --download --out firmware_files/ep7-1100-catalog
```

输出目录必须新建；运行中的下载不得再运行一次。`--expect-version` 检查的是目录
实际提供版本，不把 installed 参数当历史版本选择。`--no-hash` 不删除原有型号、
官方 HTTPS URL、文件名和长度检查；默认行为仍记录哈希。

主程序组件已有完整边界时，可以只检查第一组件：

```sh
python tools/ep7_prepare_input.py --stock firmware_files/ep7-1100-catalog/OLY_E_142_1100_0000_0000.BIN --out generated/ep7/main-input --main-component-only
```

本次实际检查26214400字节：kind0100、model1420、build1100、payload26214336、
container406a0000；复用 `oly_container.parse/encode` 完成头尾匹配、原生加法校验和、
无修改回转逐字节相等；入口指令/操作数符合 runtime base60020020。
[实际结构报告](../../research/ep7/main-input-structure.json)明确 whole_container_checked=false。
这里的回转相等仅比较当前输入自身，不表示与历史研究输入逐字节相同，也不证明厂商签名。

已另建 `generated/ep7/full-input`，去掉 `--main-component-only` 执行五组件检查。
[完整实际报告](../../research/ep7/full-input-structure.json)与
[本次官方来源记录](../../research/ep7/stock-source-current-no-hash.json)保留无SHA证据边界。
默认完整模式拒绝长度不足的下载；第一组件模式不把后续残缺数据当作已验证内容。
工具不改镜像，不生成可安装包，不访问相机。旧精确 SHA 检查器保持原状，不能把本工具
结果写成那些检查器通过。后续静态研究须重新核对实际使用的指令/操作数。

## 从实际主程序得到的别名候选

复用 `penf_disasm.refs`，新增显式 base 参数，保留 PEN-F 默认值；E-P7 使用60020020。

```sh
python tools/ep7_alias_candidates.py --main generated/ep7/main-input/main.decoded.bin
```

[候选结果](../../research/ep7/alias-reference-candidates.json)：

|对象|字面地址引用候选数|下一步|
|---|---:|---|
|global6223dd54|4|重点核对2941、3066、30b1、4344周围的 load/store 与清除顺序|
|async descriptor6223df64|1|核对300d附近的提交接口、完成回调和取消|
|callback6029e8f1|1|3001字面引用；零直接相对call候选不能排除间接调用|
|wrapper queue6223e2f0|8|除已有事件4c/43外，核对c634初始化、43dd/43ee及78f4附近路径|

以上是数据字节匹配，地址表示字面值位置，不一定是指令起点。没有反汇编就不能
把它们标成已审读写或完整引用集合；间接计算地址也可能不含这些字面值。
GNU binutils2.45 源码仍在下载，完成后构建本地 MN10300 objdump，再检查这些窗口。

## 本轮最小验证

目录客户端3项定向测试通过：不调用SHA、拒绝其他版本、拒绝短下载。
引用扫描器2项通过：显式E-P7基址下16/32bit相对call与字面引用，原PEN-F默认基址不变。
没有重跑完整测试集；上述主程序结构检查是实际输入执行，不是合成fixture。
