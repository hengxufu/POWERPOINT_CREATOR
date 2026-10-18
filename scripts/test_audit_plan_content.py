import unittest
from audit_plan_content import audit


class PlanContentTests(unittest.TestCase):
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
