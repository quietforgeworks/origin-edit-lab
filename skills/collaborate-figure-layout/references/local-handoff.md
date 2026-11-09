# 本机轮流交接与参考线选择

## 何时使用

默认使用本机轮流交接工作台，本地、不上传。用户操作完成后通知助手，助手直接读取保存状态，不要求截图或手动导出。只有无法读取本地状态或用户明确选择时，才协商截图/导出后备。它不是实时共同编辑器：用户在浏览器操作并保存，通知助手；助手在同一台已连接电脑读取和修改，通知用户刷新整页。云端localhost不是用户电脑。不要上传源PPT、缩略图或布局，不默认创建公网站点、登录启动项或持久访问。

## 先建立源绑定（不是要求用户传JSON）

助手在隔离任务目录读取PPT并创建源对象清单，按科学含义整理`panels.json`（id/name/sourceAssetIds/category）及真实缩略图。用以下助手内部命令生成哈希绑定；辅助boxes.pptx无需交付用户：

```sh
python scripts/inspect_pptx.py original.pptx --output inventory.json
python scripts/layout_boxes.py create inventory.json boxes.pptx --manifest binding.json --spec panels.json
```

完整面板schema见[file-exchange.md](file-exchange.md)的Bundled tools节；这里只复用绑定生成，不选择其PPT文件交换流程。每个面板源对象归属需人工语义核对，清单成功不等于识别完成。

## 参考线的含义

遵循[对齐关系规则](guide-relations.md)：参考线只告诉助手谁与谁对齐，不固定最终坐标。位置、间距、字体、字号和行距由审美规范及原图参考确定。工作台用户线条的坐标保护只是防止覆盖用户草稿，不是精修坐标硬约束。

## 工具接口

生成（不启动服务；Python 3.10+ 与 Pillow，后者用于实际PNG像素验证，已列在包依赖中）：

```sh
python scripts/prepare_local_handoff.py binding.json previews.json --output-dir handoff --thumbnail-record thumbnail-record.json
cd handoff
python3 server.py --port 8766
```

只绑定127.0.0.1。用实际返回地址打开同机浏览器，不假设端口。保留已运行的同项目工作台和最新状态；不要为了升级重置布局。页面白画布纵向尽量铺满，灰区暂存、固定左侧五色说明保留；选中参考线后隐藏后续颜色选择和对齐说明，新增参考线时可选语义颜色。助手在该目录执行：

```sh
python3 assistant_layout.py read  # Compact layout and preview hashes
python3 assistant_layout.py confirm --revision N  # Only after explicit confirmation
# Read current intent; after explicit user confirmation of this revision:
python3 assistant_layout.py read-confirmed
python3 assistant_layout.py lock --revision N --label '正在补充参考线'
python3 assistant_layout.py renew --lock-id ID
python3 assistant_layout.py apply --layout proposal.json --revision N --lock-id ID
python3 assistant_layout.py unlock --lock-id ID
```

ID来自lock响应的lock.id；每60秒续租，最长180秒未续租自动解除；finally释放自己仍有效的锁。用户取消后旧ID失效，立即停止写入并重新协调。read返回当前状态，apply要求完整布局，不生成参考线；助手依语义计算建议。API强制助手不得覆盖/删除既有user参考线，用户本人可在界面调整。读回状态可核对写入，不能代替用户确认。

按任务生成的source、页面、状态、历史和截图都属于私人工作文件，不写入可发布Skill。通用模板中不得保留上一位用户的图、路径或项目标识。

## 画布与语义参考线

白色区域是最终成图范围；灰色区域只是临时暂存区。完全移出画布的图不参与这一版细化，但保留原始素材与布局记录。横跨边界者先完整移入或移出，不能自行裁掉科研内容。与截图交接不同，这种明确可见的暂存操作可以表达不纳入当前版式；截图中不见某图仍不能直接推断删除。

语义色固定为：青色图框/轴，紫色标题/单位，红色图号/标签，金色对应中心，绿色自定义。保留常驻简短图例，用颜色和目标ID说明线的含义；不要仅将缩略图外框当作真实轴线。图块拖拽可临时变形；正式细化按既有规则恢复字体、轴、标记和科学内容的正确比例。

## 在各阶段给简短选择

复用已明确选择，不每次重问。界面可以弹出短选项，但不得用界面默认值推定用户已批准科学源文件修改。

- 入口：互动式拉图 / 已有版式轻微精修。
- 排列：用户自行拖 / 助手按语义建议；自动排列由对话请求触发，不增加自动布局按钮。
- 参考线：①全部已添加（complete）；②由助手自动添加（auto）；③已有部分作为助手自动补线的约束（constrained）。未选为unselected，不能自动替用户选。
- 细化前：既定审美 / 用户参考图或配色；字号以指定图或既定视觉层次为准；以及既有的三种编辑路线。
- 明显形变：沿既定科学图像/示意图分类规则处理，不把生成能力用于替换科研证据。

complete允许用户确认现有线；若确实缺少必要语义锚点，明确提出缺口而不悄悄改掉。auto与constrained先读取当前布局和已有线、生成补线建议。保留用户线条的绘制坐标、类型、目标与身份；constrained保留其中表达的对齐关系，并非把坐标当作硬约束。只在关系或锚点含义相互矛盾时澄清，不因线的位置不同而强制固定间距或缩小字体。新增线标为assistant。生成完通知用户刷新检查，用户确认这一版后才能应用精修；补线成功不等于已获精修批准。

## 轮流读写、锁定与恢复

1. 用户完成后，读取当前项目、绑定哈希、revision和保存状态。校验为本任务源；不拿旧confirmed-layout快照或测试坐标代替当前布局。
2. 私有候选制作和渲染可先基于已核对的快照完成；修改共享布局或发布预览前重读版本并取得当前会话编辑锁，在页面置顶显示等待对话框并禁用编辑。告知正在做什么；锁定不能丢掉未保存草稿。锁失败/版本变化先重读协调，不强制写文件。
3. 以读到的revision提交完整新布局，保留未纳入图和用户线。409冲突表示期间有新修改，停止覆盖、保留冲突副本，重读后再判断。不得写底层状态绕过检查。
4. 完成或异常时释放自己拥有的锁。界面有超时恢复与用户解除途径；服务停止、模型中断或浏览器刷新不得永久禁用编辑。旧锁令牌不能解锁新任务。长期细化不能无限锁住用户。
5. 写成功后通知用户刷新整页，继续检查/确认；不声称用户浏览器已自动更新。刷新前保留本地未同步草稿及恢复副本，不能直接清空localStorage。
6. 用户说“好了”只触发读取和检查，不证明页面所有保存请求已完成：检查当前revision和用户保存提示；若冲突或未同步，先恢复/重读。需要依据工作台应用新排列/关系时，当前read响应的confirmation必须非空，`confirmation.revision == revision`，`confirmation.layoutHash`等于当前layout的规范JSON哈希（不是不存在的顶层layoutHash字段），否则先确认当前意图。用户已在对话明确确认刚展示的版本时，助手可调用confirm --revision N记录并读回；无需再要求重复点击页面按钮。“好了”只触发读取，不能替代明确确认。细化用当前确认的refinementInput.selectedPanels和alignmentRelations；guidePositionPolicy为display-only。layout.guides中的pos仅用于画线，不传作最终坐标约束，不把灰区图纳入输出。confirmation.revision及layoutHash必须匹配当前状态；后续编辑使确认失效。保存/锁定/页面按钮仅表达布局阶段，不代替真实用户对源文件、引擎或更改数据的授权。

## 正式执行和验证

本机工作台只改布局和参考线。确认后继续主Skill三条编辑路线、统一审美和完整质量审查。Python路线必须保留实际工作页的独立Origin OLE与源数据、每对象缓存及双框关系，遵守ole-display-safety.md；不能整页PNG替代可编辑PPT。

测试分别记录：服务并发/锁恢复、浏览器拖拽与保存、用户实际操作后读取、最终PPT显示、Origin激活更新。一个环节通过不能替代另一个；不把开发时一次验证写成所有未来环境均通过。服务停掉或电脑不可达时，说明限制，保留本地文件，改用已允许的截图/导出交接，不新开网络权限。

精修输出仍须保持PPT原生对象：a/b/c图号与可编辑标注使用原生文字，原生箭头/图形/文字不图片化，不给原本分离的对象新建组合。工作台中的逻辑组合不授权PPT物理组合；参考线独立组为明确例外。


## 细化后的图像如何回到同一页面

`apply`只写布局/参考线，不会刷新缩略图。对已经完成且校验的细化结果，按同一panel ID输出PNG，再用有锁与版本保护的预览接口；不得把这一步叫作原生Origin修改。预览清单为`{"projectId":"实际项目","mapHash":"实际绑定哈希","previews":{"实际panelId":"相对清单路径的已验证.png"}}`，仅助手读取本机文件路径，路径不进入页面。

```sh
python3 assistant_layout.py update-previews --previews preview-update.json --revision N --lock-id ID
```

该操作保留全部几何、参考线和原始素材，保存为独立显示预览，使revision递增并撤销旧确认。更新后读回核对PNG哈希，释放锁并通知刷新；页面刷新时读取保存的预览，不能重新生成整个工作台覆盖用户布局。后续涉及新排列或新关系时确认当前版本；已经明确请求的局部外观修正可沿用兼容的关系授权，先核对当前状态，不能覆盖新的用户拖动。接口只接受有界PNG、已知面板、匹配project/map、当前revision与有效锁，不接受任意HTML或对象文件。

## 能力边界必须在执行前识别

布局状态不是可直接施加给所有OOXML对象的完整精修计划。绑定真实对象、保持原生分组/连接箭头、OLE双框、Calibri文字和数据保护仍需选定路线中受支持的编辑器。现有通用原生PPT adapter限顶层文字与平移；复杂全图编辑要使用已测试的任务专用补丁，不可宣传为任意PPT一键自动化。

`alignment_guides.py`仅支持其文档中的简单单页子集；原页有既有组合或AlternateContent时不能为通过它而拆组/扁平化。使用并验证保留原对象的任务专用导引线组写入器；如果没有安全实现，明确阻碍并保留副本，不用整页图片替代。在页面或对话中确认当前排列意图与对齐关系；最终PPT参考线须按审美修正后的实际锚点重建，而不是复制工作台线条坐标。原生参考线组仍是独立输出检查。

默认read/read-confirmed仅返回预览哈希，避免大量图片编码占用上下文；确需PNG内容时加--include-previews。新服务支持摘要读取，CLI对旧服务自动回退到读取后过滤。confirm需要显式revision，保留服务身份、版本、锁和暂存区检查，不能自动批准未展示的版本。
