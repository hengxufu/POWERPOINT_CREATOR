"""Synthetic parser/contract tests; these are not live web observations."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from receive_web_plan import receive, validate


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'slides': [{'slide_number': 1, 'slide_id': 's1', 'title': '问题',
            'takeaway': '需要验证', 'layout_family': 'figure-analysis', 'visual_rationale': '证据优先',
            'content_blocks': [{'text': '待验证的假设', 'box_inches': [1, 1, 4, 2]}],
            'asset_requests': [{'request_id': 'icon1', 'object_id': 'icon', 'kind': 'icon',
                                'single_subject_prompt': '单枚烧杯图标'}]}]}

    def test_good_and_wordart(self):
        validate(self.plan)
        self.plan['slides'][0]['asset_requests'][0].update(kind='art_text', exact_text='探索')
        validate(self.plan)

    def test_invalid_contracts(self):
        for mutation in ('number', 'empty', 'bounds', 'nan', 'whole_slide', 'duplicate', 'wordart'):
            with self.subTest(mutation=mutation):
                plan = copy.deepcopy(self.plan); slide = plan['slides'][0]
                if mutation == 'number': slide['slide_number'] = 2
                if mutation == 'empty': slide['content_blocks'] = [{'title': '空标题', 'box_inches': [1,1,2,2]}]
                if mutation == 'bounds': slide['content_blocks'][0]['box_inches'] = [12,1,4,2]
                if mutation == 'nan': slide['content_blocks'][0]['box_inches'][0] = float('nan')
                if mutation == 'whole_slide': slide['asset_requests'][0]['kind'] = 'full_slide'
                if mutation == 'duplicate': slide['asset_requests'] *= 2
                if mutation == 'wordart': slide['asset_requests'][0]['kind'] = 'art_text'
                with self.assertRaises(ValueError): validate(plan)

    def test_receive_fenced_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); reply = root/'reply.txt'; evidence = root/'evidence.txt'
            reply.write_text('```json\n'+json.dumps(self.plan)+'\n```', encoding='utf-8')
            evidence.write_text('SYNTHETIC TEST ONLY', encoding='utf-8')
            args = (reply, evidence, 'https://chatgpt.com/c/test-fixture', 'GPT-6', root/'out')
            receive(*args)
            self.assertTrue((root/'out/deck_plan.json').is_file())
            report = json.loads((root/'out/layout-plan-audit.json').read_text(encoding='utf-8'))
            self.assertTrue(report['visual_review_required'])
            self.assertGreater(report['geometry_errors'], 0)  # Legacy fixture lacks IDs/asset boxes; never silently certified.
            import hashlib
            self.assertEqual(report['plan_sha256'], hashlib.sha256((root/'out/deck_plan.json').read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError): receive(*args)
            with self.assertRaises(ValueError): receive(reply,evidence,'https://example.com','GPT-6',root/'bad')
            with self.assertRaises(ValueError): receive(reply,evidence,args[2],'unverified',root/'bad')


if __name__ == '__main__': unittest.main()
