# Origin Edit Lab

让放进 PowerPoint 的 Origin 图，仍然是一张能继续编辑的图。

这个项目探索 **保留原始 Origin 源对象的数据与图形编辑**：改变数据或参数后，仍能在 Origin 中打开、调整、保存，并正确回到 PowerPoint。当前是研究起点，不是完整的 Origin 替代品。

## 目前做到哪里

- **原生数据写回实验**：对一个严格限定的 Origin OLE 模板，在既有压缩记录的空间内写入两列、各 9 个数值。双解码器核对数值，保留图对象、X/Y 绑定、其他流及未知字节，支持精确恢复。
- **新版结构与有限原生字段实验**：从数据集根记录顺序建立工作表/图形引用，只在完整、已识别的数据集与页链上，尝试四类存储整数字段的等长修改。未知结构拒绝；数字数组解码、Origin 界面单位和应用重开验收仍不在支持范围内。
- **容器与预览工具**：检查 PPTX/OLE、提取 CFB 流及 WMF 中的 EMF；按明确选择器修改 SVG 外观，并替换支持布局中的 PPTX 预览。这些工具单独存在，预览修改不会改变 Origin 源对象。
- **布局提案与对照**：先展示参考线提案并取得明确确认，再按精确对象与锚点执行。新增只读审批绑定校验和同画布像素叠加工具；它们不自动画参考线、移动对象或修改 Origin 源数据。
- **测试基础**：公开的合成样本测试不依赖真实科研文件。严格拒绝不支持的输入、覆盖输出、越界编辑等情况。

**最关键的验收还没完成：真实 Origin 打开、重算、保存、再次打开，以及 PowerPoint 激活与更新。** 字节保留和解析通过，不能代替应用验收。原生写回实验保留的显示缓存是旧图，不能把它当作新数据的绘图结果。当前也不支持任意 OPJU 写入、从零创建完整 Origin 图或通用原生样式编辑。

## 快速开始

Python 3.10+；本次测试环境是 Linux、Python 3.12。原生实验的原子输出目前仅支持 Linux `renameat2(RENAME_NOREPLACE)`，不静默降低保护要求。

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -B run_tests.py
```

默认测试只使用合成数据；需要外部真实样本的测试明确标为跳过。没有捆绑原始研究 PPT、OLE 模板、用户文件或测量数据，也没有自动下载它们。

只读检查：

```sh
python preview/pptx_origin.py inspect presentation.pptx
python preview/cfb_extract.py object.bin --report streams.json
python preview/compat.py project.opju
```

`compat.py` 只记录大小、签名提示和哈希，不证明文件有效或兼容。实际预览操作见 [预览工具说明](docs/preview.md)。原生实验见 [原生数据实验](native/README.md)。

多面板排版见 [视觉布局流程](docs/visual-layout.md)、[参考线提案与审批校验](docs/alignment-plan.md) 和 [字体与配色选项](docs/style-options.md)。这些是独立的外观工作流；审批 JSON 不能自行证明用户授权，像素叠加也不能证明 Origin 原生可编辑性。

## 独立运行的读取验证

[Ropj 原生工作簿读回实验](research/ropj_readback/README.md) 使用真实 Ropj API，在四份合成旧版 OPJ 上核对了 1,761 个 binary64 数值及 12 组列长名/单位。它与 LabPlot 共享 liborigin 祖先，不是独立设计的解析器；不支持 OPJU，也不验证图形。仓库仅包含验收源码、合成单测和事实摘要，不包含 R/Origin 二进制或原生样本。默认测试明确跳过需要外部运行时和样本的用例。

## 有限原生样式研究

[旧版 OPJ 样式字段实验](research/legacy_style_fields/README.md) 对两个精确哈希锁定的公开模板，分别修改刻度字号、轴线宽、曲线线宽和图层矩形。8 项变化由实际 LabPlot 导入重绘独立复现，数值与已识别的 EMF 缓存保持不变。代码不改预览，也不是任意文件编辑器；字体和矩形探针可能产生标签重叠，不能当作排版成品。Origin 重开/保存、新版 OPJU 和完整原生单位映射仍未验证。

[旧版原生图有效行数实验](research/legacy_active_rows/README.md) 在一个固定分配 50 行的公开模板中，验证了 7、49、50 行有效前缀。实际 LabPlot 读回了逐位一致的数值，并发出相同数量的原始曲线点；原生图和绑定保持不变。51/257 行扩容明确拒绝。未使用的源数据仍保留，因此它不是数据清理器，也不能视为任意行数写入或 Origin 重开验收。

## 新版原生绑定诊断

[新版 CPYUA 绑定反例](research/modern_binding_diagnostics/README.md) 是只读、源码级研究补充。在 110 份哈希锁定的公开输入中，复现了固定版本解析器用工作表 X 替代图形自身 X、并合并不同工作表同名列的问题。313 个显式属性 ID 候选中，295 个属于五份候选覆盖完整的文件，另 18 个仅属于三份局部映射。描述符和图锚点仍是候选，不构成完整类型化数据集语法；X=0 不得猜成 A 列。代码不修改原生文件，不包含原生样本、第三方运行时或私有数据，也没有完成 Origin 打开/保存验收。默认测试只使用合成数据，外部复现需要明确指定公开输入与已核验的固定版本依赖。

## 新版图形对象结构研究

[只读图形归属解析](research/modern_owner_walk/README.md) 在已识别的新版图页内，按文件记录顺序追踪图层、标题、曲线和轴参数，而不是按最近出现的名称猜测归属。公开 110 份输入中走通了 105 个图页、120 个图层和 2,717 条曲线；页的初始发现仍是候选扫描，未知对象会停止解析。独立的 LZ4 实验还复核了 182 个压缩属性块的字节一致性，但没有据此推断属性含义。此补充只读，不提供通用原生编辑或 Origin 重开验收。

## 新版根记录、引用与四类字段研究

[严格根记录与引用读取](research/modern_native_binding/README.md) 从 prolog 开始，顺序读取完整数据集列表和页链，以原生选择器与所属记录确定工作表列和曲线引用，不再依赖页扫描或最近名称。原公开样本中 101/110 份、独立公开样本中 24/57 份完成受限数据集与页段；这不是完整项目支持率，后续项目尾部仍未知。它不解码数值数组，也不把 X=0 猜成 A 列。

[有限原生标量写入](research/modern_native_scalar/README.md) 只支持 type200 曲线线宽、具名轴标题字体、刻度字体与轴线宽四类**存储整数**。每次写入都经过完整根链检查、精确归属、外部哈希锚点和一对一 literal 字节来源验证；不改变压缩控制、零位模式或长度，不编辑 repeat 支撑的字节。输出只能独占创建新文件，原生、CFB 和单个 PPT 嵌入对象的变更均能精确恢复。

公开 110 份样本中 101 份通过结构门槛，共有 385 项单字段实验；另有一个公开 PPT 的四字段串行实验，逐字节保留非目标流、其他成员和显示缓存。包只含源码、合成测试及公开来源证据，没有原生样本或测量数组。这些字节检查不能证明 Origin 界面单位、打开、刷新、保存重开或 PowerPoint 激活；这些应用兼容性与生命周期仍**未通过验收**，macOS 写入未验证。显示缓存保持旧图，不能视为新字段的渲染结果。

## 旧版原生图容量扩展研究

[带图模板的 51/257/1024 行扩容实验](research/legacy_allocation/README.md) 对一个公开旧版 OPJ 模板重新分配数据记录。官方 LabPlot 2.12.1 的独立实跑逐位读回全部 X/Y 数据，并产生对应数量的真实曲线点，保存后的数据、原图样式与绑定也经过检查。这是明确选择后才会运行的 **LabPlot-only 研究模式**，不是安全的 Origin 导出：若干旧范围字段和未知依赖仍保留，Origin 的打开、刷新和保存重开未验证，默认导出继续拒绝。包只含源码、合成数据和有限证据，不含原生模板或应用程序。

## 独立多曲线与自定义输入研究

[独立 X/Y 多曲线实验](research/legacy_multicurve/README.md) 在同一个公开旧版 OPJ 模板、同一张 Book1 表中增加 2、5、10 条各有独立 X/Y 列的曲线，每条固定 50 行。独立实跑的官方 LabPlot 2.12.1 核对了 200、500、1,000 个 binary64 单元格及各自绑定和真实曲线点。原来的黑色样式及单项 B 图例仍保留，不提供自动图例、新工作表或 Origin 安全导出。

[自定义声明输入实验](research/legacy_custom_data/README.md) 保持固定 50 行分配和一条曲线，接受 7、49、50 行 CSV 及单独的来源声明。原始 CSV、声明和完整 binary64 转换记录精确保留；核验和恢复要求外部保存的原始输入哈希。公开示例全部是自有生成的合成数字，measured 声明文件仅测试 schema，不代表真实测量。7/49 行仍保留 86/2 个未使用的原生单元格，所有情况都保留无关模板内容。

两项补充都仅适用于精确公开模板，默认拒绝原生安全导出；Origin 打开、编辑、重算和原生保存重开的完整兼容性仍未通过验收，macOS 写入不支持。仓库只包含源码和有限历史证据，不包含原生样本、截图或应用二进制。当前测试与历史应用实跑的区别、逐例来源与哈希见[分发和复现说明](docs/native-data-packaging.md)。

## 下一步

1. 用公开许可、隔离副本建立真实 Origin/PowerPoint 的打开、编辑、保存与重开验收。
2. 扩展可定位且可验证的原生图字段，拒绝猜测式修改和全局字节替换。
3. 解决压缩记录扩容、长度/依赖更新以及更多数据类型。
4. 在验收证据充分后扩展跨平台支持。

欢迎提交不含私有数据的最小复现、明确版本信息与失败日志。请勿把保密实验文件直接上传 issue。

## License

自有代码采用 [MIT](LICENSE)。`native/dependencies/quantized/` 中的第三方代码保持 Apache-2.0，原 LICENSE、NOTICE 和逐文件哈希均保留，详见 [第三方说明](THIRD_PARTY.md)。Origin / OriginLab / PowerPoint 是各自权利人的产品或商标；本项目与其无隶属或背书关系。

---

## English overview

A source-preserving research toolkit for Origin graphs embedded in PowerPoint. The goal is to keep the underlying graph editable, including data, object bindings and eventual Origin save/reopen behavior.

The native experiment changes fixed-width numeric residuals in one exact OLE template, with independent decoding and reversible byte deltas. It is **not a general OPJU writer**. Preview utilities are separately tested helpers; they do not satisfy the native-editability goal. Origin application lifecycle, recalculation, PowerPoint activation and macOS compatibility remain **unvalidated**. See [validation and limitations](docs/validation.md).

The separate [visual-layout workflow](docs/visual-layout.md) proposes guides before alignment, with a [read-only approval-binding gate](docs/alignment-plan.md) and an identity-coordinate PNG comparison helper. Neither helper edits native Origin objects or implements automatic layout.

The separate [strict modern reference reader](research/modern_native_binding/README.md) and [restricted scalar writer](research/modern_native_scalar/README.md) operate only on recognized sequential dataset/page roots. The writer edits four stored-integer field classes with equal-length literal changes, external anchors and exact restoration. Neither is a numeric-array decoder, complete project parser, modern UI-unit mapping or Origin-validated editor. Their frozen dependencies and tests remain isolated from the older supplements.
