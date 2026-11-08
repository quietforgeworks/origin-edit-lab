# Private figure layout backend template

This reusable backend persists approximate layout intent in an owner-private
Site. It contains no project data, images, Site registration, user identity,
source mapping, runtime database, credentials, or compiled Worker.

## Integration interface

Supply these frontend files separately before building:

- `dist/index.html`, `dist/app.js`, and `dist/style.css`
- `dist/project.json` with schema `figure-layout-roundtrip/v1`, a project-specific
  `projectId` and `mapHash`, a fixed `{width,height,unit:"mm"}` canvas, and `panels`
- Each panel needs a unique string `id`, `name`, and finite `initialBounds` with
  `x`, `y`, `w`, and `h` inside that canvas. `preview` names a relative PNG path,
  such as `previews/panel-1.png`; repeated paths are embedded only once.
- Put only approved preview PNGs under `dist/`. The build includes only previews
  named in the project, rejects traversal and symlinks, and checks PNG signatures.
  Do not add sourceBindings,
  sourceAssetIds, original scientific files, or private source paths.

The frontend owns local-storage migration, drag interactions, conflict UI, and
save retries. This backend component does not implement the frontend or an offline
project builder; those are supplied separately. `dist/` frontend files are retained inputs, not disposable build
output. `dist/server/` and `dist/.openai/` are generated.

For a new Site, perform the supported registration workflow first and persist
its returned Site ID in `.openai/hosting.json`. For an existing Site, retain its
verified ID and access policy. `.openai/hosting.example.json` supplies only the
`DB` binding and unused R2 setting; it intentionally has no `project_id`. Never
publish an invented or test Site ID. Preserve the owner-only hosting audience
and omit `static` from the production manifest.

Run `npm run build` to embed the current frontend and project definition in the
Worker ES module at `dist/server/index.js`. Run `npm run check` to validate the
artifact and execute the 32 backend tests with Node's SQLite implementation.
The tests derive their project and panel data from `dist/project.json`; use at
least two synthetic panels for template QA. No deployment is part of the tests.

## API and data contract

`GET /api/layout` returns `{projectId,mapHash,revision,updatedAt,layout}`. Before
first save, revision is `0` and layout/time are null.

`PUT /api/layout` accepts `{expectedRevision,layout}` and returns that envelope
with the revision increased by one. The layout contains:

- `schema`, `projectId`, `mapHash`, and the fixed `canvas`
- `selectedPanels: [{id,bounds:{x,y,w,h}}]`
- `omittedPanelIds`, covering exactly all remaining known IDs
- `refinement: {mode:"existing-aesthetics"|"user-references",references:[]}`
- An optional `note` up to 2,000 characters
- Fixed scientific-source safety flags, added and checked by the backend

Selected/omitted IDs must form a complete, disjoint partition of the project.
Source references, unrecognized fields, unsafe bounds, non-finite numbers,
changed canvas/project hashes, and altered safety flags are rejected. Only
0.002 mm of rounding tolerance is accepted at a canvas edge. The server stores
only known IDs, rough bounds, omissions, fixed canvas, aesthetic mode, note,
and fixed safety flags. It never stores or modifies the scientific source.

A stale revision returns HTTP 409 with `error:"revision_conflict"` and the
current envelope. Writes are atomic compare-and-swap operations; simultaneous
requests cannot silently replace each other. A different database mapHash
returns `project_binding_conflict` without replacing the stored record.

`DB.figure_layouts` contains one row per layout project: `project_id`, `map_hash`,
`owner_user_id`, `revision`, `layout_json`, and `updated_at`. The first authenticated
visitor owns the row, relying on the Site retaining owner-only hosting access.
Another identity cannot read or overwrite that owner's record.

Every production route requires dispatch's `oai-authenticated-user-id` header.
Browser JavaScript must never supply that header. PUT also requires exact same
origin, JSON, and a bounded body. Service access without a visitor identity does
not grant API access. API responses are private and non-cacheable.

## Later scientific refinement

Layout persistence does not choose or execute scientific refinement. After the
user chooses a refinement path, a separate workflow can either edit PPT assets
with code or use an actual Origin bridge on Windows. This backend does neither:
it contains no bridge launcher, bridge connection, source editor, or automatic
rearrangement operation. Its refinement mode records aesthetic intent only.

## Schema migrations

The schema is `db/schema.ts`. Install the declared development dependencies via
the supported Sites installer when migration generation is needed. Run
`npm run db:generate` after schema changes and commit generated SQL and metadata
under `drizzle/`. Applied migrations are immutable. Build output includes them
under `dist/.openai/drizzle/`; the hosting workflow applies hosted migrations.
Request handlers never create tables or run schema migrations.

## Local browser QA

Use the supported Sites preview daemon. It invokes `npm run dev`, which builds
the Worker and starts `scripts/dev-preview.mjs`. The development wrapper uses
`.sites-runtime/preview-layouts.sqlite` plus a fixed local test identity. It is
never imported or embedded in the production Worker. Local migrations run at
preview startup, not in request handlers. Keep all runtime state untracked.

Local tests verify application behavior, not hosted ChatGPT sign-in or the live
D1 binding. Real production save/read verification requires the owner's normal
authenticated browser. Do not claim a development fixture verified production.
