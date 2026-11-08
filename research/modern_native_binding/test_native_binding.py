"""Synthetic-only tests: names are display, selectors and hierarchy are identity."""
import unittest, struct, hashlib, tempfile, os, subprocess, sys, json
from pathlib import Path
from unittest.mock import patch
import native_binding as n

Z=bytes(5)+b'\n'
def u(v):
    out=bytearray()
    while v>=128:out.append((v&127)|128);v>>=7
    out.append(v);return bytes(out)
def frame(d):
    data=b''.join(bytes([len(d[k:k+127])])+d[k:k+127] for k in range(0,len(d),127))
    return b'\x80'+u(len(data))+data
def blob(d):return u(len(d))+d+b'\n' if d else b'\0'
def dataset(name=b'Book_A',extent=0,dtype=0x5121):
    h=bytearray(147);h[88:88+len(name)]=name;struct.pack_into('<H',h,22,dtype)
    struct.pack_into('<III',h,25,99,3,90)
    payload=b'\x05'+u(extent)
    if extent:payload+=b'\xff\xff'+u(extent)+b'\0'+u(extent*2)+b'\x64\xce\xfa'
    return frame(h)+b'\0'+payload+bytes(4)
def column(ref,name=b'A',designation=0):
    h=bytearray(519);h[0]=16;struct.pack_into('<H',h,4,ref);h[17]=designation;h[18:18+len(name)]=name
    return frame(h)+bytes(3)
def worksheet(cols=None,name=b'Sheet1',extra=b''):
    h=bytearray(409);h[:4]=b'\0\0\x5e\0'
    return frame(h)+u(len(name))+name+b'\n\0'+blob(extra)+Z+(b''.join(cols) if cols is not None else column(1))+Z*5+b'\0'
def curve(x=1,y=2,kind=200):
    h=bytearray(519);h[0]=1;struct.pack_into('<H',h,4,y);struct.pack_into('<H',h,35,x);h[76]=kind
    return frame(h)+b'\0'+blob(bytes.fromhex('01588009980340b3'))+b'\0'
def graph(curves=None):
    h=bytearray(409);h[:4]=b'\0\0\x1f\0';out=frame(h)+b'\0\n\0\0'+Z
    out+=b''.join(curves if curves is not None else [curve()])+Z*2
    for _ in range(3):
        for _ in range(6):
            a=bytearray(519);a[0]=17;out+=frame(a)
        out+=Z
    return out+b'\0'
def page(name=b'Book',layers=None,extra=b'',preview=b'preview'):
    h=bytearray(199);h[2:2+len(name)]=name
    return frame(h)+blob(extra)+bytes(2)+(b''.join(layers) if layers is not None else worksheet())+Z+blob(preview)
def project(datasets=None,pages=None,tail=b'UNVALIDATED-TAIL'):
    head=b'CPYUA 4.3811 222\n'+blob(b'meta')+b'PrvwOPJU'+bytes(8)+struct.pack('<I',115)+b'\n'+bytes(115)+b'\n'+bytes(4)+b'\n'
    ds=b''.join(datasets if datasets is not None else [dataset(b'Book_A'),dataset(b'Book_B')])
    ps=b''.join(pages if pages is not None else [page(layers=[worksheet([column(1),column(2,b'B')])]),page(b'Graph', [graph()])])
    return head+ds+Z+b'\0'+ps+Z+tail

class Binding(unittest.TestCase):
    def complete(self,b):
        r=n.walk(b);self.assertTrue(r['page_list_complete'],r.get('blocker'));return r
    def test_complete_root_and_sheet_binding(self):
        r=self.complete(project());self.assertEqual(r['summary']['worksheet_columns'],2)
        c=r['pages'][1]['layers'][0]['curves'][0]
        self.assertEqual(c['x_reference']['descriptor_slot1'],1);self.assertEqual(c['y_reference']['descriptor_slot1'],2)
        self.assertEqual(c['x_reference']['worksheet_membership_count'],1)
        self.assertFalse(r['project_tail_validated']);self.assertFalse(r['origin_acceptance'])
    def test_reordered_columns_preserve_selector_not_position(self):
        r=self.complete(project(pages=[page(layers=[worksheet([column(2,b'S'),column(1,b'T')])]),page(b'G',[graph()])]))
        members=r['worksheet_memberships'];self.assertEqual([m['column_name']['utf8'] for m in members],['S','T'])
        c=r['pages'][1]['layers'][0]['curves'][0]
        self.assertEqual(c['x_reference']['worksheet_membership_id'],members[1]['column_offset'])
        self.assertEqual(c['y_reference']['worksheet_membership_id'],members[0]['column_offset'])
    def test_sheet_labels_and_descriptor_labels_not_identity(self):
        r=self.complete(project(datasets=[dataset(b'Wrong_Z@9'),dataset(b'Wrong_Z@2')],pages=[page(layers=[worksheet([column(2,b'Same')],b'Dup'),worksheet([column(1,b'Same')],b'Dup')]),page(b'G',[graph()])]))
        c=r['pages'][1]['layers'][0]['curves'][0];mid=c['x_reference']['worksheet_membership_id']
        m=next(x for x in r['worksheet_memberships'] if x['column_offset']==mid)
        self.assertEqual(m['layer_ordinal1'],2);self.assertEqual(c['x_reference']['native_descriptor_name'],'Wrong_Z@9')
    def test_zeroextent_and_special_slots_not_dropped(self):
        r=self.complete(project(datasets=[dataset(b'Function',dtype=0x6081),dataset(b'Book_B',extent=3)]))
        c=r['pages'][1]['layers'][0]['curves'][0];self.assertEqual(c['x_reference']['data_type_u16'],0x6081)
        self.assertEqual(c['x_reference']['stored_extent_rows'],0);self.assertEqual(c['y_reference']['descriptor_slot1'],2)
        self.assertIn('not decoded',c['plot_semantics'])
    def test_zero_histogram_x_not_defaulted(self):
        r=self.complete(project(pages=[page(b'G',[graph([curve(x=0,y=2,kind=219)])])]))
        c=r['pages'][0]['layers'][0]['curves'][0];self.assertEqual(c['x_reference']['selector_u16'],0)
        self.assertNotIn('descriptor_slot1',c['x_reference']);self.assertEqual(r['summary']['zero_curve_refs'],1)
    def test_out_of_range_selectors_unresolved(self):
        r=self.complete(project(pages=[page(layers=[worksheet([column(65535)])]),page(b'G',[graph([curve(65535,3)])])]))
        self.assertEqual(r['summary']['out_of_range_curve_refs'],2);self.assertEqual(r['summary']['out_of_range_column_refs'],1)
    def test_zero_column_unresolved(self):
        r=self.complete(project(pages=[page(layers=[worksheet([column(0)])])]))
        self.assertEqual(r['summary']['zero_column_refs'],1)
    def test_duplicate_selector_not_arbitrarily_chosen(self):
        r=self.complete(project(pages=[page(layers=[worksheet([column(1)]),worksheet([column(1)])]),page(b'G',[graph()])]))
        c=r['pages'][1]['layers'][0]['curves'][0];ref=c['x_reference']
        self.assertEqual(ref['worksheet_membership_status'],'ambiguous duplicate memberships');self.assertIsNone(ref['worksheet_membership_id'])
        self.assertEqual(ref['worksheet_membership_count'],2)
    def test_prefix_membership_not_global_unique(self):
        b=project(pages=[page(layers=[worksheet([column(1)])]),page(b'G',[graph()])]);r=n.walk(b[:-10000])
        self.assertFalse(r['page_list_complete'])
        if r['pages']:self.assertEqual(r['pages'][0]['layers'][0]['columns'][0]['dataset_reference']['worksheet_membership_status'],'one explicit membership in incomplete page prefix')
    def test_graph_only_not_invented_workbook(self):
        r=self.complete(project(pages=[page(b'G',[graph()])]))
        self.assertEqual(r['summary']['worksheet_columns'],0)
        self.assertEqual(r['pages'][0]['layers'][0]['curves'][0]['x_reference']['worksheet_membership_count'],0)
    def test_nonascii_display_text_supported(self):
        r=self.complete(project(pages=[page('图'.encode(),[worksheet([column(1,'列'.encode())],'页'.encode())])]))
        self.assertEqual(r['pages'][0]['name']['utf8'],'图');self.assertEqual(r['worksheet_memberships'][0]['sheet_name']['utf8'],'页')
    def test_bad_utf8_is_hex_not_guess(self):
        r=self.complete(project(pages=[page(b'\xff',[worksheet([column(1,b'\xff')],b'\xff')])]))
        self.assertIsNone(r['pages'][0]['name']['utf8'])
    def test_embedded_fake_page_never_discovered(self):
        fake=page(b'Fake',[graph()]);r=self.complete(project(pages=[page(layers=[worksheet()],extra=b'\n'+fake),page(b'G',[graph()])]))
        self.assertEqual(len(r['pages']),2);self.assertNotIn('Fake',[p['name']['utf8'] for p in r['pages']])
    def test_arbitrary_prefix_before_first_page_stops(self):
        b=project();r=n.walk(b);at=r['page_list_start'];bad=b[:at]+b'JUNK\n'+b[at:];r=n.walk(bad)
        self.assertFalse(r['page_list_complete']);self.assertEqual(r['pages'],[])
    def test_ambiguous_preview_not_guessed(self):
        b=project(pages=[page(preview=b'\x01'+b'Q'*128)]);r=n.walk(b)
        self.assertFalse(r['page_list_complete']);self.assertIn('ambiguous',r['blocker'])
    def test_unknown_worksheet_type_stops(self):
        b=project();b=b.replace(b'\0\0\x5e\0',b'\0\0\x5d\0',1);r=n.walk(b)
        self.assertFalse(r['page_list_complete']);self.assertEqual(r['pages'],[])
    def test_unknown_column_type_stops(self):
        b=project();r=n.walk(b);at=r['pages'][0]['layers'][0]['columns'][0]['header']['offset'];f=n.s.frame(b,at);where=f['mapping'][0];bad=b[:where]+b'\x11'+b[where+1:]
        r=n.walk(bad);self.assertFalse(r['page_list_complete']);self.assertEqual(r['pages'],[])
    def test_nonempty_worksheet_axis_not_skipped(self):
        b=project();r=n.walk(b);at=r['pages'][0]['layers'][0]['columns'][-1]['end']+len(Z)
        r=n.walk(b[:at]+b'\x01'+b[at+1:]);self.assertFalse(r['page_list_complete']);self.assertIn('axis-break',r['blocker'])
    def test_page_limit_before_extra_parse(self):
        with patch.object(n,'MAX_PAGES',1):
            r=n.walk(project());self.assertFalse(r['page_list_complete']);self.assertEqual(len(r['pages']),1)
    def test_every_prefix_before_page_list_end_cannot_complete(self):
        b=project(pages=[page(layers=[worksheet()])],tail=b'');r=self.complete(b)
        for k in range(17,r['page_list_terminator']['end']):
            q=n.walk(b[:k]);self.assertFalse(q['page_list_complete'],k)
    def test_bad_dataset_prevents_any_page_discovery(self):
        b=project();r=n.walk(b);at=r['dataset_envelope']['datasets'][0]['descriptor_end']+1
        q=n.walk(b[:at]+b'\x06'+b[at+1:]);self.assertEqual(q['pages'],[]);self.assertFalse(q['page_list_complete'])
    def test_scalar_field_evidence_matches_source(self):
        b=project();r=self.complete(b);c=r['pages'][1]['layers'][0]['curves'][0]
        for key in ['x_selector_field','y_selector_field']:
            e=c[key];self.assertEqual(bytes(b[o] for o in e['literal_offsets']).hex(),e['decoded_le_hex'])
    def test_source_immutable(self):
        b=project();sha=hashlib.sha256(b).hexdigest();self.complete(b);self.assertEqual(hashlib.sha256(b).hexdigest(),sha)
    def test_checked_root_requires_complete_lists(self):
        b=project();self.assertTrue(n.checked_root(b)['page_list_complete'])
        r=n.walk(b);at=r['page_list_terminator']['start']
        with self.assertRaisesRegex(ValueError,'Complete dataset and page lists'):
            n.checked_root(b[:at])
        r=n.walk(b);at=r['dataset_envelope']['datasets'][0]['descriptor_end']+1
        with self.assertRaisesRegex(ValueError,'Complete dataset and page lists'):
            n.walk(b[:at]+b'\x06'+b[at+1:],require_complete_page_list=True)
        with self.assertRaises(TypeError):n.walk(b,require_complete_page_list=1)
    def test_api_input_bounds(self):
        for b in [None,bytearray(project()),b'bad',b'']:
            with self.assertRaises(ValueError):n.walk(b)

class CLI(unittest.TestCase):
    def test_new_output_and_no_overwrite_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source';data=project();src.write_bytes(data);out=root/'out.json'
            cmd=[sys.executable]+(['-O'] if sys.flags.optimize else [])+[n.__file__,str(src),'--out']
            p=subprocess.run(cmd+[str(out)],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(json.loads(out.read_text())['page_list_complete'])
            hard=root/'hard';os.link(src,hard);sym=root/'sym';sym.symlink_to(src)
            for target in [src,out,hard,sym]:
                p=subprocess.run(cmd+[str(target)],capture_output=True,text=True,timeout=10);self.assertEqual(p.returncode,2)
            self.assertEqual(src.read_bytes(),data)
    def test_fifo_read_fails_without_hanging(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fifo';os.mkfifo(p)
            with self.assertRaisesRegex(ValueError,'regular'):n.ds.read_bounded_source(p)

if __name__=='__main__':unittest.main()
