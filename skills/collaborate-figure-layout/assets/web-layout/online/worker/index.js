import { validateLayout, LayoutValidationError } from './layout-validation.js';

// PROJECT and STATIC_ASSETS are embedded by the build. Identity headers are
// injected by Sites dispatch. Preserve the Site's owner-only access policy.
const ROW_COLUMNS = 'project_id, map_hash, owner_user_id, revision, layout_json, updated_at';
const MAX_BODY_BYTES = 32768;
const securityHeaders = {
  'Cache-Control': 'private, no-store',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'same-origin',
  'Vary': 'oai-authenticated-user-id',
};
const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), {
  status, headers: { ...securityHeaders, 'Content-Type': 'application/json; charset=utf-8', ...headers },
});
const envelope = row => ({
  projectId: PROJECT.projectId,
  mapHash: PROJECT.mapHash,
  revision: row?.revision ?? 0,
  updatedAt: row?.updated_at ?? null,
  layout: row ? JSON.parse(row.layout_json) : null,
});
const bindingError = row => row && row.map_hash !== PROJECT.mapHash
  ? json({ error: 'project_binding_conflict' }, 409) : null;

async function readBody(request) {
  if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type') || '')) return { error: json({ error: 'json_required' }, 415) };
  const length = request.headers.get('content-length');
  if (length && (!/^\d+$/.test(length) || Number(length) > MAX_BODY_BYTES)) return { error: json({ error: 'request_too_large' }, 413) };
  if (!request.body) return { error: json({ error: 'invalid_json' }, 400) };
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BODY_BYTES) {
        await reader.cancel();
        return { error: json({ error: 'request_too_large' }, 413) };
      }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    return { value: JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)) };
  } catch {
    return { error: json({ error: 'invalid_json' }, 400) };
  }
}

async function layoutApi(request, env, userId, url) {
  if (!['GET', 'PUT'].includes(request.method)) return json({ error: 'method_not_allowed' }, 405, { Allow: 'GET, PUT' });
  if (request.method === 'PUT' && (request.headers.get('origin') !== url.origin || ['cross-site', 'same-site'].includes(request.headers.get('sec-fetch-site')))) return json({ error: 'same_origin_required' }, 403);
  if (!env?.DB?.prepare) return json({ error: 'storage_unavailable' }, 503);
  const read = () => env.DB.prepare(`SELECT ${ROW_COLUMNS} FROM figure_layouts WHERE project_id = ?`).bind(PROJECT.projectId).first();
  if (request.method === 'GET') {
    const row = await read();
    if (row && row.owner_user_id !== userId) return json({ error: 'forbidden' }, 403);
    return bindingError(row) ?? json(envelope(row));
  }
  const parsed = await readBody(request);
  if (parsed.error) return parsed.error;
  const body = parsed.value;
  if (!body || typeof body !== 'object' || Array.isArray(body) || Object.keys(body).some(key => !['expectedRevision', 'layout'].includes(key)) || !Number.isSafeInteger(body.expectedRevision) || body.expectedRevision < 0 || body.expectedRevision >= Number.MAX_SAFE_INTEGER) return json({ error: 'invalid_revision' }, 422);
  let layout;
  try { layout = validateLayout(body.layout, PROJECT); }
  catch (error) {
    if (error instanceof LayoutValidationError) return json({ error: 'invalid_layout', message: error.message }, 422);
    throw error;
  }
  const existing = await read();
  if (existing && existing.owner_user_id !== userId) return json({ error: 'forbidden' }, 403);
  const mismatch = bindingError(existing);
  if (mismatch) return mismatch;
  if ((existing?.revision ?? 0) !== body.expectedRevision) return json({ error: 'revision_conflict', ...envelope(existing) }, 409);
  const now = new Date().toISOString();
  const saved = body.expectedRevision === 0
    ? await env.DB.prepare(`INSERT INTO figure_layouts (project_id, map_hash, owner_user_id, revision, layout_json, updated_at) VALUES (?, ?, ?, 1, ?, ?) ON CONFLICT(project_id) DO NOTHING RETURNING ${ROW_COLUMNS}`).bind(PROJECT.projectId, PROJECT.mapHash, userId, JSON.stringify(layout), now).first()
    : await env.DB.prepare(`UPDATE figure_layouts SET layout_json = ?, revision = revision + 1, updated_at = ? WHERE project_id = ? AND map_hash = ? AND owner_user_id = ? AND revision = ? RETURNING ${ROW_COLUMNS}`).bind(JSON.stringify(layout), now, PROJECT.projectId, PROJECT.mapHash, userId, body.expectedRevision).first();
  if (saved) return json(envelope(saved));
  // Compare-and-swap lost a race. Never overwrite the winner or reveal its
  // content to a different owner.
  const current = await read();
  if (current && current.owner_user_id !== userId) return json({ error: 'forbidden' }, 403);
  return bindingError(current) ?? json({ error: 'revision_conflict', ...envelope(current) }, 409);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const userId = request.headers.get('oai-authenticated-user-id');
    if (!userId || userId.length > 512 || /[\s\u0000-\u001f\u007f]/.test(userId)) return json({ error: 'authentication_required' }, 401);
    try {
      if (url.pathname === '/api/layout') return await layoutApi(request, env, userId, url);
      if (url.pathname.startsWith('/api/')) return json({ error: 'not_found' }, 404);
      if (!['GET', 'HEAD'].includes(request.method)) return json({ error: 'method_not_allowed' }, 405, { Allow: 'GET, HEAD' });
      const path = url.pathname === '/' ? '/index.html' : url.pathname;
      const asset = Object.hasOwn(STATIC_ASSETS, path) ? STATIC_ASSETS[path] : null;
      if (!asset) return new Response('Not found', { status: 404, headers: securityHeaders });
      const bytes = request.method === 'HEAD' ? null : Uint8Array.from(atob(asset.bytes), character => character.charCodeAt(0));
      return new Response(bytes, { headers: { ...securityHeaders, 'Content-Type': asset.type } });
    } catch {
      // Do not log user layout notes or identity.
      return json({ error: 'storage_unavailable' }, 503);
    }
  },
};
