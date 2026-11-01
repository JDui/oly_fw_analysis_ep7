# EP7HSL 006 交付记录

2026-11-01。源码`a059e5f`，修正未绑定拍摄任务时的误停机并增加原厂AF故障提示。
005实机黑屏的唯一根因没有确认，006尚待正常开机及H/L实测；不是已通过机身验收版。

最终构建目录：`generated/ep7/flash-build-006-r2/`。
交付目录：`generated/ep7/flash-packages/EP7HSL-006-EXPERIMENTAL/`。
ZIP：`EP7HSL-006-EXPERIMENTAL-SD.zip`，内含独立install与restore-stock。
每个BIN为111,017,984字节；详见[安装及验证说明](EXPERIMENTAL_SD_006.md)。
ZIP为82,790,811字节，11项归档内容的CRC/全字节回读通过；见交付目录中的
`delivery-check.json`。没有把早期失败修订放入安装目录或ZIP。

106对象、98补丁，沿用原工具链与fishcu封装。最终修订增量编译1对象、复用105对象；
整个006变更涉及2个生产源文件。代码两区使用23,096B/23,711B，私有BSS8,088B；
原厂启动前缀、CPU2池32槽和8KiB私有镜像初始化布局保持。

|定向证据|范围|
|---|---|
|[boot guard](../../research/ep7/candidate-006-boot-guard.json)|未绑定回退、后续正常绑定、已绑定异任务仍拒绝；原厂AF-helper参数/终止保持|
|[GUI](../../research/ep7/candidate-006-ui-editor.json)|最终候选编辑、文字、重放拒绝与冻结；含明确的构图/输入/显示模型|
|[worker](../../research/ep7/candidate-006-worker-job.json)|实际分配、生命周期和H/L系数；处理完成服务含模型|
|[residency](../../research/ep7/candidate-006-residency.json)|实际原厂加载复制与候选字节；不含物理缓存|
|[SD isolation](../../research/ep7/candidate-006-sd-isolation.json)|修改区不映射条件下的原生选包/转交，1,624条指令|
|[container](../../research/ep7/candidate-006-package.json)|fishcu五组件封装、原生加和校验及回读|
|[updater](../../research/ep7/candidate-006-updater.json)|实际包由fishcu解码后，原生mode1五项写入路由被截获；后端失败停止|

未重复完整原生mode2解码；没有SHA、真实flash写入、真实LCD/照片或006机身启动验收。
原厂回刷文件与官方输入逐字节相同；005原文件与ZIP保留。首次失败修订没有交付：
定向检查发现新AF数字CALL被汇编为相对位移，已改为原有绝对符号绑定流程，最终r2
通过原厂helper入口的实际执行核对。该开发错误不在005，也不是005黑屏根因。
