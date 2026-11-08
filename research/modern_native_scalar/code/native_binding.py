"""Read-only, source-anchored CPYUA dataset/page/column reference certificate.

Restricted research grammar. Starts at the validated prolog, never searches for
records or uses labels to bind references. Unknown framing stops; project tail,
codec values and Origin application acceptance are outside this certificate.
"""
from __future__ import annotations
import hashlib, struct
import sparse_transport as s
import owner_walk as o
import walk_dataset_envelope as ds

MAX_BYTES = 16 * 1024 * 1024
MAX_PAGES = 4096
LAYER_SIZES = (341, 361, 385, 393, 405, 409)
PAGE_SIZES = (195, 199, 205, 245, 253, 261, 269)
COLUMN_SIZES = (489, 515, 519)
WORKSHEET_TYPES = (b'\0\0\x5e\0',)
GRAPH_TYPES = (b'\0\0\x1f\0', b'\0\0\x17\0', b'\0\0\x5f\0')


def text_field(raw: bytes):
    try:
        return {'utf8': raw.decode('utf8'), 'hex': raw.hex()}
    except UnicodeDecodeError:
        return {'utf8': None, 'hex': raw.hex()}


def named_slot(raw, start, end):
    field = raw[start:end]
    o.need(b'\0' in field, 'unterminated fixed-name slot', start)
    return text_field(field.split(b'\0', 1)[0])


def scalar_evidence(frame, at, width):
    return {'decoded_offset': at, 'width': width,
            'decoded_le_hex': frame['raw'][at:at+width].hex(),
            'literal_offsets': frame['mapping'][at:at+width]}


def column(b, p, owned):
    start = p
    h = o.record(b, p, owned)
    d = h['raw']
    o.need(len(d) in COLUMN_SIZES and d[0] == 0x10 and d[2:4] == b'\0\0',
           'worksheet column header type/size', p)
    p = h['end']
    opaque = []
    for _ in range(3):
        value = o.compact_blob(b, p, owned=owned)
        opaque.append(value)
        p = value['end']
    return {'offset': start, 'end': p, 'header': s.meta(h),
            'name': named_slot(d, 18, 30), 'designation_u8': d[17],
            'dataset_selector_u16': struct.unpack_from('<H', d, 4)[0],
            'selector_field': scalar_evidence(h, 4, 2),
            'opaque': opaque}


def worksheet_layer(b, p, owned):
    start = p
    h = o.record(b, p, owned)
    d = h['raw']
    o.need(len(d) in LAYER_SIZES and d[:4] in WORKSHEET_TYPES,
           'worksheet layer header type/size', p)
    n, q = s.uleb(b, h['end'])
    end = q + n
    o.need(n <= 4096 and end < len(b) and b[end] == 10,
           'worksheet post-header name extent', q)
    name = text_field(b[q:end])
    o.claim(owned, h['end'], end + 1, 'worksheet_name')
    p = o.take(b, end + 1, b'\0', 'worksheet metadata separator')
    prop = o.compact_blob(b, p, owned=owned)
    p = prop['end']
    annotations = []
    while b[p:p+6] != o.ZERO_LIST:
        o.need(len(annotations) < o.MAX_OBJECTS, 'worksheet annotation budget', p)
        a = o.annotation(b, p, owned)
        annotations.append(a)
        p = a['end']
    p = o.take(b, p, o.ZERO_LIST, 'worksheet annotation terminator')
    columns = []
    while b[p:p+6] != o.ZERO_LIST:
        o.need(len(columns) < o.MAX_OBJECTS, 'worksheet column budget', p)
        c = column(b, p, owned)
        columns.append(c)
        p = c['end']
    p = o.take(b, p, o.ZERO_LIST, 'worksheet column terminator')
    for role in ('axis-break', 'X', 'Y', 'Z'):
        p = o.take(b, p, o.ZERO_LIST, 'worksheet empty ' + role + ' list')
    tail = o.compact_blob(b, p, owned=owned)
    p = tail['end']
    return {'offset': start, 'end': p, 'header': s.meta(h), 'name': name,
            'name_envelope': {'start': h['end'], 'payload_start': q,
                              'payload_end': end, 'end': end + 1},
            'kind': 'worksheet', 'columns': columns, 'annotations': annotations,
            'opaque_properties': prop, 'trailing_opaque': tail}


def page(b, p, budget):
    owned = o.OwnedRanges(budget)
    h = o.record(b, p, owned)
    d = h['raw']
    o.need(len(d) in PAGE_SIZES and d[:2] == b'\0\0', 'page header type/size', p)
    out = {'offset': p, 'header': s.meta(h), 'name': named_slot(d, 2, 27),
           'layers': [], 'owned_intervals': owned, 'chain_complete': False}
    p = h['end']
    opaque = []
    for _ in range(3):
        z = o.compact_blob(b, p, owned=owned)
        opaque.append(z)
        p = z['end']
    out['post_header_opaque'] = opaque
    while b[p:p+6] != o.ZERO_LIST:
        o.need(len(out['layers']) < o.MAX_OBJECTS, 'page layer budget', p)
        h = s.frame(b, p)
        o.need(len(h['raw']) in LAYER_SIZES, 'layer header size', p)
        if h['raw'][:4] in WORKSHEET_TYPES:
            item = worksheet_layer(b, p, owned)
        elif h['raw'][:4] in GRAPH_TYPES:
            item = o.layer(b, p, owned)
            o.need(item['chain_complete'], 'graph layer incomplete: ' + item.get('blocker', ''), p)
            item['kind'] = 'graph'
        else:
            raise o.Unknown('unknown layer type at ' + str(p))
        if item['kind'] == 'graph':
            for curve in item['curves']:
                ch = s.frame(b, curve['header']['offset'])
                curve['x_selector_field'] = scalar_evidence(ch, 35, 2)
                curve['y_selector_field'] = scalar_evidence(ch, 4, 2)
        item['layer_ordinal1'] = len(out['layers']) + 1
        out['layers'].append(item)
        p = item['end']
    p = o.take(b, p, o.ZERO_LIST, 'page layer-list terminator')
    out['body_end'] = p
    # This framed post-page block contains previews in observed real sources.
    # Its codec and contents are opaque, and not used for any binding.
    z = o.compact_blob(b, p, owned=owned)
    out['post_page_opaque'] = z
    out.update(end=z['end'], chain_complete=True)
    return out


def resolve_refs(report):
    """References are validated stream ordinals, never successful-decode order."""
    datasets = report['dataset_envelope']['datasets']
    memberships = {}
    for pg in report['pages']:
        for layer in pg['layers']:
            if layer['kind'] != 'worksheet':
                continue
            for ci, col in enumerate(layer['columns'], 1):
                selector = col['dataset_selector_u16']
                member = {'page_offset': pg['offset'], 'page_ordinal1': pg['page_ordinal1'],
                          'page_name': pg['name'], 'layer_offset': layer['offset'],
                          'layer_ordinal1': layer['layer_ordinal1'], 'sheet_name': layer['name'],
                          'column_offset': col['offset'], 'column_ordinal1': ci,
                          'column_name': col['name'], 'selector_field': col['selector_field']}
                memberships.setdefault(selector, []).append(member)
    report['worksheet_memberships'] = [m for members in memberships.values() for m in members]
    def ref(selector):
        value = {'selector_u16': selector}
        if selector == 0:
            return value | {'status': 'zero selector; no dataset assigned'}
        if selector > len(datasets):
            return value | {'status': 'selector outside complete dataset list'}
        d = datasets[selector - 1]
        value.update(status='resolved sequential descriptor slot', descriptor_slot1=d['slot1'],
                     descriptor_offset=d['start'], descriptor_sha256=d['descriptor_sha256'],
                     native_descriptor_name=d.get('name'), data_type_u16=d.get('data_type_u16'),
                     stored_extent_rows=d.get('stored_extent_rows'))
        matches = memberships.get(selector, [])
        value['worksheet_membership_status'] = ('unique explicit column-selector membership' if len(matches) == 1 and report['page_list_complete']
                                               else 'one explicit membership in incomplete page prefix' if len(matches) == 1
                                               else 'ambiguous duplicate memberships' if matches
                                               else 'no explicit worksheet column in accepted page prefix')
        value['worksheet_membership_count'] = len(matches)
        value['worksheet_membership_id'] = matches[0]['column_offset'] if len(matches) == 1 else None
        return value
    for pg in report['pages']:
        for layer in pg['layers']:
            if layer['kind'] == 'worksheet':
                for col in layer['columns']:
                    col['dataset_reference'] = ref(col['dataset_selector_u16'])
            else:
                for curve in layer['curves']:
                    curve['x_reference'] = ref(curve['x_selector_u16'])
                    curve['y_reference'] = ref(curve['y_selector_u16'])
                    curve['selector_binding'] = 'source-anchored sequential descriptor references; plot semantics not inferred'
                    curve['plot_semantics'] = 'not decoded; histogram/function/matrix/other special-mode semantics not claimed'
    return report


def walk(b, *, require_complete_page_list=False):
    if type(require_complete_page_list) is not bool:
        raise TypeError('require_complete_page_list must be bool')
    if type(b) is not bytes or not 16 < len(b) <= MAX_BYTES:
        raise ValueError('Expected bytes within bounded CPYUA source limit')
    envelope = ds.walk(b)
    out = {'source_sha256': hashlib.sha256(b).hexdigest(), 'source_bytes': len(b),
           'read_only': True, 'origin_acceptance': False, 'numeric_values_decoded': False,
           'dataset_envelope': envelope, 'pages': [], 'page_list_complete': False,
           'project_tail_validated': False, 'discovery': 'strict sequential from prolog; no scan'}
    if not envelope['dataset_list_complete']:
        out['blocker'] = 'dataset envelope incomplete: ' + envelope.get('blocker', 'unknown')
        return require_complete(summarize(out), require_complete_page_list)
    p = envelope['dataset_list_end']
    out['page_list_start'] = p
    budget = {'claims': 0}
    try:
        while b[p:p+6] != o.ZERO_LIST:
            o.need(len(out['pages']) < MAX_PAGES, 'page count budget', p)
            pg = page(b, p, budget)
            pg['page_ordinal1'] = len(out['pages']) + 1
            out['pages'].append(pg)
            p = pg['end']
        out['page_list_terminator'] = {'start': p, 'end': p + 6}
        p = o.take(b, p, o.ZERO_LIST, 'page-list terminator')
        out['page_list_complete'] = True
    except (o.Unknown, s.Reject, IndexError) as error:
        out['blocker'] = str(error)
    out['parsed_until'] = p
    out['claim_budget_used'] = budget['claims']
    return require_complete(summarize(resolve_refs(out)), require_complete_page_list)


def require_complete(report, required):
    if required and not (report['dataset_envelope']['dataset_list_complete'] and report['page_list_complete']):
        raise ValueError('Complete dataset and page lists required: ' + report.get('blocker', 'unknown'))
    return report


def checked_root(b):
    """Return only a complete recognized dataset/page section; project tail is unknown."""
    return walk(b, require_complete_page_list=True)


def summarize(out):
    layers = [l for pg in out['pages'] for l in pg['layers']]
    curves = [c for l in layers for c in l.get('curves', [])]
    cols = [c for l in layers for c in l.get('columns', [])]
    refs = [c[k] for c in curves for k in ('x_reference', 'y_reference') if k in c]
    out['summary'] = {
        'complete_dataset_list': out['dataset_envelope']['dataset_list_complete'],
        'complete_page_list': out['page_list_complete'], 'pages': len(out['pages']),
        'worksheet_layers': sum(l['kind'] == 'worksheet' for l in layers),
        'graph_layers': sum(l['kind'] == 'graph' for l in layers),
        'worksheet_columns': len(cols), 'curves': len(curves),
        'resolved_curve_refs': sum(r['status'] == 'resolved sequential descriptor slot' for r in refs),
        'zero_curve_refs': sum(r['selector_u16'] == 0 for r in refs),
        'out_of_range_curve_refs': sum(r['status'] == 'selector outside complete dataset list' for r in refs),
        'curve_refs_unique_worksheet_membership': sum(r.get('worksheet_membership_status') == 'unique explicit column-selector membership' for r in refs),
        'duplicate_column_selectors': len({c['dataset_selector_u16'] for c in cols if c.get('dataset_reference', {}).get('worksheet_membership_status') == 'ambiguous duplicate memberships'}),
        'out_of_range_column_refs': sum(c.get('dataset_reference', {}).get('status') == 'selector outside complete dataset list' for c in cols),
        'zero_column_refs': sum(c['dataset_selector_u16'] == 0 for c in cols),
        'blocker': out.get('blocker')}
    return out


def main():
    import argparse, json
    from pathlib import Path
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--require-complete-page-list', action='store_true')
    args = ap.parse_args()
    try:
        b = ds.read_bounded_source(args.source)
        result = walk(b, require_complete_page_list=args.require_complete_page_list)
        ds.write_new_result(args.out, result, source=args.source)
    except (OSError, ValueError) as error:
        ap.exit(2, str(error) + '\n')
    print(json.dumps(result['summary']))

if __name__ == '__main__':
    main()
