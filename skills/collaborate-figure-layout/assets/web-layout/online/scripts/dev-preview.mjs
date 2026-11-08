// DEVELOPMENT ONLY. Never imported or copied into the production Worker bundle.
// The Sites preview daemon owns this process. This is a local browser fixture:
// production Worker + SQLite D1 adapter + a fixed local preview identity.
import { createServer } from 'node:http';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import worker from '../dist/server/index.js';
import { localDatabase } from './local-d1.mjs';

const argv = process.argv.slice(2);
function option(name, fallback) { const i = argv.indexOf(name); return i === -1 ? fallback : argv[i + 1]; }
const port = Number(option('--port', '4173'));
const host = option('--host', '127.0.0.1');
mkdirSync('.sites-runtime', { recursive: true });
const database = localDatabase(resolve('.sites-runtime/preview-layouts.sqlite'));
const server = createServer(async (incoming, outgoing) => {
  try {
    const headers = new Headers();
    for (const [key, value] of Object.entries(incoming.headers)) {
      if (!key.startsWith('oai-authenticated-user-') && value !== undefined) headers.set(key, Array.isArray(value) ? value.join(', ') : value);
    }
    headers.set('oai-authenticated-user-id', 'local-preview-owner');
    const forwardedHost = headers.get('x-forwarded-host')?.split(',')[0].trim();
    const forwardedProtocol = headers.get('x-forwarded-proto')?.split(',')[0].trim();
    const authority = forwardedHost || headers.get('host') || `127.0.0.1:${port}`;
    const protocol = forwardedProtocol === 'https' ? 'https' : 'http';
    const url = new URL(incoming.url || '/', `${protocol}://${authority}`);
    const method = incoming.method || 'GET';
    const request = new Request(url, { method, headers, ...(!['GET', 'HEAD'].includes(method) ? { body: incoming, duplex: 'half' } : {}) });
    const response = await worker.fetch(request, { DB: database.DB });
    outgoing.writeHead(response.status, Object.fromEntries(response.headers));
    outgoing.end(Buffer.from(await response.arrayBuffer()));
  } catch {
    outgoing.writeHead(500, { 'Content-Type': 'text/plain' }); outgoing.end('Local preview error');
  }
});
server.listen(port, host, () => console.log(`Local fixture on ${host}:${port}. Fixed local identity; not hosted authentication.`));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => server.close(() => { database.close(); process.exit(0); }));
