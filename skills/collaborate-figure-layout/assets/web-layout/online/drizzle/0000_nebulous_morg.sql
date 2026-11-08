CREATE TABLE `figure_layouts` (
	`project_id` text PRIMARY KEY NOT NULL,
	`map_hash` text NOT NULL,
	`owner_user_id` text NOT NULL,
	`revision` integer NOT NULL,
	`layout_json` text NOT NULL,
	`updated_at` text NOT NULL,
	CONSTRAINT "figure_layouts_revision_positive" CHECK("figure_layouts"."revision" > 0),
	CONSTRAINT "figure_layouts_layout_json_valid" CHECK(json_valid("figure_layouts"."layout_json"))
);
