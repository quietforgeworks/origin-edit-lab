import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import worker from '../dist/server/index.js';
import { validateLayout, LayoutValidationError } from '../worker/layout-validation.js';
import { localDatabase } from '../scripts/local-d1.mjs';

const project = JSON.parse(readFileSync(new URL('../dist/project.json', import.meta.url)));
const origin = 'https://private-site.example';
const identity = 'test-user-owner';
const initial = () => ({
  schema: project.schema, projectId: project.projectId, mapHash: project.mapHash,
  canvas: structuredClone(project.canvas),
  selectedPanels: project.panels.map(panel => ({ id: panel.id, bounds: { ...panel.initialBounds } })),
  omittedPanelIds: [], refinement: { mode: 'existing-aesthetics', references: [] }, note: '',
});
const body = (expectedRevision = 0, layout = initial()) => ({ expectedRevision, layout });
function request(method = 'GET', data, options = {}) {
  const headers = new Headers({ 'oai-authenticated-user-id': identity });
  if (method === 'PUT') { headers.set('Origin', origin); headers.set('Content-Type', 'application/json'); }
  for (const [key, value] of Object.entries(options.headers || {})) {
    if (value === null) headers.delete(key); else headers.set(key, value);
  }
  return new Request(origin + (options.path || '/api/layout'), { method, headers, ...(data !== undefined ? { body: typeof data === 'string' ? data : JSON.stringify(data) } : {}) });
}
function fixture(t) {
  const database = localDatabase(); t.after(database.close);
  return { ...database, call: (method, data, options) => worker.fetch(request(method, data, options), { DB: database.DB }) };
}

test('unauthenticated API reads/writes and static resources fail before DB access', async () => {
  for (const [method, path, data] of [['GET', '/api/layout'], ['PUT', '/api/layout', body()], ['GET', '/'], ['GET', '/assets/a.png']]) {
    const response = await worker.fetch(request(method, data, { path, headers: { 'oai-authenticated-user-id': null } }), {});
    assert.equal(response.status, 401);
    assert.equal((await response.json()).error, 'authentication_required');
  }
});

test('empty state, create, read and update return immutable binding and durable revision', async t => {
  const { call, sqlite } = fixture(t);
  assert.deepEqual(await (await call('GET')).json(), { projectId: project.projectId, mapHash: project.mapHash, revision: 0, updatedAt: null, layout: null });
  const first = await call('PUT', body()); assert.equal(first.status, 200);
  const saved = await first.json(); assert.equal(saved.revision, 1); assert.ok(Date.parse(saved.updatedAt));
  assert.equal(saved.layout.selectedPanels.length, project.panels.length);
  assert.equal(saved.layout.scientificSourceEdited, false);
  assert.deepEqual(await (await call('GET')).json(), saved);
  const next = initial(); next.selectedPanels[0].bounds.x += 1; next.note = 'Move the left figure';
  const updated = await (await call('PUT', body(1, next))).json(); assert.equal(updated.revision, 2);
  const row = sqlite.prepare('SELECT * FROM figure_layouts').get();
  assert.equal(row.owner_user_id, identity); assert.equal(row.project_id, project.projectId); assert.equal(row.revision, 2);
  assert.equal(JSON.parse(row.layout_json).note, next.note);
  assert.equal(row.map_hash, project.mapHash);
  assert.equal(Object.hasOwn(updated, 'owner_user_id'), false);
  assert.match(first.headers.get('cache-control'), /no-store/);
});

test('same owner stale revision receives current layout without overwriting it', async t => {
  const { call } = fixture(t);
  await call('PUT', body());
  const changed = initial(); changed.note = 'Do not save this';
  const response = await call('PUT', body(0, changed)); assert.equal(response.status, 409);
  const conflict = await response.json(); assert.equal(conflict.error, 'revision_conflict'); assert.equal(conflict.revision, 1); assert.equal(conflict.layout.note, '');
  assert.equal((await (await call('GET')).json()).layout.note, '');
});

test('two simultaneous creates or updates produce exactly one winner', async t => {
  const { call } = fixture(t);
  const first = initial(), second = initial(); first.note = 'first'; second.note = 'second';
  const creates = await Promise.all([call('PUT', body(0, first)), call('PUT', body(0, second))]);
  assert.deepEqual(creates.map(r => r.status).sort(), [200, 409]);
  const updates = await Promise.all([call('PUT', body(1, first)), call('PUT', body(1, second))]);
  assert.deepEqual(updates.map(r => r.status).sort(), [200, 409]);
  assert.equal((await (await call('GET')).json()).revision, 2);
});

test('different identity cannot read or overwrite an established owner record', async t => {
  const { call } = fixture(t); await call('PUT', body());
  for (const method of ['GET', 'PUT']) {
    const response = await call(method, method === 'PUT' ? body(1) : undefined, { headers: { 'oai-authenticated-user-id': 'someone-else' } });
    assert.equal(response.status, 403); assert.deepEqual(await response.json(), { error: 'forbidden' });
  }
});

test('cross-origin, absent Origin, and sibling-site writes are rejected', async t => {
  const { call } = fixture(t);
  for (const headers of [{ Origin: 'https://attacker.example' }, { Origin: null }, { Origin: 'null' }, { 'Sec-Fetch-Site': 'cross-site' }, { 'Sec-Fetch-Site': 'same-site' }]) {
    assert.equal((await call('PUT', body(), { headers })).status, 403);
  }
  assert.equal((await (await call('GET')).json()).revision, 0);
});

const invalidCases = [
  ['foreign project', layout => { layout.projectId = 'wrong'; }],
  ['stale map', layout => { layout.mapHash = 'wrong'; }],
  ['unknown ID', layout => { layout.selectedPanels[0].id = 'unknown'; }],
  ['duplicate ID', layout => { layout.selectedPanels[0].id = layout.selectedPanels[1].id; }],
  ['missing selected/omitted member', layout => { layout.selectedPanels.pop(); }],
  ['duplicate omitted', layout => { const p = layout.selectedPanels.pop(); layout.omittedPanelIds.push(p.id, p.id); }],
  ['overlapping selected/omitted IDs', layout => { layout.selectedPanels.pop(); layout.omittedPanelIds.push(layout.selectedPanels[0].id); }],
  ['infinite bounds', layout => { layout.selectedPanels[0].bounds.w = Infinity; }],
  ['NaN bounds', layout => { layout.selectedPanels[0].bounds.x = NaN; }],
  ['negative origin', layout => { layout.selectedPanels[0].bounds.x = -1; }],
  ['zero width', layout => { layout.selectedPanels[0].bounds.w = 0; }],
  ['off-canvas bounds', layout => { layout.selectedPanels[0].bounds.x = project.canvas.width; }],
  ['string coordinate', layout => { layout.selectedPanels[0].bounds.x = '10'; }],
  ['changed canvas', layout => { layout.canvas.width++; }],
  ['source binding injection', layout => { layout.selectedPanels[0].sourceBindings = [{ path: 'private' }]; }],
  ['source asset injection', layout => { layout.selectedPanels[0].sourceAssetIds = ['private']; }],
  ['reference injection', layout => { layout.refinement.references.push('https://external.example'); }],
  ['new mode', layout => { layout.refinement.mode = 'edit-source'; }],
  ['unsafe source flag', layout => { layout.scientificSourceEdited = true; }],
  ['oversized note', layout => { layout.note = 'x'.repeat(2001); }],
  ['unknown top-level fields', layout => { layout.sourceFile = '/private/source.pptx'; }],
];
for (const [name, mutate] of invalidCases) test(`rejects ${name}`, async t => {
  const { call } = fixture(t); const layout = initial(); mutate(layout);
  assert.throws(() => validateLayout(layout, project), LayoutValidationError);
  const response = await call('PUT', body(0, layout)); assert.equal(response.status, 422);
  assert.equal((await (await call('GET')).json()).revision, 0);
});

test('valid omissions cover all known IDs, including empty selection', async t => {
  const { call } = fixture(t); const layout = initial();
  layout.omittedPanelIds = layout.selectedPanels.map(p => p.id); layout.selectedPanels = [];
  const response = await call('PUT', body(0, layout)); assert.equal(response.status, 200);
  assert.equal((await response.json()).layout.selectedPanels.length, 0);
});

test('rejects malformed JSON, non-finite JSON exponent, oversized bodies and wrong content type', async t => {
  const { call } = fixture(t);
  assert.equal((await call('PUT', '{')).status, 400);
  assert.equal((await call('PUT', JSON.stringify(body()).replace(/"x":[\d.]+/, '"x":1e999'))).status, 422);
  assert.equal((await call('PUT', 'x'.repeat(32769))).status, 413);
  assert.equal((await call('PUT', body(), { headers: { 'Content-Type': 'text/plain' } })).status, 415);
  assert.equal((await call('PUT', { expectedRevision: -1, layout: initial() })).status, 422);
  assert.equal((await call('PUT', { expectedRevision: '0', layout: initial() })).status, 422);
});

test('existing different mapHash is preserved and not exposed as a current layout', async t => {
  const { call, sqlite } = fixture(t); await call('PUT', body());
  sqlite.prepare('UPDATE figure_layouts SET map_hash = ?').run('old-hash');
  for (const method of ['GET', 'PUT']) {
    const response = await call(method, method === 'PUT' ? body(1) : undefined);
    assert.equal(response.status, 409); assert.deepEqual(await response.json(), { error: 'project_binding_conflict' });
  }
  assert.equal(sqlite.prepare('SELECT revision FROM figure_layouts').get().revision, 1);
});

test('all original frontend and PNG bytes are served unchanged and authenticated', async () => {
  const files = ['index.html', 'app.js', 'style.css', 'project.json', ...new Set(project.panels.map(panel => panel.preview).filter(value => value !== undefined))];
  for (const path of files) {
    const response = await worker.fetch(request('GET', undefined, { path: '/' + path }), {});
    assert.equal(response.status, 200, path);
    assert.deepEqual(Buffer.from(await response.arrayBuffer()), readFileSync(resolve('dist', path)), path);
  }
  assert.equal((await worker.fetch(request('GET', undefined, { path: '/server/index.js' }), {})).status, 404);
});

test('missing or failed DB reports unavailable; methods are bounded', async t => {
  const { call } = fixture(t);
  assert.equal((await worker.fetch(request(), {})).status, 503);
  assert.equal((await worker.fetch(request(), { DB: { prepare() { throw Error('internal details'); } } })).status, 503);
  assert.equal((await call('DELETE')).status, 405);
  assert.equal((await call('OPTIONS')).status, 405);
});
