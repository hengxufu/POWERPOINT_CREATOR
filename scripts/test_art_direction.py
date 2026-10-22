"""Offline visual contract tests, not rendered aesthetic evaluations."""
import copy
import unittest
from art_direction import direction, asset_context, contrast, audit, representatives


class ArtTests(unittest.TestCase):
    def test_aspect_fit_and_source_objects(self):
        request = {'object_id':'icon', 'box_inches':[1,2,5,1], 'aspect':'1:1'}
        plan = {'slides':[{'slide_id':'s1','asset_requests':[request]}]}
        self.assertEqual(audit(plan)['findings'][0]['code'], 'asset_aspect_fit')
        request['aspect'] = '5:1'
        self.assertEqual(audit(plan)['findings'], [])
        request['aspect'] = 'nan:1'
        self.assertEqual(audit(plan)['findings'][0]['code'], 'invalid_asset_aspect')
        request['decision'] = 'native_or_source'
        request['visual_context'] = {'lighting':'Different source light'}
        self.assertEqual(audit(plan)['findings'], [])

    def test_profile_defaults_and_theme_color(self):
        self.assertEqual(direction(profile='scholarship')['art_direction'],'achievement-story')
        self.assertEqual(direction(profile='challenge')['art_direction'],'technical-product')
        self.assertEqual(direction()['art_direction'],'research-editorial')
        self.assertEqual(direction({'theme_profile':'none'},'scholarship')['color_roles']['primary'],'#991F28')
        from beihang_theme import PROFILES
        self.assertEqual(direction({'theme_profile':'beihang-blue'})['color_roles']['primary'],'#'+PROFILES['beihang-blue'])

    def test_style_inheritance_preserves_explicit_values_and_input(self):
        plan={'design_system':{'image_defaults':{'material':'User matte material','lighting':'User soft light'}}}
        slide={'slide_id':'s1','title':'Synthetic','visual_context':{'viewpoint':'front'}}
        request={'visual_context':{'material':'Intentional exception'},'box_inches':[1,2,3,4]}
        original=copy.deepcopy((plan,slide,request))
        result=asset_context(plan,slide,request)
        self.assertEqual(result['lighting'],'User soft light')
        self.assertEqual(result['material'],'Intentional exception')
        self.assertEqual(result['viewpoint'],'front')
        self.assertIn('[1, 2, 3, 4]',result['placement'])
        self.assertEqual((plan,slide,request),original)

    def test_solid_contrast_and_unknown_background(self):
        self.assertAlmostEqual(contrast('#000000','#FFFFFF'),21)
        self.assertEqual(contrast('#FFFFFF','#FFFFFF'),1)
        with self.assertRaises(ValueError):contrast('gradient','#FFFFFF')
        plan={'slides':[{'slide_id':'s1','content_blocks':[{'text':'Synthetic','text_color':'#EEEEEE','background_color':'#FFFFFF'}]}]}
        self.assertEqual(audit(plan)['findings'][0]['code'],'low_contrast')
        plan['slides'][0]['content_blocks'][0]['background_color']='photo'
        self.assertEqual(audit(plan)['findings'][0]['code'],'contrast_needs_render')

    def test_series_drift_requires_reason_and_is_advisory(self):
        request={'object_id':'icon','visual_context':{'lighting':'Right dramatic light'}}
        plan={'slides':[{'slide_id':'s1','asset_requests':[request]}]}
        result=audit(plan)
        self.assertEqual(result['findings'][0]['code'],'asset_family_drift')
        request['style_override_reason']='Different physical illumination is the content of this page'
        self.assertEqual(audit(plan)['findings'],[])
        self.assertTrue(result['visual_review_required'])

    def test_representative_selection_is_content_based_and_explicit_override_wins(self):
        plan={'slides':[{'slide_id':'s1','theme_variant':'cover'},
                        {'slide_id':'s2','layout_family':'method-process'},
                        {'slide_id':'s3','content_blocks':[{'source_ref':'fig1'},{'data_ref':'data'}]}]}
        self.assertEqual(representatives(plan),{'cover':'s1','technical':'s2','dense':'s3'})
        plan['representative_slides']={'dense':'s2'}
        self.assertEqual(representatives(plan)['dense'],'s2')
        plan['representative_slides']['dense']='missing'
        with self.assertRaises(ValueError):representatives(plan)


if __name__=='__main__':unittest.main()
