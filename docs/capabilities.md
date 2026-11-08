# Capability map

`native/` contains experimental, exact-template numeric mutation plus conservative CFB and ZIP preservation primitives. Hash guards intentionally prevent treating an arbitrary Origin file as supported. Unknown records are preserved rather than guessed, but preservation does not prove all internal dependencies remain valid.

`preview/` contains bounded read-only extractors, package inspection, SVG appearance editing and selected PPTX preview replacement. Preview work is an auxiliary route with explicit stale-OLE acknowledgement, not completion of the native-editability goal.

The next major milestone is independent Origin/PowerPoint open-edit-save-reopen validation. New native fields, resizing and graph generation require their own support contract and tests. Do not infer broad support from extensions, parser success, object counts or unchanged previews.
