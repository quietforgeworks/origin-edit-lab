# Public provenance and semantic boundaries

The public corpus manifests contain exact source URLs, source hashes, licensed record references and (where applicable) the public archive member and OLE object part. The original110 consists of the public Heliox supplementary PPT's embedded Contents streams plus independent standalone project/graph sources. The independent57 consists of directly downloadable OPJU originals from three additional Zenodo records. No source bytes are included.

The relevant official-source corroboration is LabPlot 2.12.1 liborigin:

- URL: https://download.kde.org/stable/labplot/labplot-2.12.1.tar.xz
- Archive SHA256: e28155bfddf40e5b6f7c4791313556d1e48138044f216f210d515b9f6d6c106a
- OriginAnyParser.cpp SHA256: b43d1fbf3b70fd135188dcd12838c83b0886dc3444dbc63b086183e09f53d611
- Lines 2284–2287 read worksheet dataID at +0x04 then datasets[dataID-1].sheet.
- Lines 2388–2403 read graph selectors at +0x04 and +0x23, then findDataByIndex(w-1).

This older-format source corroborates the one-based stream-reference convention. It does not establish every modern typed dataset encoding or universal plot interpretation. The modern boundary/transport grammar in this package is deliberately restricted, source-tested research. No external liborigin source is included or required at runtime.

The adjacent generic helper files are frozen source dependencies; their exact hashes are in MANIFEST.json. The dataset-envelope helper establishes sequential envelope extents but does not decode numerical values. The owner helper contains the earlier diagnostic scanner for standalone use; native_binding never invokes it for project-root discovery.
