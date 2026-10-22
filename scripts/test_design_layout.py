"""Offline geometry/semantic tests, not fabricated visual reviews."""
import copy
import unittest
from design_layout import audit, text_pressure
from asset_job import prompt


def plan():
    return {'design_system':{'theme_profile':'beihang-blue'}, 'slides':[
        {'slide_id':'s1', 'layout_family':'figure-analysis', 'reading_order':['figure','explanation'],
         'alignment_groups':[{'axis':'top','members':['figure','explanation']}],
         'content_blocks':[
             {'object_id':'figure','role':'primary','source_ref':'source-1','box_inches':[.7,1.8,7.5,4.7]},
             {'object_id':'explanation','role':'secondary','text':'证据解读','font_pt':20,'box_inches':[8.6,1.8,3.9,4.7]}]}]}


class DesignTests(unittest.TestCase):
    def test_declared_indent_reduces_capacity_and_rejects_invalid_values(self):
        item = {'text':'中文说明内容'*5, 'font_pt':20, 'box_inches':[1,2,3,2]}
        baseline = text_pressure(item)
        item['text_layout'] = {'indent_pt':90}
        self.assertGreater(text_pressure(item)['estimated_lines'], baseline['estimated_lines'])
        for invalid in (-1, float('nan'), True):
            item['text_layout']['indent_pt'] = invalid
            with self.assertRaises(ValueError): text_pressure(item)

    def test_text_pressure_is_advisory_and_does_not_shrink_content(self):
        value=plan()
        item=value['slides'][0]['content_blocks'][1]
        item['text']='在相同实验条件下，需要保留样本量与测量不确定性。'*25
        original=copy.deepcopy(value)
        self.assertIn('text_pressure',self.codes(value))
        self.assertEqual(audit(value)['geometry_errors'],0)
        self.assertEqual(value,original)
        item['box_inches']=[1,1,10,5]
        item['text']='证据支持有条件的结论。'
        self.assertFalse(text_pressure(item)['pressure'])

    def test_text_spacing_breaks_and_invalid_values(self):
        item={'text':'A\nB\nC','font_pt':20,'box_inches':[1,1,4,.6]}
        self.assertEqual(text_pressure(item)['estimated_lines'],3)
        self.assertTrue(text_pressure(item)['pressure'])
        narrow={'text':'测','font_pt':20,'box_inches':[1,1,.3,2]}
        self.assertTrue(text_pressure(narrow)['pressure'])
        item['text_layout']={'line_spacing':float('nan')}
        with self.assertRaises(ValueError):text_pressure(item)
        item['type']='formula'
        self.assertIsNone(text_pressure(item))

    def test_spacing_and_caption_links(self):
        value=plan();slide=value['slides'][0]
        slide['spacing_groups']=[{'axis':'horizontal','members':['figure','explanation'],'min_gap_inches':.5}]
        self.assertIn('tight_spacing',self.codes(value))
        slide['content_blocks'][1]['caption_for']='figure'
        slide['content_blocks'][1]['box_inches']=[9,1.8,3,4.7]
        self.assertIn('detached_caption',self.codes(value))
        slide['content_blocks'][1]['caption_for']='missing'
        self.assertIn('caption_target',self.codes(value))
        slide['spacing_groups'][0]['members']=['figure','missing']
        self.assertIn('spacing_group',self.codes(value))

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
