"""Project workbench guides to alignment intent. Never produce final coordinates."""
import hashlib, json
POLICY = 'alignment-relations/v1'
KINDS = {'frame', 'title', 'label', 'center', 'custom'}

def from_layout(layout):
    if not isinstance(layout, dict) or not isinstance(layout.get('projectId'), str) or not isinstance(layout.get('mapHash'), str):
        raise ValueError('Missing task binding for guide relations')
    panels = layout.get('selectedPanels')
    omitted = layout.get('omittedPanelIds')
    if not isinstance(panels, list) or not isinstance(omitted, list):
        raise ValueError('Missing panel selection')
    active = [p.get('id') for p in panels if isinstance(p, dict)]
    known = active + omitted
    if len(active) != len(panels) or any(not isinstance(x, str) or not x for x in known) or len(set(known)) != len(known):
        raise ValueError('Invalid panel identities')
    guides = layout.get('guides', [])
    if not isinstance(guides, list):
        raise ValueError('Invalid guide collection')
    seen, relations = set(), []
    for g in guides:
        if not isinstance(g, dict) or not isinstance(g.get('id'), str) or not g['id'] or g['id'] in seen:
            raise ValueError('Invalid or duplicate guide identity')
        seen.add(g['id'])
        targets = g.get('targets', [])
        if not isinstance(targets, list) or any(not isinstance(x, str) or x not in known for x in targets) or len(set(targets)) != len(targets):
            raise ValueError('Invalid guide target identities')
        if g.get('axis') not in ('x', 'y') or (not isinstance(g.get('kind'), str) or g['kind'] not in KINDS) or not isinstance(g.get('label'), str):
            raise ValueError('Invalid guide meaning')
        # pos/color/owner are drawing and custody metadata, never target coordinates.
        relations.append({'guideId':g['id'], 'axis':g['axis'], 'kind':g['kind'],
                          'targetPanelIds':sorted(targets), 'intentLabel':g['label'],
                          'anchorBindingRequired':True})
    relations.sort(key=lambda r:r['guideId'])
    core = {'policy':POLICY, 'projectId':layout['projectId'], 'mapHash':layout['mapHash'],
            'alignmentRelations':relations}
    encoded = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'guideSemantics':POLICY, 'guidePositionPolicy':'display-only',
            'panelGeometryPolicy':'rough-composition-intent',
            'alignmentRelations':relations,
            'guideIntentSha256':hashlib.sha256(encoded).hexdigest()}

def normalize_refinement_input(layout, existing):
    """Normalize a current/legacy confirmed view without mutating saved state."""
    import copy
    if not isinstance(existing, dict):
        raise ValueError('Missing confirmed refinement input')
    intent = from_layout(layout)
    if existing.get('guidePositionPolicy', 'display-only') != 'display-only':
        raise ValueError('Refinement must not pin workbench guide coordinates')
    if 'alignmentRelations' in existing and existing['alignmentRelations'] != intent['alignmentRelations']:
        raise ValueError('Saved alignment relations do not match current layout')
    # Preserve only documented coarse composition/protection fields from legacy records.
    result = {k:copy.deepcopy(existing[k]) for k in ('selectedPanels', 'excludedOutsidePanelIds', 'sourcePreserved') if k in existing}
    result.update(intent)
    return result
