import { sql } from 'drizzle-orm';
import { check, integer, sqliteTable, text } from 'drizzle-orm/sqlite-core';

// Only layout intent belongs here. Original figure/source bindings never enter D1.
export const figureLayouts = sqliteTable('figure_layouts', {
  projectId: text('project_id').primaryKey().notNull(),
  mapHash: text('map_hash').notNull(),
  ownerUserId: text('owner_user_id').notNull(),
  revision: integer('revision').notNull(),
  layoutJson: text('layout_json').notNull(),
  updatedAt: text('updated_at').notNull(),
}, table => [
  check('figure_layouts_revision_positive', sql`${table.revision} > 0`),
  check('figure_layouts_layout_json_valid', sql`json_valid(${table.layoutJson})`),
]);
