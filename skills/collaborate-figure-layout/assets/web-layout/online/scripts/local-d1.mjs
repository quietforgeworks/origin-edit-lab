// Development/test-only D1 surface using real SQLite SQL semantics.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

export function localDatabase(filename = ':memory:', root = process.cwd()) {
  const sqlite = new DatabaseSync(filename);
  sqlite.exec('CREATE TABLE IF NOT EXISTS __local_migrations (name TEXT PRIMARY KEY NOT NULL)');
  for (const name of readdirSync(resolve(root, 'drizzle')).filter(name => name.endsWith('.sql')).sort()) {
    if (sqlite.prepare('SELECT name FROM __local_migrations WHERE name = ?').get(name)) continue;
    sqlite.exec('BEGIN');
    try {
      sqlite.exec(readFileSync(resolve(root, 'drizzle', name), 'utf8'));
      sqlite.prepare('INSERT INTO __local_migrations (name) VALUES (?)').run(name);
      sqlite.exec('COMMIT');
    } catch (error) { sqlite.exec('ROLLBACK'); throw error; }
  }
  const DB = {
    prepare(sql) {
      return {
        bind(...values) {
          return { async first() { return sqlite.prepare(sql).get(...values) ?? null; } };
        },
      };
    },
  };
  return { DB, sqlite, close: () => sqlite.close() };
}
