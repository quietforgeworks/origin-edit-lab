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
