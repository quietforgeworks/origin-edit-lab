#!/usr/bin/env python3
"""Synthetic approval binding tests. No application or real user evidence is mocked as authorized."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from layout_plan import alignment_bindings, plan_digest, read_json, require_alignment_approval, review_summary, sha256


class LayoutPlanTests(unittest.TestCase):
    def setUp(self):
        self.source = b'synthetic source bytes'
        self.guides = b'synthetic preview bytes'
        self.plan = {
            'schema_version': 1, 'plan_version': 'proposal-1',
            'source_sha256': sha256(self.source), 'guides_sha256': sha256(self.guides),
            'questions': [], 'alignments': [{
                'id': 'row-a', 'reference': {'panel': 'Panel A', 'object': 'frame-a', 'role': 'plot_frame', 'edge': 'bottom', 'basis': 'stroke_outer', 'axis': 'y'},
                'target': {'panel': 'Panel B', 'object': 'frame-b', 'role': 'plot_frame', 'edge': 'bottom', 'basis': 'stroke_outer', 'axis': 'y'},
                'coordinate_pt': 250.0, 'certainty': 'clear'}]}
        self.approval = self.make_approval()

    def make_approval(self):
        return {'decision': 'approve', 'plan_version': self.plan['plan_version'],
                'source_sha256': self.plan['source_sha256'], 'guides_sha256': self.plan['guides_sha256'],
                'plan_sha256': plan_digest(self.plan), 'alignments': alignment_bindings(self.plan),
                'user_confirmation': 'Synthetic test evidence only'}

    def check(self, approval=None):
        return require_alignment_approval(self.source, self.guides, self.plan, self.approval if approval is None else approval)

    def test_approved_binding(self):
        self.assertEqual(self.check()['status'], 'approved_binding_verified')
        self.assertFalse(self.check()['files_modified'])

    def test_no_approval_refused(self):
        with self.assertRaises(ValueError):
            require_alignment_approval(self.source, self.guides, self.plan, None)

    def test_review_summary_is_not_approval(self):
        summary = review_summary(self.plan)
        self.assertEqual(summary['status'], 'review_required')
        with self.assertRaises(ValueError):
            self.check(summary)

    def test_unresolved_questions_block_even_matching_approval(self):
        self.plan['questions'] = ['Which lower edge should Panel B follow?']
        self.approval = self.make_approval()
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            self.check()

    def test_uncertain_pair_requires_exact_confirmation(self):
        self.plan['alignments'][0]['certainty'] = 'needs_confirmation'
        with self.assertRaises(ValueError):
            self.check()
        self.approval = self.make_approval()
        self.assertEqual(self.check()['alignment_count'], 1)

    def test_changed_source_or_guide_blocked(self):
        for source, guide in [(self.source + b'!', self.guides), (self.source, self.guides + b'!')]:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'changed'):
                require_alignment_approval(source, guide, self.plan, self.approval)

    def test_every_approval_binding_guarded(self):
        replacements = {'decision': 'pending', 'plan_version': 'proposal-2', 'source_sha256': '0' * 64,
                        'guides_sha256': '0' * 64, 'plan_sha256': '0' * 64, 'user_confirmation': '', 'alignments': []}
        for key, value in replacements.items():
            with self.subTest(key=key):
                approval = copy.deepcopy(self.approval)
                approval[key] = value
                with self.assertRaises(ValueError):
                    self.check(approval)

    def test_panel_edge_bindings_cannot_change(self):
        for location in ['reference', 'target']:
            for key, value in [('panel', 'Panel C'), ('edge', 'top')]:
                approval = copy.deepcopy(self.approval)
                approval['alignments'][0][location][key] = value
                with self.subTest(location=location, key=key), self.assertRaisesRegex(ValueError, 'panel-edge'):
                    self.check(approval)

    def test_plan_changed_even_same_version_blocked(self):
        self.plan['alignments'][0]['coordinate_pt'] = 251.0
        with self.assertRaisesRegex(ValueError, 'complete plan'):
            self.check()

    def test_unknown_fields_duplicate_targets_and_nonfinite_blocked(self):
        bad = copy.deepcopy(self.plan); bad['extra'] = 1
        with self.assertRaises(ValueError): plan_digest(bad)
        bad = copy.deepcopy(self.plan); bad['alignments'].append(copy.deepcopy(bad['alignments'][0]))
        bad['alignments'][1]['id'] = 'row-b'
        with self.assertRaises(ValueError): plan_digest(bad)
        for number in [True, float('nan'), float('inf')]:
            bad = copy.deepcopy(self.plan); bad['alignments'][0]['coordinate_pt'] = number
            with self.assertRaises(ValueError): plan_digest(bad)

    def test_digest_independent_of_object_key_order(self):
        reversed_plan = dict(reversed(list(self.plan.items())))
        self.assertEqual(plan_digest(self.plan), plan_digest(reversed_plan))

    def test_title_ink_edges_centers_and_rotated_baselines(self):
        for edge, basis, axis in [('left', 'ink', 'x'), ('right', 'ink', 'x'), ('top', 'ink', 'y'),
                                  ('bottom', 'ink', 'y'), ('center_x', 'ink', 'x'), ('center_y', 'ink', 'y'),
                                  ('baseline', 'baseline', 'x'), ('baseline', 'baseline', 'y')]:
            with self.subTest(edge=edge, axis=axis):
                for key in ['reference', 'target']:
                    self.plan['alignments'][0][key].update(role='y_axis_title', edge=edge, basis=basis, axis=axis)
                self.approval = self.make_approval()
                self.assertEqual(self.check()['alignment_count'], 1)

    def test_text_boxes_are_not_ink_or_baselines(self):
        anchor = self.plan['alignments'][0]['target']
        anchor.update(role='x_axis_title', basis='textbox')
        with self.assertRaisesRegex(ValueError, 'glyph ink'):
            plan_digest(self.plan)
        anchor.update(edge='baseline', basis='ink')
        with self.assertRaisesRegex(ValueError, 'actual transformed'):
            plan_digest(self.plan)

    def test_invalid_axes_are_refused(self):
        self.plan['alignments'][0]['target']['axis'] = 'x'
        with self.assertRaisesRegex(ValueError, 'require the y'):
            plan_digest(self.plan)

    def test_text_roles_have_explicit_ink_anchors(self):
        for role in ['panel_title', 'panel_label', 'tick_label', 'condition_label', 'reference_label']:
            with self.subTest(role=role):
                for key in ['reference', 'target']:
                    self.plan['alignments'][0][key].update(role=role, basis='ink')
                self.approval = self.make_approval()
                self.assertEqual(self.check()['alignment_count'], 1)

    def test_cli_and_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            files = {'source.bin': self.source, 'guides.bin': self.guides,
                     'plan.json': json.dumps(self.plan).encode(), 'approval.json': json.dumps(self.approval).encode()}
            for name, data in files.items(): (root / name).write_bytes(data)
            script = Path(__file__).with_name('layout_plan.py')
            command = [sys.executable, str(script), 'check', str(root / 'plan.json'), '--source', str(root / 'source.bin'),
                       '--guides', str(root / 'guides.bin'), '--approval', str(root / 'approval.json')]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)['files_modified'])
            for name, data in files.items(): self.assertEqual((root / name).read_bytes(), data)
            (root / 'approval.json').write_text('{}')
            blocked = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(blocked.returncode, 2)
            self.assertEqual(sorted(p.name for p in root.iterdir()), sorted(files))
            (root / 'plan.json').write_text('{"key": 1, "key": 2}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
                read_json(root / 'plan.json')


if __name__ == '__main__':
    unittest.main()
