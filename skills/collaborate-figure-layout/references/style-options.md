# Typography and palette choices

For font size, character spacing, line/paragraph spacing and reference whitespace, follow [reference-led typography](typography-reference.md) before choosing or applying numerical targets.

Use this reference when choosing a final typography target or a requested color change. It supplements the default accepted compact scientific look in [aesthetic-review.md](aesthetic-review.md). Before fine stretching/refinement, ask whether the user has reference images unless already answered or supplied for the unchanged task. If none, use the established style by default. Do not repeat the question for an unchanged choice. Reuse a versioned, accepted role hierarchy or mapping when its semantic identities and rendering assumptions still apply; keep new-source bindings, current output inspection and plan approval separate. A request for an arrangement preview alone does not authorize source styling.

## Ask once, then inspect the reference

Ask a short question such as “精细调整时，有没有想参考的图片？没有的话，我就按我们既定的审美来。” A supplied reference or an earlier explicit answer for this task already resolves this question. Do not delay a coarse initial HTML arrangement for this refinement choice.

If references are supplied, inspect their actual pixels and focus first on the **spacing between individual panels**, **visible font/glyph sizes**, and **number and form of axes**. Compare within and across rows/columns: frame-to-frame versus label-to-label gaps, role-based text hierarchy at final viewing scale, single versus multiple coordinate axes, frame/spine arrangement, tick-side placement and axis styling. A nominal font size or a screenshot's pixel dimensions alone cannot establish final physical size.

Adapt the appearance to the user's own panels rather than copying another figure's scientific structure. Distinguish decorative frame/spines from data-bearing axes. Do not add/remove axes or a secondary scale, alter ranges/ticks, or change coordinate meaning merely to match the reference. Show uncertain or consequential axis changes separately for explicit confirmation and use a supported edit route. Keep current scientific axes by default.

If no reference is available, continue with the established compact scientific style and project-scaled samples. If several references materially conflict, ask which feature takes priority; otherwise make routine spacing and size decisions yourself and show the complete proposal.

## Pick the reference, not arbitrary numbers

Use one of these approaches independently of all three execution routes: direct Python editing, Windows native Origin via an available MCP, or the Mac-to-VM CLI bridge. Their target appearance is the same; route-specific persistence or reopen limitations do not redefine the style.

- **Established compact scientific style:** white background, clean sans-serif, clear bold panel letters, modest axis-title/tick hierarchy, compact positive title gaps and source palettes. Choose sizes from the current figure and intended output size, not universal point values.
- **Named source/reference panel:** measure separate final-size targets for panel letters, panel/axis titles, ticks, conditions, legends and dense references. A missing role needs a derived sample, not copying an unrelated role's stored integer.
- **User-supplied figure or palette reference:** inspect the actual image/document and retain provenance privately. Extract the intended inter-panel spacing, visible role-based glyph sizes, axis appearance, hierarchy, letter placement, line treatment and palette relationships, while respecting the scientific-axis boundary above. Do not insert its scientific content or infer that it changes the user's results.

For a project-scaled default, start from readable peer tick text at the final output scale and derive a slight axis-title hierarchy. Panel letters, captions, conditions and references retain their own roles. Show representative glyph samples and final frame/curve strokes in this project's complete proposal before application; reuse unchanged accepted style choices instead of reopening them as separate questions. Do not burden the user with entering every numerical setting.

Include native PPT text, subordinate runs and embedded text. Preserve italic variables, bold emphasis, symbols, number–unit spaces and subscript/superscript semantics. Compare actual glyph ink and visible strokes after transforms, font substitution, autofit and wrapping. A source font-size integer is not a transferable physical target.

If references conflict materially, ask which feature or example takes priority. Otherwise select routine sizes and spacing yourself and show the result. Do not claim a named venue requires the style unless its actual guidance was checked.

## Preserve colors unless a change is requested

The existing source palette is the default. A palette sheet or selected swatch is design intent, not permission to globally recolor all objects. For a new or changed mapping, show each scientific series/category explicitly, retaining its source identity and corresponding legend entry. For an unchanged accepted mapping, carry it into the current complete proposal without asking the palette question again; verify the source identities still match. Apply an accepted mapping consistently wherever that same category appears.

Identify series from labels, legends, source bindings or user confirmation, never color alone. Target specific objects instead of global RGB replacements: text, ROI marks, thresholds and data curves may share a color without sharing a meaning. Preserve special meanings such as control, threshold, sign and treatment unless a replacement is explicitly selected.

Categorical palettes suit distinct classes. Sequential and continuous variables need an ordered scale; diverging variables need a meaningful center. Do not replace either with an arbitrary categorical set, reorder values or imply a new scientific distinction.

## Six categorical starting sets

Offer a few relevant choices rather than every palette by default. Show swatches with representative real curves on the intended background. These sets are choices, not universal accessibility guarantees.

1. **Accessible contrast (Okabe–Ito):** `#0072B2`, `#D55E00`, `#009E73`, `#CC79A7`, `#E69F00`, `#56B4E9`, `#000000`. A starting set for distinct series; test lighter colors on white.
2. **Bright restrained (Tol bright):** `#4477AA`, `#EE6677`, `#228833`, `#CCBB44`, `#66CCEE`, `#AA3377`, `#BBBBBB`. Check yellow, cyan and gray curve/background contrast.
3. **Muted scholarly (Tol muted):** `#332288`, `#88CCEE`, `#44AA99`, `#117733`, `#999933`, `#DDCC77`, `#CC6677`, `#882255`, `#AA4499`. Use a tested subset appropriate to the number of categories.
4. **Vibrant compact (Tol vibrant):** `#0077BB`, `#33BBEE`, `#009988`, `#EE7733`, `#CC3311`, `#EE3377`, `#BBBBBB`. Useful for a few prominent series; verify cyan and gray at final line weight.
5. **Editorial categorical (Tableau):** `#4E79A7`, `#F28E2B`, `#E15759`, `#76B7B2`, `#59A14F`, `#EDC948`, `#B07AA1`, `#FF9DA7`, `#9C755F`, `#BAB0AC`. Familiar contrast, but some pairs can be difficult under color-vision deficiencies.
6. **Dark categorical (ColorBrewer Dark2):** `#1B9E77`, `#D95F02`, `#7570B3`, `#E7298A`, `#66A61E`, `#E6AB02`, `#A6761D`, `#666666`. Test close pairs and lighter members on the actual background.

Custom colors or preservation of an established exact mapping are equally valid choices. Never cycle a short set so different simultaneous series become indistinguishable. Do not remove source series merely to make a palette fit.

## Check the mapping in the finished figure

Inspect overlapping curves, markers, error bars, fills and transparency at final scale. Preserve line-width hierarchy rather than thinning meaningful curves to compensate for a color choice. If requested and supported, markers/dashes can add a second distinction; include those changes explicitly in the proposal.

Check grayscale readability, line/background contrast and intended print/projection use. Use color-vision-deficiency simulations when available and report what was actually tested, not a blanket accessibility claim. Verify all edited active/fallback representations consistently so transparency or color meaning does not change between renderers.

Bind the chosen reference, role targets and exact category mapping to the complete proposal in [alignment-review.md](alignment-review.md). A changed font, reference or color decision cannot inherit approval from an unrelated earlier layout version.


