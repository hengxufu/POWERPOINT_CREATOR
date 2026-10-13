"""Offline geometry/semantic tests, not fabricated visual reviews."""
import copy
import unittest
from design_layout import audit
from asset_job import prompt


def plan():
    return {'design_system':{'theme_profile':'beihang-blue'}, 'slides':[
        {'slide_id':'s1', 'layout_family':'figure-analysis', 'reading_order':['figure','explanation'],
         'alignment_groups':[{'axis':'top','members':['figure','explanation']}],
         'content_blocks':[
             {'object_id':'figure','role':'primary','source_ref':'source-1','box_inches':[.7,1.8,7.5,4.7]},
             {'object_id':'explanation','role':'secondary','text':'证据解读','font_pt':20,'box_inches':[8.6,1.8,3.9,4.7]}]}]}


class DesignTests(unittest.TestCase):
    def codes(self, value):
        return {f['code'] for f in audit(value)['findings']}

    def test_clean_plan_not_visual_pass_or_object_count(self):
        original = plan()
        result = audit(original)
        self.assertEqual(result['geometry_errors'], 0)
        self.assertEqual(result['warnings'], 0)
        self.assertTrue(result['visual_review_required'])
        self.assertEqual(result['slides'][0]['planned_boxes'], 2)
        self.assertEqual(original, plan())

    def test_bounds_invalid_dimensions_and_identity(self):
        for box, code in [([13,2,1,1],'outside_canvas'), ([1,1,0,1],'box'),
                          ([1,1,float('nan'),1],'box'), ([10.6,.2,2,.4],'theme_collision')]:
            value = plan()
            value['slides'][0]['content_blocks'][0]['box_inches'] = box
            self.assertIn(code, self.codes(value))
            self.assertGreater(audit(value)['geometry_errors'], 0)

    def test_overlap_requires_specific_reason(self):
        value = plan()
        b = value['slides'][0]['content_blocks'][1]
        b['box_inches'] = [7,2,3,3]
        self.assertIn('overlap', self.codes(value))
        b['allowed_overlaps'] = [{'object_id':'figure','reason':''}]
        self.assertIn('overlap', self.codes(value))
        b['allowed_overlaps'][0]['reason'] = 'Native callout deliberately overlays a blank figure margin; inspect render.'
        self.assertNotIn('overlap', self.codes(value))
        self.assertIn('intentional_overlap', self.codes(value))

    def test_container_only_exempts_real_child(self):
        value = plan()
        blocks = value['slides'][0]['content_blocks']
        blocks.append({'object_id':'panel','role':'container','box_inches':[.65,1.7,7.6,4.85]})
        blocks[0]['parent_id'] = 'panel'
        self.assertNotIn('overlap', self.codes(value))
        blocks[0]['parent_id'] = 'unknown'
        self.assertIn('parent', self.codes(value))

    def test_alignment_reading_font_and_ids(self):
        value = plan()
        value['slides'][0]['content_blocks'][1]['box_inches'][1] += .1
        value['slides'][0]['content_blocks'][1]['font_pt'] = 10
        value['slides'][0]['reading_order'].append('absent')
        self.assertTrue({'alignment_drift','small_text','reading_order'} <= self.codes(value))
        value['slides'][0]['content_blocks'][1]['object_id'] = 'figure'
        self.assertIn('object_id', self.codes(value))

    def test_repetition_and_decoration_are_advisory(self):
        value = plan()
        value['slides'] = [copy.deepcopy(value['slides'][0]) for _ in range(3)]
        for number, slide in enumerate(value['slides']):
            slide['slide_id'] = str(number)
        self.assertIn('repeated_layout', self.codes(value))
        value['slides'][2]['layout_repeat_reason'] = 'Matched conditions in sequential comparisons'
        self.assertNotIn('repeated_layout', self.codes(value))
        value['slides'][0]['content_blocks'][0]['role'] = 'ornament'
        self.assertIn('decoration_budget', self.codes(value))

    def test_legacy_plan_needs_fields_not_fabricated_success(self):
        result = audit({'slides':[{'content_blocks':[{'text':'旧稿','box_inches':[1,1,4,2]}]}]})
        self.assertGreater(result['geometry_errors'], 0)
        self.assertTrue(result['visual_review_required'])

    def test_asset_optical_spec_reaches_prompt(self):
        spec = {'asset_id':'a','kind':'ornament','element':'one curved wing','slide_id':'s','object_id':'o',
                'visual_context':{'viewpoint':'three quarter','silhouette':'single clear outline',
                                  'edge_treatment':'no halo','detail_level':'readable when small','optical_padding':'10%'}}
        text = prompt(spec)
        for value in spec['visual_context'].values():
            self.assertIn(value, text)

    def test_invalid_canvas_fails(self):
        value = plan()
        value['canvas_inches'] = [True, 7.5]
        with self.assertRaises(ValueError):
            audit(value)

    def test_catalog_zones_avoid_identity_and_footer(self):
        from layout_catalog import LAYOUTS
        from design_layout import intersection
        for recipe in LAYOUTS.values():
            for box in recipe['zones'].values():
                self.assertEqual(intersection(box, [.79*13.333,.025*7.5,.185*13.333,.075*7.5]), 0)
                self.assertLessEqual(box[1]+box[3], .925*7.5)


if __name__ == '__main__':
    unittest.main()
