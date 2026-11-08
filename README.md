# Origin Edit Lab

让放进 PowerPoint 的 Origin 图，仍然是一张能继续编辑的图。

这个项目探索 **保留原始 Origin 源对象的数据与图形编辑**：改变数据或参数后，仍能在 Origin 中打开、调整、保存，并正确回到 PowerPoint。当前是研究起点，不是完整的 Origin 替代品。

## 目前做到哪里

- **原生数据写回实验**：对一个严格限定的 Origin OLE 模板，在既有压缩记录的空间内写入两列、各 9 个数值。双解码器核对数值，保留图对象、X/Y 绑定、其他流及未知字节，支持精确恢复。
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

The native experiment changes fixed-width numeric residuals in one exact OLE template, with independent decoding and reversible byte deltas. It is **not a general OPJU writer**. Preview utilities are separately tested helpers; they do not satisfy the native-editability goal. Origin application acceptance, recalculation, PowerPoint activation and macOS validation are still **not run**. See [validation and limitations](docs/validation.md).

The separate [visual-layout workflow](docs/visual-layout.md) proposes guides before alignment, with a [read-only approval-binding gate](docs/alignment-plan.md) and an identity-coordinate PNG comparison helper. Neither helper edits native Origin objects or implements automatic layout.
