# SPDX-License-Identifier: MIT
"""Synthetic semantic observations only; no private figure or external runtime."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import figure_quality_check as qc

H = hashlib.sha256(b'unchanged semantic content').hexdigest()


def element(eid, kind, bbox, parent=None, role=None):
    return dict(id=eid, parent_id=parent, source_parent_id=parent, kind=kind, role=role or kind,
                coordinate_space='layout', source_present=True, present=True,
                bbox=bbox, source_bbox=copy.deepcopy(bbox), bbox_basis='ink' if kind=='text' else 'stroke_outer',
                clip_bbox=None, transform=dict(matrix=[1,0,0,1,0,0],allowed=['identity','translate'],evidence='Known synthetic source-to-final transform'),
                glyph=None, ownership=None, scientific_ratio=None, scale_bar=None, fingerprints=[],
                coverage=dict(x='measured',y='measured',reason='Synthetic full member inventory; no peer-coordinate equality inferred'),
                evidence='Synthetic source and candidate semantic node observations')


def fingerprint(kind):
    return dict(kind=kind,before=H,after=H,evidence='Exact synthetic semantic payload SHA-256, independent of placement')


def anchor(aid,eid,axis,kind,pos,basis='stroke_outer'):
    return dict(id=aid,element_id=eid,axis=axis,kind=kind,basis=basis,position_pt=pos,evidence='Known synthetic visible anchor in final points')


def constraint(cid,ids,offsets):
    return dict(id=cid,anchor_ids=ids,target_offsets_pt=offsets,tolerance_pt=.05,
                relationship='peer_layout',evidence='Fixed synthetic layout requirement established before checking candidate')


def base_document(source_hash,candidate_hash):
    p1=element('panel1','frame',[.1,.2,.3,.6]); p2=element('panel2','frame',[.6,.2,.3,.6])
    l1=element('letter1','text',[.08,.15,.02,.03],'panel1','panel_label')
    l2=element('letter2','text',[.58,.15,.02,.03],'panel2','panel_label')
    for l, owner, neighbor in [(l1,'panel1','panel2'),(l2,'panel2','panel1')]:
        l['glyph']=dict(ink_height_pt=3,peer_group='panel_letters',comparison_key='H',face='synthetic_face',weight='regular',method='rendered_mask',evidence='Synthetic matching H glyph ink height at final 100-point canvas')
        l['fingerprints']=[fingerprint('text')]
        l['ownership']=dict(frame_id=owner,neighbor_frame_ids=[neighbor],evidence='Source-defined own frame and adjacent frame')
    return dict(schema_version=1,source_sha256=source_hash,candidate_sha256=candidate_hash,
        canvas=dict(width_pt=100,height_pt=100,evidence='Known synthetic final output size'),
        thresholds=dict(ownership_max_gap_pt=6,ownership_neighbor_margin_pt=2,glyph_relative_tolerance=.05,
                        anisotropy_relative_tolerance=.01,ratio_relative_tolerance=.001,scale_bar_relative_tolerance=.001,
                        geometry_tolerance_pt=.01,evidence='Synthetic tolerances fixed before candidate; not universal style defaults'),
        elements=[p1,p2,l1,l2],collision_checks=[],
        selection_checks=[dict(id='selection1',owner_id='panel1',expected_ids=['panel1','letter1'],selected_ids=['panel1','letter1'],evidence='Complete semantic panel selection'),
                          dict(id='selection2',owner_id='panel2',expected_ids=['panel2','letter2'],selected_ids=['panel2','letter2'],evidence='Complete semantic panel selection')],
        anchors=[anchor('left1','panel1','x','left',10),anchor('left2','panel2','x','left',60),
                 anchor('right1','panel1','x','right',40),anchor('right2','panel2','x','right',90),
                 anchor('base1','letter1','y','baseline',17,'baseline'),anchor('base2','letter2','y','baseline',17,'baseline')],
        alignment_checks=[constraint('left_edges',['left1','left2'],[0,50]),constraint('right_edges',['right1','right2'],[0,50]),constraint('letter_baselines',['base1','base2'],[0,0])])


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.source=self.root/'source.synthetic'; self.source.write_bytes(b'synthetic source only\n')
        self.candidate=self.root/'candidate.synthetic'; self.candidate.write_bytes(b'synthetic candidate only\n')
        self.doc=base_document(qc.sha256_file(self.source),qc.sha256_file(self.candidate))
    def tearDown(self): self.tmp.cleanup()
    def report(self): return qc.check(self.doc,self.source,self.candidate)
    def findings(self,code,status=None):
        return [f for f in self.report()['findings'] if f['code']==code and (status is None or f['status']==status)]
    def invalid(self):
        with self.assertRaises(qc.InvalidObservation): self.report()
    def test_intact_baseline_passes(self):
        self.assertEqual(self.report()['status'],'checks_passed')
    def test_stale_source_hash_rejected(self):
        self.source.write_bytes(b'changed source')
        self.invalid()
    def test_stale_candidate_hash_rejected(self):
        self.candidate.write_bytes(b'changed candidate')
        self.invalid()
    def test_duplicate_ids_rejected(self):
        self.doc['elements'][1]['id']='panel1'; self.invalid()
    def test_nonfinite_rejected(self):
        for n in [float('nan'),float('inf'),float('-inf')]:
            self.doc['canvas']['width_pt']=n; self.invalid()
    def test_bool_number_rejected(self):
        self.doc['canvas']['width_pt']=True; self.invalid()
    def test_huge_integer_rejected(self):
        self.doc['canvas']['width_pt']=10**1000; self.invalid()
    def test_negative_or_excessive_bbox_rejected(self):
        for b in [[.1,.2,-.3,.4],[3,.2,.3,.4]]:
            self.doc['elements'][0]['bbox']=b; self.invalid()
    def test_unknown_field_rejected(self):
        self.doc['approval']='pass'; self.invalid()
    def test_cycle_rejected(self):
        self.doc['elements'][0]['parent_id']='panel2'; self.doc['elements'][1]['parent_id']='panel1'; self.invalid()
    def test_missing_parent_rejected(self):
        self.doc['elements'][2]['parent_id']='missing'; self.invalid()
    def test_missing_measurement_not_pass(self):
        self.doc['elements'][2]['glyph']=None
        self.assertEqual(self.report()['status'],'review_needed')
        self.assertTrue(self.findings('final_glyph_ink','unmeasured'))
    def test_unmatched_glyphs_rejected_not_compared(self):
        self.doc['elements'][3]['glyph']['comparison_key']='g'; self.invalid()
    def test_same_role_size_failure(self):
        self.doc['elements'][3]['glyph']['ink_height_pt']=4
        self.assertTrue(self.findings('glyph_peer_size','failure'))
    def test_different_role_not_forced_equal(self):
        e=self.doc['elements'][3]; e['role']='axis_title'; e['glyph']['peer_group']='axis_titles'; e['glyph']['ink_height_pt']=5
        self.assertFalse(self.findings('glyph_peer_size','failure'))
    def test_anisotropy_fails_even_if_declared_allowed(self):
        tr=self.doc['elements'][2]['transform']; tr['matrix']=[1.5,0,0,1,0,0]; tr['allowed'].append('anisotropic_scale')
        self.assertTrue(self.findings('anisotropic_distortion','failure'))
    def test_intentional_rotation_not_distortion(self):
        tr=self.doc['elements'][2]['transform']; tr['matrix']=[0,1,-1,0,0,0]; tr['allowed'].append('rotate')
        self.assertFalse(self.findings('anisotropic_distortion','failure'))
    def test_shear_classification_does_not_invent_rotation(self):
        tr=self.doc['elements'][0]['transform'];tr['matrix']=[1,0,.2,1,0,0];tr['allowed']=['shear']
        findings=[f for f in self.findings('allowed_transform') if f['element_ids']==['panel1']]
        self.assertEqual(findings[0]['status'],'pass')
        self.assertEqual(findings[0]['measurements']['operations'],['shear'])
    def test_sheared_text_still_fails_distortion(self):
        tr=self.doc['elements'][2]['transform'];tr['matrix']=[1,0,.2,1,0,0];tr['allowed']=['shear']
        self.assertTrue(self.findings('anisotropic_distortion','failure'))
    def test_singular_transform_fails(self):
        self.doc['elements'][2]['transform']['matrix']=[0,0,0,1,0,0]
        self.assertTrue(self.findings('singular_transform','failure'))
    def test_unlisted_transform_fails(self):
        self.doc['elements'][0]['transform']['matrix']=[2,0,0,2,0,0]
        self.assertTrue(self.findings('allowed_transform','failure'))
    def test_detached_letter_fails(self):
        self.doc['elements'][2]['bbox']=[.49,.15,.02,.03]
        self.assertTrue(self.findings('label_ownership','failure'))
    def test_query_bbox_cannot_certify_ownership(self):
        self.doc['elements'][0]['bbox_basis']='container'
        self.assertTrue(self.findings('label_ownership','unmeasured'))
    def test_bbox_overlap_review_only(self):
        self.doc['elements'][2]['bbox']=[.12,.22,.02,.03]
        f=self.findings('text_collision','review_needed')
        self.assertTrue(f)
        self.assertFalse(self.findings('text_collision','failure'))
    def test_bbox_boolean_cannot_claim_intersection(self):
        self.doc['collision_checks']=[dict(a='letter1',b='panel1',method='bbox_only',intersects=True,evidence='bbox only',exemption=None)]
        self.invalid()
    def test_actual_collision_fails(self):
        self.doc['collision_checks']=[dict(a='letter1',b='panel1',method='rendered_mask',intersects=True,evidence='Verified overlapping ink pixel masks',exemption=None)]
        self.assertTrue(self.findings('text_collision','failure'))
    def test_source_equal_candidate_does_not_waive_observed_collision(self):
        self.doc['candidate_sha256']=self.doc['source_sha256']
        self.doc['collision_checks']=[dict(a='letter1',b='panel1',method='rendered_mask',intersects=True,evidence='Verified inherited collision in unchanged source and candidate',exemption=None)]
        report=qc.check(self.doc,self.source,self.source)
        self.assertEqual(report['status'],'failure')
        self.assertTrue(any(f['code']=='text_collision' and f['status']=='failure' for f in report['findings']))
    def test_intentional_overlap_exempt(self):
        self.doc['collision_checks']=[dict(a='letter1',b='panel1',method='rendered_mask',intersects=True,evidence='Verified ink intersection',exemption=dict(reason='Intentional label on a non-data background patch',evidence='Separately verified intended label/background relationship and no scientific marks hidden'))]
        self.assertTrue(self.findings('text_collision','exempt'))
        self.assertFalse(self.findings('text_collision','failure'))
    def test_contour_can_clear_false_bbox_candidate(self):
        self.doc['elements'][2]['bbox']=[.12,.22,.02,.03]
        self.doc['collision_checks']=[dict(a='letter1',b='panel1',method='glyph_contour',intersects=False,evidence='Verified frame outline has no ink in interior',exemption=None)]
        self.assertTrue(self.findings('text_collision','pass'))
    def test_clipping_known_ink_fails(self):
        self.doc['elements'][2]['bbox']=[-.02,.15,.03,.03]
        self.assertTrue(self.findings('content_bounds','failure'))
    def test_clip_aperture_fails(self):
        self.doc['elements'][2]['clip_bbox']=[.09,.15,.01,.03]
        self.assertTrue(self.findings('content_bounds','failure'))
    def test_container_bounds_unknown_not_proof(self):
        self.doc['elements'][2]['bbox']=[-.02,.15,.03,.03];self.doc['elements'][2]['bbox_basis']='container'
        self.assertTrue(self.findings('content_bounds','review_needed'))
        self.assertFalse(self.findings('content_bounds','failure'))
    def test_protected_text_mutation_fails(self):
        self.doc['elements'][2]['fingerprints'][0]['after']='0'*64
        self.assertTrue(self.findings('fingerprint_text','failure'))
    def test_data_and_axes_fingerprint_mutations_fail(self):
        for kind,fp in [('curve','data'),('axis','axes')]:
            e=element('node_'+kind,kind,[.3,.3,.1,.1]);e['coordinate_space']='data';e['fingerprints']=[fingerprint(fp)];e['fingerprints'][0]['after']='1'*64
            self.doc['elements'].append(e)
            self.assertTrue(self.findings('fingerprint_'+fp,'failure'))
    def test_missing_fingerprint_unknown(self):
        self.doc['elements'][2]['fingerprints']=[]
        self.assertTrue(self.findings('fingerprint_text','unmeasured'))
    def test_removed_source_content_fails(self):
        e=self.doc['elements'][2];e['present']=False;e['bbox']=None;e['glyph']=None;e['transform']=None
        self.assertTrue(self.findings('source_content_removed','failure'))
    def test_source_membership_changed_fails(self):
        self.doc['elements'][2]['parent_id']='panel2';self.doc['elements'][2]['ownership']=None
        self.assertTrue(self.findings('semantic_parent','failure'))
    def test_selection_missing_accessory_fails(self):
        self.doc['selection_checks'][0]['selected_ids']=['panel1']
        self.assertTrue(self.findings('logical_selection','failure'))
    def test_selection_inventory_omission_fails(self):
        s=self.doc['selection_checks'][0];s['expected_ids']=['panel1'];s['selected_ids']=['panel1']
        self.assertTrue(self.findings('logical_selection','failure'))
    def test_measurement_ratio_and_scale_bar_fidelity(self):
        e=element('micrograph','image',[.1,.85,.2,.1]);e['coordinate_space']='measurement';e['bbox_basis']='image_edge';e['scientific_ratio']=dict(source=2,final=3,evidence='Known source and final physical aspect');e['fingerprints']=[fingerprint('content')]
        b=element('bar','scale_bar',[.12,.92,.04,.002],'micrograph');b['fingerprints']=[fingerprint('association')];b['scale_bar']=dict(image_id='micrograph',source_fraction=.2,final_fraction=.25,source_value=10,final_value=10,source_unit='um',final_unit='um',evidence='Known bar length divided by same image width')
        self.doc['elements'] += [e,b]
        self.assertTrue(self.findings('scientific_ratio','failure'))
        self.assertTrue(self.findings('scale_bar_calibration','failure'))
    def test_ragged_right_edges_fail_despite_left_edges_passing(self):
        self.doc['anchors'][3]['position_pt']=92
        findings=self.findings('semantic_alignment')
        states={f['measurements']['constraint_id']:f['status'] for f in findings}
        self.assertEqual(states['left_edges'],'pass');self.assertEqual(states['right_edges'],'failure')
    def test_equal_text_tops_do_not_prove_baselines(self):
        self.doc['anchors'][5]['position_pt']=18
        self.assertTrue(self.findings('semantic_alignment','failure'))
    def test_missing_baseline_unmeasured(self):
        self.doc['anchors'][5]['position_pt']=None
        self.assertTrue(self.findings('semantic_alignment','unmeasured'))
    def test_alignment_cannot_waive_requirement(self):
        self.doc['alignment_checks'][0]['exemption']='looks intentional';self.invalid()
    def test_data_elements_not_equalized_as_peers(self):
        self.doc['elements'][0]['coordinate_space']='data';self.invalid()
    def test_data_attachment_constraint_is_distinct(self):
        self.doc['elements'][0]['coordinate_space']='data'
        for c in self.doc['alignment_checks'][:2]: c['relationship']='scientific_attachment'
        self.assertEqual(self.report()['status'],'checks_passed')
    def test_duplicate_collision_pair_rejected(self):
        c=dict(a='letter1',b='panel1',method='bbox_only',intersects=None,evidence='Candidate only',exemption=None)
        self.doc['collision_checks']=[c,copy.deepcopy(c)]; self.invalid()
    def test_all_reports_are_finite_json(self):
        json.dumps(self.report(),allow_nan=False)


class CLITests(unittest.TestCase):
    setUp = CheckerTests.setUp
    tearDown = CheckerTests.tearDown
    def run_cli(self,doc=None,raw=None,extra=None,optimize=False):
        path=self.root/'observations.json'
        path.write_text(raw if raw is not None else json.dumps(doc or self.doc))
        argv=[sys.executable]+(['-O'] if optimize else [])+[str(Path(qc.__file__)),str(path),'--source',str(self.source),'--candidate',str(self.candidate)]+(extra or [])
        out=subprocess.run(argv,text=True,capture_output=True)
        self.assertEqual(out.stderr,'')
        return out.returncode,json.loads(out.stdout)
    def test_cli_exit_codes_in_both_modes(self):
        for optimized in (False,True):
            code,report=self.run_cli(optimize=optimized);self.assertEqual((code,report['status']),(0,'checks_passed'))
            bad=copy.deepcopy(self.doc);bad['elements'][2]['fingerprints'][0]['after']='0'*64
            code,report=self.run_cli(doc=bad,optimize=optimized);self.assertEqual((code,report['status']),(1,'failure'))
            unknown=copy.deepcopy(self.doc);unknown['elements'][2]['glyph']=None
            code,report=self.run_cli(doc=unknown,optimize=optimized);self.assertEqual((code,report['status']),(3,'review_needed'))
            bad=copy.deepcopy(self.doc);bad['source_sha256']='0'*64
            code,report=self.run_cli(doc=bad,optimize=optimized);self.assertEqual((code,report['status']),(2,'invalid_input'))
    def test_cli_malformed_duplicate_and_nonfinite(self):
        for raw in ['{','{"schema_version":1,"schema_version":1}',json.dumps(self.doc).replace('100,','NaN,',1),json.dumps(self.doc).replace('100,','1e999,',1)]:
            for optimized in (False,True):
                code,report=self.run_cli(raw=raw,optimize=optimized)
                self.assertEqual((code,report['status']),(2,'invalid_input'))
    def test_cli_never_overwrites_inputs_or_reports(self):
        old=self.source.read_bytes()
        code,_=self.run_cli(extra=['--output',str(self.source)])
        self.assertEqual(code,2); self.assertEqual(self.source.read_bytes(),old)
        target=self.root/'new-report.json'
        code,report=self.run_cli(extra=['--output',str(target)])
        self.assertEqual(code,0); self.assertEqual(json.loads(target.read_text()),report)
        code,_=self.run_cli(extra=['--output',str(target)])
        self.assertEqual(code,2)
    def test_cli_candidate_and_source_unchanged(self):
        before=(self.source.read_bytes(),self.candidate.read_bytes());self.run_cli()
        self.assertEqual(before,(self.source.read_bytes(),self.candidate.read_bytes()))

if __name__=='__main__': unittest.main()
