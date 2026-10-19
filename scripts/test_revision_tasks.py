"""Synthetic revision signals; no real source validation or visual review."""
import copy
import unittest
from revision_tasks import build, markdown, request_signature


class RevisionTests(unittest.TestCase):
    def test_priorities_deduplication_and_no_mutation(self):
        plan={'slides':[{'slide_id':'s1','slide_number':1,'title':'SYNTHETIC'}]}
        content={'slides':[{'slide_id':'s1','review_signals':['no_evidence_locator: missing','no_evidence_locator: missing']}]}
        finding={'slide_id':'s1','code':'text_pressure','severity':'warning','objects':['body'],'message':'Synthetic pressure'}
        layout={'findings':[finding,{**finding,'severity':'error','code':'outside_canvas'}]}
        art={'findings':[{'slide_id':'s1','object_id':'icon','code':'asset_family_drift','action':'Synthetic check'}]}
        original=copy.deepcopy((plan,content,layout,art))
        result=build(plan,content,layout,art)
        self.assertEqual([t['priority'] for t in result['tasks']],[0,1,2,3])
        self.assertTrue(all(t['status']=='needs_review' for t in result['tasks']))
        self.assertEqual(result['automatic_fixes'],0)
        self.assertEqual((plan,content,layout,art),original)
        self.assertEqual(build(plan,content,layout,art),result)
        self.assertIn('保留条件',markdown(result))

    def test_no_signals_is_not_a_pass(self):
        report=build({'slides':[]},{},{},{})
        self.assertEqual(report['count'],0)
        self.assertNotIn('ready',report)
        self.assertIn('实际渲染',markdown(report))

    def test_only_image_relevant_design_changes_affect_binding(self):
        plan={'design_system':{'font_roles_pt':{'body':20}}}
        slide={'slide_id':'s1'};request={'single_subject_prompt':'Synthetic icon'}
        original=request_signature(plan,slide,request)
        plan['design_system']['font_roles_pt']['body']=24
        self.assertEqual(request_signature(plan,slide,request),original)
        plan['design_system']['image_defaults']={'lighting':'new light'}
        self.assertNotEqual(request_signature(plan,slide,request),original)


if __name__=='__main__':unittest.main()
