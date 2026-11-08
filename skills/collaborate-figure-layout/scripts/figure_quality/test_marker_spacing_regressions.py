# SPDX-License-Identifier: MIT
"""Analytic, synthetic SVG/observation regressions; no native app or recognizer.

The SVG is generated from the same explicit source geometry used for observations.
This proves checker behavior on known observations, not automatic visual extraction.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import figure_quality_check as qc
from test_figure_quality_check import element, fingerprint, anchor, constraint, base_document


def compose(left, right):
    a,b,c,d,x,y=left; e,f,g,h,u,v=right
    return [a*e+c*f,b*e+d*f,a*g+c*h,b*g+d*h,a*u+c*v+x,b*u+d*v+y]


def blank_document():
    d=base_document('0'*64,'0'*64)
    for key in ('elements','anchors','alignment_checks','collision_checks','selection_checks'): d[key]=[]
    d['canvas']['evidence']='Synthetic SVG width=height=100pt and viewBox=0 0 100 100'
    return d


def bind_files(root,doc,source_svg,candidate_svg):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    source=root/'source.svg';candidate=root/'candidate.svg'
    source.write_text(source_svg);candidate.write_text(candidate_svg)
    doc['source_sha256']=qc.sha256_file(source);doc['candidate_sha256']=qc.sha256_file(candidate)
    return doc,source,candidate


def svg(body):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="100pt" height="100pt" viewBox="0 0 100 100">'+body+'</svg>\n'


def marker_document(root, mode='shared'):
    """Three ellipse primitives, including a fill-only off-center highlight.

    Modes: all shared compensation; no compensation; only highlight missed; or
    each layer compensated around its own center (preserves shape, breaks offsets).
    """
    doc=blank_document();plot=[1.08,0,0,1,0,0]
    specs=[('outline',25,40,2.1,2.1,'fill="none" stroke="black" stroke-width="0.12"',.06),
           ('body',25,40,2,2,'fill="blue" stroke="none"',0),
           ('highlight',24.6,39.7,.7,.4,'fill="white" stroke="none"',0)]
    group=element('marker_group','object',[.2284,.3784,.0432,.0432],role='composite_marker')
    group['bbox_basis']='ink';group['transform']['matrix']=plot;group['transform']['allowed']=['anisotropic_scale']
    group['evidence']='Source-verified logical marker group, not inferred from ellipse tags or stroke presence'
    doc['elements'].append(group)
    before=[];after=[];final_boxes=[]
    for name,cx,cy,rx,ry,style,stroke in specs:
        shape=f'<ellipse id="{name}" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" {style}/>'
        local=[1,0,0,1,0,0]
        if mode=='shared' or (mode=='partial' and name!='highlight'):
            local=[1/1.08,0,0,1,25*(1-1/1.08),0]
        elif mode=='per_layer':
            local=[1/1.08,0,0,1,cx*(1-1/1.08),0]
        full=compose(plot,local)
        x,y=full[0]*cx+full[4],cy
        source_box=[(cx-rx-stroke)/100,(cy-ry-stroke)/100,2*(rx+stroke)/100,2*(ry+stroke)/100]
        final_box=[(x-(rx+stroke)*full[0])/100,(y-ry-stroke)/100,2*(rx+stroke)*full[0]/100,2*(ry+stroke)/100]
        e=element(name,'marker',final_box,'marker_group','marker_layer')
        e['coordinate_space']='data';e['source_bbox']=source_box;e['bbox_basis']='stroke_outer' if stroke else 'ink'
        e['transform']=dict(matrix=full,allowed=['identity','translate','anisotropic_scale'],evidence='Analytically composed full plot ancestor × local layer matrix in physical points')
        e['fingerprints']=[fingerprint('data'),fingerprint('content'),fingerprint('association')]
        e['evidence']='Verified source marker constituent: '+name+'; ellipse primitive; '+style
        doc['elements'].append(e);final_boxes.append(final_box)
        before.append(shape);after.append('<g transform="matrix('+ ' '.join(map(str,local)) +')">'+shape+'</g>')
        for axis,value in [('x',x),('y',y)]:
            doc['anchors'].append(anchor(name+'_'+axis,name,axis,'center_'+axis,value,'ink'))
    x1=min(b[0] for b in final_boxes);y1=min(b[1] for b in final_boxes)
    x2=max(b[0]+b[2] for b in final_boxes);y2=max(b[1]+b[3] for b in final_boxes)
    group['bbox']=[x1,y1,x2-x1,y2-y1]
    # A genuine scientific confidence-region ellipse follows data-space mapping.
    region=element('region','region_stroke',[.64692,.349,.21816,.102],role='confidence_region')
    region['coordinate_space']='data';region['source_bbox']=[.599,.349,.202,.102]
    region['transform']=dict(matrix=plot,allowed=['anisotropic_scale'],evidence='Verified data-coordinate region; full plot mapping is intentional')
    region['fingerprints']=[fingerprint('data'),fingerprint('association')]
    region['evidence']='Source identifies this ellipse as a confidence region, not a marker layer'
    doc['elements'].append(region)
    for axis,offset in [('x',-.4),('y',-.3)]:
        c=constraint('marker_offsets_'+axis,['outline_'+axis,'body_'+axis,'highlight_'+axis],[0,0,offset])
        c.update(relationship='scientific_attachment',tolerance_pt=.01,
                 evidence='Source-verified concentric body/outline plus deliberately offset highlight; preserve signed offsets, not universal concentricity')
        doc['alignment_checks'].append(c)
    doc['selection_checks']=[dict(id='complete_marker',owner_id='marker_group',expected_ids=['marker_group','outline','body','highlight'],selected_ids=['marker_group','outline','body','highlight'],evidence='All source marker constituents inventoried, including fill-only highlight')]
    region_svg='<ellipse id="region" cx="70" cy="40" rx="10" ry="5" fill="none" stroke="gray" stroke-width="0.2"/>'
    source=svg('<g id="marker_group">'+''.join(before)+'</g>'+region_svg)
    candidate=svg('<g transform="scale(1.08 1)"><g id="marker_group">'+''.join(after)+'</g>'+region_svg+'</g>')
    return bind_files(root,doc,source,candidate)


def spacing_document(root,h_gap=6,v_gap=8,inner_gap=2):
    """Synthetic glyph-outline extents, with independent inner/outer x/y gaps.

    Frame gaps remain exactly 10pt horizontal and 20pt vertical in every variant.
    Final glyph outlines, rather than nominal fonts or container boxes, supply ink.
    """
    doc=blank_document()
    specs=[('frame_left','frame',[10,20,25,20]),('frame_right','frame',[45,20,25,20]),
           ('frame_top','frame',[65,10,20,20]),('frame_bottom','frame',[65,50,20,20]),
           ('ink_left','text',[45-h_gap-6,12,6,6]),('ink_right','text',[45,12,6,6]),
           ('ink_top','text',[88,50-v_gap-6,6,6]),('ink_bottom','text',[88,50,6,6]),
           ('inner_left','text',[10,88,6,6]),('inner_right','text',[16+inner_gap,88,6,6])]
    pieces=[]
    for eid,kind,box in specs:
        e=element(eid,kind,[v/100 for v in box],role='annotation' if kind=='text' else 'frame')
        e['evidence']='Synthetic actual glyph outline/outer stroke coordinates in physical points, not queried containers'
        x,y,w,h=box
        if kind=='text':
            # An explicit H-like closed silhouette gives known six-point ink extents.
            p=[(x,y),(x+1,y),(x+1,y+2),(x+5,y+2),(x+5,y),(x+6,y),(x+6,y+6),(x+5,y+6),(x+5,y+3),(x+1,y+3),(x+1,y+6),(x,y+6)]
            pieces.append('<path id="'+eid+'" d="M'+' L'.join(f'{a},{b}' for a,b in p)+' Z" fill="black"/>')
            e['glyph']=dict(ink_height_pt=6,peer_group='outline_H',comparison_key='H',face='synthetic-verified-outline',weight='regular',method='glyph_outline',evidence='Analytically specified six-point H-like outline; no font extraction claim')
            e['fingerprints']=[fingerprint('text')]
        else:
            # Inset stroke center by .05pt so declared box is the actual outer stroke.
            pieces.append(f'<rect id="{eid}" x="{x+.05}" y="{y+.05}" width="{w-.1}" height="{h-.1}" fill="none" stroke="black" stroke-width="0.1"/>')
        doc['elements'].append(e)
    lookup={e['id']:e for e in doc['elements']}
    pairs=[('frame_gap_x','frame_left','right','frame_right','left','x',10,.01,'stroke_outer'),
           ('frame_gap_y','frame_top','bottom','frame_bottom','top','y',20,.01,'stroke_outer'),
           ('outer_ink_x','ink_left','right','ink_right','left','x',6,.2,'ink'),
           ('outer_ink_y','ink_top','bottom','ink_bottom','top','y',8,.3,'ink'),
           ('inner_ink_x','inner_left','right','inner_right','left','x',2,.15,'ink')]
    for cid,left,edge1,right,edge2,axis,target,tolerance,basis in pairs:
        ids=[]
        for eid,edge in [(left,edge1),(right,edge2)]:
            b=lookup[eid]['bbox'];x,y,w,h=[v*100 for v in b]
            value={'left':x,'right':x+w,'top':y,'bottom':y+h}[edge]
            aid=cid+'_'+eid;ids.append(aid)
            doc['anchors'].append(anchor(aid,eid,axis,edge,value,basis))
        c=constraint(cid,ids,[0,target]);c['tolerance_pt']=tolerance
        c['evidence']='Task-specific '+cid+' interval fixed from source glyph edges, final-size visual role and measurement uncertainty; ink gaps are intentionally larger outside than inside, not exactly equal'
        doc['alignment_checks'].append(c)
    # Roots are distinct semantic objects; each selection explicitly covers its own object.
    doc['selection_checks']=[dict(id='select_'+e['id'],owner_id=e['id'],expected_ids=[e['id']],selected_ids=[e['id']],evidence='Single complete source semantic object') for e in doc['elements']]
    candidate=svg(''.join(pieces))
    # Source is a separately bound intact analytic artifact. Its original placement
    # can differ; scientific text stays the same. No source figure is rewritten.
    source=svg('<!-- Intact synthetic source; exact glyph content preserved. -->'+''.join(pieces))
    return bind_files(root,doc,source,candidate)


class MarkerSpacingRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def check(self,fixture):
        doc,source,candidate=fixture
        return qc.check(doc,source,candidate)
    def findings(self,report,code,status=None):
        return [f for f in report['findings'] if f['code']==code and (status is None or f['status']==status)]
    def alignments(self,report):
        return {f['measurements']['constraint_id']:f for f in self.findings(report,'semantic_alignment')}
    def test_all_ellipse_layers_receive_distortion_checks(self):
        report=self.check(marker_document(self.root,'none'))
        failed={f['element_ids'][0] for f in self.findings(report,'anisotropic_distortion','failure')}
        self.assertEqual(failed,{'outline','body','highlight'})
        for f in self.findings(report,'anisotropic_distortion','failure'):
            self.assertAlmostEqual(f['measurements']['relative_anisotropy'],.08)
    def test_fill_only_highlight_is_not_missed_after_partial_fix(self):
        report=self.check(marker_document(self.root,'partial'))
        failed={f['element_ids'][0] for f in self.findings(report,'anisotropic_distortion','failure')}
        self.assertEqual(failed,{'highlight'})
    def test_full_ancestor_compensation_passes_not_local_matrix_only(self):
        fixture=marker_document(self.root,'shared');report=self.check(fixture)
        self.assertEqual(report['status'],'checks_passed')
        self.assertEqual(len(self.findings(report,'anisotropic_distortion','pass')),3)
        for e in fixture[0]['elements']:
            if e['kind']=='marker':self.assertAlmostEqual(e['transform']['matrix'][0],1)
    def test_individually_circular_layers_can_still_have_broken_centers(self):
        report=self.check(marker_document(self.root,'per_layer'))
        self.assertFalse(self.findings(report,'anisotropic_distortion','failure'))
        alignment=self.alignments(report)['marker_offsets_x']
        self.assertEqual(alignment['status'],'failure')
        self.assertAlmostEqual(alignment['measurements']['observed_offsets_pt'][2],-.432)
        self.assertAlmostEqual(alignment['measurements']['target_offsets_pt'][2],-.4)
    def test_intentional_offcenter_highlight_is_preserved(self):
        report=self.check(marker_document(self.root,'shared'))
        aa=self.alignments(report)
        self.assertEqual(aa['marker_offsets_x']['status'],'pass')
        self.assertAlmostEqual(aa['marker_offsets_x']['measurements']['observed_offsets_pt'][2],-.4)
        self.assertAlmostEqual(aa['marker_offsets_y']['measurements']['observed_offsets_pt'][2],-.3)
    def test_data_region_ellipse_is_not_circularized_or_flagged_as_marker(self):
        fixture=marker_document(self.root,'shared');report=self.check(fixture)
        self.assertFalse([f for f in self.findings(report,'anisotropic_distortion') if f['element_ids']==['region']])
        region=next(e for e in fixture[0]['elements'] if e['id']=='region')
        self.assertEqual(region['transform']['matrix'][0],1.08)
        self.assertNotEqual(region['bbox'][2]/region['bbox'][3],1)
        self.assertEqual(report['status'],'checks_passed')
    def test_elliptical_highlight_source_aspect_is_not_forced_to_circle(self):
        fixture=marker_document(self.root,'shared');report=self.check(fixture)
        highlight=next(e for e in fixture[0]['elements'] if e['id']=='highlight')
        self.assertAlmostEqual(highlight['bbox'][2]/highlight['bbox'][3],1.75)
        self.assertEqual(report['status'],'checks_passed')
    def test_unknown_layer_transform_remains_unmeasured(self):
        fixture=marker_document(self.root,'shared')
        next(e for e in fixture[0]['elements'] if e['id']=='highlight')['transform']=None
        report=self.check(fixture)
        self.assertEqual(report['status'],'review_needed')
        self.assertTrue([f for f in self.findings(report,'transform','unmeasured') if f['element_ids']==['highlight']])
    def test_complete_semantic_selection_detects_omitted_fill_layer(self):
        fixture=marker_document(self.root,'shared')
        fixture[0]['selection_checks'][0]['selected_ids'].remove('highlight')
        self.assertTrue(self.findings(self.check(fixture),'logical_selection','failure'))
    def test_equal_frame_gaps_do_not_clear_failed_horizontal_ink_gap(self):
        report=self.check(spacing_document(self.root,h_gap=2))
        aa=self.alignments(report)
        self.assertEqual(aa['frame_gap_x']['status'],'pass')
        self.assertEqual(aa['frame_gap_y']['status'],'pass')
        self.assertEqual(aa['outer_ink_x']['status'],'failure')
        self.assertEqual(aa['outer_ink_y']['status'],'pass')
    def test_equal_frame_gaps_do_not_clear_failed_vertical_ink_gap(self):
        aa=self.alignments(self.check(spacing_document(self.root,v_gap=3)))
        self.assertEqual(aa['frame_gap_y']['status'],'pass')
        self.assertEqual(aa['outer_ink_y']['status'],'failure')
        self.assertEqual(aa['outer_ink_x']['status'],'pass')
    def test_task_justified_small_ink_differences_are_not_exact_equality(self):
        report=self.check(spacing_document(self.root,h_gap=6.15,v_gap=8.25,inner_gap=2.1))
        self.assertEqual(report['status'],'checks_passed')
        aa=self.alignments(report)
        self.assertAlmostEqual(aa['outer_ink_x']['measurements']['observed_offsets_pt'][1],6.15)
        self.assertAlmostEqual(aa['outer_ink_y']['measurements']['observed_offsets_pt'][1],8.25)
        self.assertNotEqual(aa['outer_ink_x']['threshold'],aa['outer_ink_y']['threshold'])
    def test_hierarchy_is_concrete_not_a_universal_equal_gap(self):
        aa=self.alignments(self.check(spacing_document(self.root)))
        self.assertEqual(aa['inner_ink_x']['measurements']['observed_offsets_pt'][1],2)
        self.assertEqual(aa['outer_ink_x']['measurements']['observed_offsets_pt'][1],6)
        self.assertTrue(all(f['status']=='pass' for f in aa.values()))
    def test_missing_ink_anchor_cannot_fall_back_to_frame(self):
        fixture=spacing_document(self.root)
        next(a for a in fixture[0]['anchors'] if a['id']=='outer_ink_x_ink_left')['position_pt']=None
        report=self.check(fixture);aa=self.alignments(report)
        self.assertEqual(aa['frame_gap_x']['status'],'pass')
        self.assertEqual(aa['outer_ink_x']['status'],'unmeasured')
        self.assertEqual(report['status'],'review_needed')
    def test_observed_offsets_are_reported_for_both_axes(self):
        aa=self.alignments(self.check(spacing_document(self.root)))
        self.assertEqual(aa['outer_ink_x']['measurements']['observed_offsets_pt'],[0,6])
        self.assertEqual(aa['outer_ink_y']['measurements']['observed_offsets_pt'],[0,8])
    def test_new_failures_reach_cli_in_normal_and_optimized_modes(self):
        for name,builder,expected in [('marker',lambda p:marker_document(p,'partial'),1),('centers',lambda p:marker_document(p,'per_layer'),1),('gap',lambda p:spacing_document(p,v_gap=3),1),('intact',lambda p:marker_document(p,'shared'),0)]:
            d,s,c=builder(self.root/name);obs=s.parent/'observations.json';obs.write_text(json.dumps(d))
            for optimized in (False,True):
                cmd=[sys.executable]+(['-O'] if optimized else [])+[str(Path(qc.__file__)),str(obs),'--source',str(s),'--candidate',str(c)]
                p=subprocess.run(cmd,text=True,capture_output=True)
                self.assertEqual(p.returncode,expected,p.stdout+p.stderr)
                self.assertEqual(p.stderr,'')
                self.assertIn(json.loads(p.stdout)['status'],('failure','checks_passed'))

if __name__=='__main__':unittest.main()
