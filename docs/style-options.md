# Typography and palette choices

Offer choices before applying style changes. Do not reinterpret a request for a proposal as permission to recolor or resize the source deck.

## Font reference

The user may name a reference panel or choose a default. If a panel is named, measure separate roles at final slide scale: panel title, axis title, ticks, conditions, legend and references. Use the same glyph/font/weight for visual comparison where possible. Respect a slight axis-title/tick hierarchy. Handle a missing role by proposing a derived size, not silently copying another role.

The default is **compact scientific**, scaled to the current slide rather than an invariant point-size rule. Start from the median readable final tick size among peer panels, propose axis titles around 1.1 times that size, and keep condition/legend labels at a readable size appropriate to their role. Derive panel titles and references from the existing hierarchy. Show actual proposed point sizes, final glyph samples and frame-stroke widths for this deck before applying. If no readable reference exists, make a small preview at a sensible viewing size and ask the user to choose. Typography and strokes must be rechecked after the final geometry changes.

## Six palette options

These are categorical starting sets, not claims of universal accessibility. Show swatches with representative curves on the real background, ask for a set or custom colors, and record the selected mapping. Do not silently change colors when the user has not selected a palette. Limit the number of simultaneous series; do not cycle a short set and make different series indistinguishable.

1. **Accessible contrast (Okabe–Ito):** `#0072B2`, `#D55E00`, `#009E73`, `#CC79A7`, `#E69F00`, `#56B4E9`, `#000000`. Balanced starting choice for distinct scientific series; test lighter colors on the actual background.
2. **Bright restrained (Tol bright):** `#4477AA`, `#EE6677`, `#228833`, `#CCBB44`, `#66CCEE`, `#AA3377`, `#BBBBBB`. Clear medium-weight plots; yellow/cyan/gray may need stronger stroke or marker contrast.
3. **Muted scholarly (Tol muted):** `#332288`, `#88CCEE`, `#44AA99`, `#117733`, `#999933`, `#DDCC77`, `#CC6677`, `#882255`, `#AA4499`. Broad muted range; use a tested subset rather than every color at once.
4. **Vibrant compact (Tol vibrant):** `#0077BB`, `#33BBEE`, `#009988`, `#EE7733`, `#CC3311`, `#EE3377`, `#BBBBBB`. Suitable when a few series need stronger contrast; gray and cyan need background checks.
5. **Editorial categorical (Tableau):** `#4E79A7`, `#F28E2B`, `#E15759`, `#76B7B2`, `#59A14F`, `#EDC948`, `#B07AA1`, `#FF9DA7`, `#9C755F`, `#BAB0AC`. Familiar balanced palette; not all pairs are distinguishable under color-vision deficiencies.
6. **Dark categorical (ColorBrewer Dark2):** `#1B9E77`, `#D95F02`, `#7570B3`, `#E7298A`, `#66A61E`, `#E6AB02`, `#A6761D`, `#666666`. Stronger strokes on white; use additional markers/dashes for close pairs.

A custom palette can specify exact colors or preserve a known series mapping. Do not infer series identity from color alone: verify labels, source data or existing legend relationships. Select explicit series/object targets rather than globally replacing RGB values: the same color may also occur in text, markers or region annotations. Apply one mapping consistently to the same series across panels and keep special semantic colors (control, threshold, warning, sign or treatment) unless the user explicitly chooses a replacement. Sequential/continuous or diverging variables need a suitable ordered scale, not a categorical set. Preserve values and category order.

Check color-vision-deficiency simulations when available, grayscale readability, line/background contrast, overlapping curves and projector/print context. Use markers or dash styles as a second channel when authorized. A palette name is not an accessibility certificate; report the actual checks. Recolor every supported active/fallback representation consistently and verify that opaque fills have not replaced transparency.
