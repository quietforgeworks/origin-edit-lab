import base64,json,lzma,shutil,sys,tempfile,unittest,xml.etree.ElementTree as E
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import verify_application as v
HERE=Path(__file__).resolve().parents[1]
READY=(HERE/'application/results/curves2/curve-observation.json').is_file()
@unittest.skipUnless(READY,'requires separately generated real-application evidence')
class VerifierAttacks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for name in ('original','curves2'):
            src=HERE/'application/results'/name;dst=self.root/'application/results'/name;dst.mkdir(parents=True)
            for file in ('imported-application.lml','curve-observation.json','input.before.sha256','input.after.sha256','source-evidence.opj'):
                shutil.copyfile(src/file,dst/file)
            (dst/'Book1').mkdir();shutil.copyfile(src/'Book1/native-app-values.tsv',dst/'Book1/native-app-values.tsv')
        d=self.root/'candidates/curves2';d.mkdir(parents=True)
        for file in ('raw.json','candidate.opj'):shutil.copyfile(HERE/'candidates/curves2'/file,d/file)
        self.a=patch.object(v,'ROOT',self.root);self.b=patch.object(v,'APP',self.root/'application/results');self.a.start();self.b.start()
        self.case=self.root/'application/results/curves2'
    def tearDown(self):self.a.stop();self.b.stop();self.tmp.cleanup()
    def observe(self,fn):
        p=self.case/'curve-observation.json';o=json.loads(p.read_text());fn(o);p.write_text(json.dumps(o))
    def xml(self,fn):
        p=self.case/'imported-application.lml';raw=p.read_bytes();x=E.fromstring(lzma.decompress(raw) if raw.startswith(b'\xfd7zXZ') else raw);fn(x);p.write_bytes(E.tostring(x))
    def rejects(self):
        with self.assertRaises((RuntimeError,ValueError,KeyError)):v.verify(2)
    def test_untouched(self):self.assertEqual(v.verify(2)['source_cells_bit_exact'],200)
    def test_wrong_x_identity(self):
        self.observe(lambda o:o['curves'][1].update(x_path=o['curves'][0]['x_path']));self.rejects()
    def test_wrong_x_values(self):
        self.observe(lambda o:o['curves'][1].update(x_values=o['curves'][0]['x_values']));self.rejects()
    def test_duplicate_y_identity(self):
        self.observe(lambda o:o['curves'][1].update(y_path=o['curves'][0]['y_path']));self.rejects()
    def test_no_curve(self):
        self.observe(lambda o:o['curves'].pop());self.rejects()
    def test_no_emission(self):
        self.observe(lambda o:o['curves'][1].update(point_signal_emissions=[]));self.rejects()
    def test_bad_rendered_pair(self):
        self.observe(lambda o:o['curves'][1]['point_signal_emissions'][0]['logical_points_binary64'][4].__setitem__(0,'0000000000000000'));self.rejects()
    def test_dropped_source_row(self):
        self.observe(lambda o:o['curves'][1]['x_values'].pop());self.rejects()
    def test_masked_row(self):
        self.observe(lambda o:o['curves'][1]['x_values'][3].update(masked=True));self.rejects()
    def test_saved_wrong_x(self):
        self.xml(lambda x:x.findall('.//xyCurve')[1].find('general').set('xColumn','test_tree_import/Folder1/Book1/A'));self.rejects()
    def test_saved_bit_loss(self):
        def mutate(x):
            o=x.find(".//spreadsheet[@name='Book1']/column[@name='D']/output_filter");b=bytearray(base64.b64decode(o.tail));b[8]^=1;o.tail=base64.b64encode(b).decode()
        self.xml(mutate);self.rejects()
    def test_new_style_mutation(self):
        self.xml(lambda x:x.findall('.//xyCurve')[1].find('lines').set('width','999'));self.rejects()
    def test_new_column_mutation(self):
        self.xml(lambda x:x.find(".//spreadsheet[@name='Book1']/column[@name='C']").set('designation','2'));self.rejects()
    def test_unrelated_mutation(self):
        self.xml(lambda x:x.find(".//spreadsheet[@name='Book3']/column[@name='A']").set('width','999'));self.rejects()
    def test_unrelated_whitespace_text_mutation(self):
        self.xml(lambda x:setattr(x.find(".//spreadsheet[@name='Book3']/column[@name='A']/comment"),'text',' '));self.rejects()
    def test_unrelated_whitespace_tail_mutation(self):
        self.xml(lambda x:setattr(x.find(".//spreadsheet[@name='Book3']/column[@name='A']/comment"),'tail','\n '));self.rejects()
    def test_expected_column_tail_mutation(self):
        self.xml(lambda x:setattr(x.find(".//spreadsheet[@name='Book1']/column[@name='B']"),'tail','\n '));self.rejects()
    def test_snapshot_mutation(self):
        p=self.case/'source-evidence.opj';b=bytearray(p.read_bytes());b[-1]^=1;p.chmod(0o600);p.write_bytes(b);self.rejects()
    def test_api_duplicate_cell(self):
        p=self.case/'Book1/native-app-values.tsv';lines=p.read_text().splitlines();lines[-1]=lines[-2];p.write_text('\n'.join(lines)+'\n');self.rejects()
if __name__=='__main__':unittest.main()
