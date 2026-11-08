export class LayoutValidationError extends Error {}
const fail = message => { throw new LayoutValidationError(message); };
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const onlyKeys = (value, allowed, label) => {
  if (!isObject(value)) fail(`${label} must be an object`);
  if (Object.keys(value).some(key => !allowed.includes(key))) fail(`${label} contains unsupported fields`);
};

export function validateLayout(raw, project) {
  onlyKeys(raw, ['schema', 'projectId', 'mapHash', 'interaction', 'exportedAt', 'canvas', 'selectedPanels', 'omittedPanelIds', 'refinement', 'note', 'geometryIsApproximateIntent', 'previewStretchIsNotScientificEdit', 'semanticGuideApprovalRequired', 'userChatApprovalStillRequired', 'scientificSourceEdited'], 'layout');
  if (raw.schema !== 'figure-layout-roundtrip/v1' || raw.projectId !== project.projectId || raw.mapHash !== project.mapHash) fail('Layout does not belong to this project');
  onlyKeys(raw.canvas, ['width', 'height', 'unit'], 'canvas');
  if (['width', 'height', 'unit'].some(key => raw.canvas[key] !== project.canvas[key])) fail('Canvas must match the project');
  if (!Array.isArray(raw.selectedPanels) || !Array.isArray(raw.omittedPanelIds)) fail('Selected and omitted panels must be arrays');
  if (raw.selectedPanels.length + raw.omittedPanelIds.length !== project.panels.length) fail('Selected and omitted panels must cover the project exactly');
  const known = new Map(project.panels.map(panel => [panel.id, panel]));
  const seen = new Set();
  const readId = id => {
    if (typeof id !== 'string' || !known.has(id) || seen.has(id)) fail('Unknown or duplicate panel ID');
    seen.add(id);
  };
  const selectedPanels = raw.selectedPanels.map(panel => {
    onlyKeys(panel, ['id', 'name', 'bounds'], 'panel');
    readId(panel.id);
    if (panel.name !== undefined && panel.name !== known.get(panel.id).name) fail('Panel name cannot be changed');
    onlyKeys(panel.bounds, ['x', 'y', 'w', 'h'], 'bounds');
    const { x, y, w, h } = panel.bounds;
    if (![x, y, w, h].every(value => typeof value === 'number' && Number.isFinite(value))) fail('Bounds must be finite numbers');
    if (x < 0 || y < 0 || w < 0.1 || h < 0.1 || w > project.canvas.width || h > project.canvas.height || x + w > project.canvas.width + 0.002 || y + h > project.canvas.height + 0.002) fail('Bounds must stay inside the canvas');
    // Absorb at most 0.002 mm of browser rounding at an outer edge.
    return { id: panel.id, bounds: { x, y, w: Math.min(w, project.canvas.width - x), h: Math.min(h, project.canvas.height - y) } };
  });
  for (const id of raw.omittedPanelIds) readId(id);
  if (seen.size !== known.size) fail('Selected and omitted panels must cover the project exactly');
  const refinement = raw.refinement ?? { mode: 'existing-aesthetics', references: [] };
  onlyKeys(refinement, ['mode', 'references'], 'refinement');
  if (!['existing-aesthetics', 'user-references'].includes(refinement.mode)) fail('Unsupported refinement mode');
  if (refinement.references !== undefined && (!Array.isArray(refinement.references) || refinement.references.length !== 0)) fail('Source references cannot be saved here');
  const note = raw.note ?? '';
  if (typeof note !== 'string' || note.length > 2000 || /[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(note)) fail('Note is invalid or too long');
  if (raw.interaction !== undefined && raw.interaction !== 'browser-layout') fail('Unsupported interaction');
  if (raw.exportedAt !== undefined && (typeof raw.exportedAt !== 'string' || raw.exportedAt.length > 64 || !Number.isFinite(Date.parse(raw.exportedAt)))) fail('Invalid export time');
  const safety = { geometryIsApproximateIntent: true, previewStretchIsNotScientificEdit: true, semanticGuideApprovalRequired: true, userChatApprovalStillRequired: true, scientificSourceEdited: false };
  for (const [key, value] of Object.entries(safety)) if (raw[key] !== undefined && raw[key] !== value) fail('Scientific-source safety flags cannot be changed');
  return {
    schema: 'figure-layout-roundtrip/v1', projectId: project.projectId, mapHash: project.mapHash,
    interaction: 'browser-layout', canvas: { ...project.canvas }, selectedPanels,
    omittedPanelIds: project.panels.filter(panel => raw.omittedPanelIds.includes(panel.id)).map(panel => panel.id),
    refinement: { mode: refinement.mode, references: [] }, note, ...safety,
  };
}
