# Communicate the workflow and its decisions

Use this layer throughout both entry modes and all three execution routes. Follow the current channel, acknowledgement, progress and confirmation instructions. Keep explanations concrete and brief; never expose private manifests, internal coordination or raw approval records. The user supplies intent and checks the result, not technical coordinates or JSON.

## Entry: understand before asking

Infer the mode when the request is clear. Otherwise ask: “这次是先互动拉图，还是在已有版式上做轻微精修？” In interactive mode, ask manual versus assistant suggestion only if not already answered. In light-refinement mode, preserve the arrangement, skip HTML and prepare the minimal alignment/type proposal automatically. Do not force the user back through setup they already completed.

For interactive work, explain the next action: “我会打开本地排版工作台。你调整完告诉我，我直接读取；我改完通知你刷新查看，精确比例和间距由我细化。” Do not deploy/upload by default. Say whether the file is actually saved on the requested computer; a cloud file is not a successful local save. Screenshots/exports are only agreed fallback or recovery aids when local state is unavailable, never the normal return requirement.

## Consolidate the choices that are actually missing

Before refinement, ask whether there are reference images unless already supplied/declined. No reference means established aesthetics. With a reference, briefly name the inspected features used: panel spacing, visible font sizes, axis appearance. Explain only material conflicts; preserve scientific axes/data rather than blindly copying a visual reference.

Ask the execution choice only once per unchanged task, using the exact three options in [refinement-routes.md](refinement-routes.md). If the style/reference question and route choice are both unresolved, combine them into one compact message rather than serial questions. Do not ask ordinary numerical design questions; choose reasonable measured defaults and show the result.

A chosen route is not a new access grant. State the exact missing tool/environment/permission if applicable. For Python, name the actual target layer before writing: native PPT objects, external visible preview, or a separately verified source field. For preview replacement, explain: “这里改的是 PPT 的显示预览，Origin 数据保持不变；重新激活或刷新时可能恢复旧外观。” Do not imply all Python modifications have identical consequences. For MCP/VM, verify the actual current connection and permitted operation; no silent installation, restart or persistent access expansion.

## Explain uncertainty with a concrete decision

Use the actual source and current saved state to resolve questions first; use screenshots only in an agreed fallback. Ask only when uncertainty materially affects identity, scientific meaning, the final proposal or required approval. State what is known, what differs, and the smallest choice. For example: “这张图部分跨出画布，需要整体移入还是移出？我不会裁掉数据。” Do not treat absence, an ambiguous spoken letter or a similar image as a confirmed deletion/new panel.

For alignment, distinguish frame edge, title ink and baseline. Ask which relationship is intended if the alternatives materially differ; do not ask the user to measure pixels. Data-coordinate ticks, unrelated annotations and deliberate insets can be valid exceptions. Explain an exception rather than hiding an unaligned object or forcing a false relationship.

For clear distortion, follow [aesthetic-review.md](aesthetic-review.md#resolve-clear-png-or-vector-distortion): automatically adapt only verified non-measurement illustrations; warn while retaining stretched micrograph draft placement, then restore physical aspect/scale bars for final output; ask the specified keep/adapt choice for other eligible images. Always restore final text, axes, ticks and scientific geometry through supported sources. A generative illustration is not measurement evidence.

## Confirm the complete guide proposal

Show the complete proposed relationships together, with visible reference lines and a clean companion when useful. Briefly identify the main corrections: true frame edges, close panel letters, role-based type sizes, restored deformation and intentional exceptions. Ask one confirmation for the complete shown plan, not one approval per clear object. Keep unresolved consequential questions explicit.

After approval, bind that exact version privately and execute it without repeated confirmation. A material change of source, target membership, alignment meaning or aesthetic scope needs corresponding approval; ordinary derived coordinate/spacing choices within the confirmed intent do not. Rebind the exact executable plan before writing; an already approved narrow appearance-only edit does not need an invented alignment question. Source data changes are never implied by layout approval. Tool/security-specific confirmations remain separate when required.

## Progress, blockers and completion

Update at meaningful milestones, changes or blockers according to the current channel rules. Say what is actually done and the next step. Give time estimates only when supported by the remaining operation. Separate “inventory complete,” “preview ready,” “PPT preview replaced,” “native Origin saved,” and “reopen/refresh verified.” Do not turn a successful parser, cached screenshot or old test into a stronger claim.

If a method cannot safely achieve part of the plan, stop that part and name the missing operation. Offer a supported next step or a clearly limited preview; ask before changing route or output. Do not tell the user to enable a bridge merely because an easier preview path failed. Do not send repeated empty progress messages.

Deliver the requested format with a short summary of changes and any remaining evidence boundary. Every final figure includes visible alignment references; editable PPT references form one independently manageable native group per figure/slide. A raster shows the lines but cannot preserve selectable/hideable groups. A clean companion may be additional, never the sole final output under this requirement. If the user asked only for an effect screenshot, do not surprise them with an editable PPT or claim it was changed.

The completion summary should answer: what changed, whether original/scientific data stayed intact, which output is final, and what native/application checks actually ran. State visible unresolved defects plainly. Do not claim high-quality completion while the quality gates fail; preserve the last verified revision and continue only with a supported, approved correction.

## Stage choices and handoff examples

Use a short multiple-choice question at a genuine unresolved stage; do not ask every question again when the user's current instruction already answers it. Only the reference-line three-choice control is currently implemented in the page; entry mode, arrangement choice, reference style and editing route are chat choices, not imaginary UI dialogs.

1. Entry: interactive composition or light refinement.
2. Arrangement: user drags or assistant proposes based on scientific meaning.
3. Reference lines (page control): complete, auto, or constrained. “已有部分” means retain user hint artwork and its alignment meaning, then add compatible relationships; it does not pin the final coordinates.
4. Style (chat): established aesthetics or supplied reference; type scale based on a named panel or default visual hierarchy. No reference is needed if the user chooses defaults.
5. Editing route (chat): Python / Windows Origin MCP / Mac command-line bridge, with the exact consequences in refinement-routes.md.
6. Where needed, eligible distorted illustration: keep distortion or proportional generative adaptation. Scientific images/data are never generatively replaced; final physical geometry is restored.
7. Confirmation: show the complete alignment-relationship proposal (line positions are illustrative). Read a page confirmation, or record an explicit chat confirmation of that exact reviewed revision with `confirm --revision N`; do not ask twice. Layout confirmation does not authorize new scientific-data changes.
8. Work: “我正在补线/细化，页面暂时锁定；完成后通知你刷新。” Take/renew/release a real lock for shared-state work; prepare independent private candidates before locking and never simulate a busy status without backend protection.
9. Delivery: edited PPT retains independent native labels/arrows/shapes and Origin objects, with a separate guide group. Explain cache/native differences and separately report target-host rendering, Origin activation and update checks.

Normal handoff dialogue: “你操作完告诉我就行，不需要截图；我直接读取当前状态。” After modification: “已保存这版修改并解锁，刷新页面查看。” If local readback is blocked: name the exact blocker, preserve current work, then ask whether screenshot/export fallback is acceptable rather than silently demanding one.
