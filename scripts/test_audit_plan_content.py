import unittest
from audit_plan_content import audit


class PlanContentTests(unittest.TestCase):
    def test_dependency_and_repetition_are_actionable_without_rewriting(self):
        plan = {'slides': [
            {'slide_id':'s1', 'takeaway':'相同结论', 'depends_on':['s2','missing']},
            {'slide_id':'s2', 'takeaway':'相同 结论', 'depends_on':['s1']}]}
        result = audit(plan)
        self.assertTrue(any(s.startswith('forward_dependency:') for s in result['slides'][0]['review_signals']))
        self.assertTrue(any(s.startswith('unknown_dependency:') for s in result['slides'][0]['review_signals']))
        self.assertTrue(any(s.startswith('repeated_takeaway:') for s in result['slides'][1]['review_signals']))
        plan['slides'][0]['nonlinear_reason'] = '先结果后推导'
        plan['slides'][1]['content_repeat_reason'] = '总结回顾'
        plan['slides'][1]['depends_on'] = 's1'
        result = audit(plan)
        self.assertFalse(any(s.startswith('forward_dependency:') for s in result['slides'][0]['review_signals']))
        self.assertFalse(any(s.startswith('repeated_takeaway:') for s in result['slides'][1]['review_signals']))
        self.assertTrue(any(s.startswith('invalid_dependency:') for s in result['slides'][1]['review_signals']))

    def test_substantive_source_linked_page_has_no_structural_signals(self):
        plan = {'slides': [{'slide_number': 1, 'slide_id': 's1', 'theme_variant': 'content',
                            'content_blocks': [{'text': '合成方法先控制输入条件，再比较处理组与对照组；结论仅限相同条件下的方向差异。',
                                                'source_ref': 'synthetic-source:p3'}],
                            'speaker_notes': '先交代比较口径，再解释差异。'}]}
        self.assertFalse(audit(plan)['review_required'])

    def test_thin_page_is_flagged_without_inventing_content(self):
        plan = {'slides': [{'slide_number': 1, 'slide_id': 's1', 'content_blocks': [{'text': '创新点'}]}]}
        result = audit(plan)
        self.assertEqual(len(result['slides'][0]['review_signals']), 3)
        self.assertNotIn('evidence', plan['slides'][0])


if __name__ == '__main__':
    unittest.main()
