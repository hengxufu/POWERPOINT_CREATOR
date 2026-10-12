"""Synthetic offline tests; no browser or image generation occurs here."""
import json
import tempfile
import unittest
from pathlib import Path
from ornament_library import build, catalog, RECIPES


class OrnamentTests(unittest.TestCase):
    def test_local_proposals_are_not_claimed_as_web_results(self):
        data = catalog()
        self.assertEqual(len(data['elements']), 12)
        self.assertEqual(len({item['id'] for item in data['elements']}), 12)
        self.assertFalse(data['web_planning_received'])
        self.assertFalse(data['image_generation_completed'])
        self.assertEqual(len(data['sample_ids']), 3)

    def test_default_three_independent_jobs_keep_prepared_status(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'jobs'
            result = build(out)
            self.assertEqual(result['prepared_jobs'], 3)
            self.assertEqual(result['actual_web_submissions'], 0)
            queue = json.loads((out / 'queue.json').read_text(encoding='utf-8'))
            for entry in queue['jobs']:
                job = json.loads((out / entry['job_dir'] / 'job.json').read_text(encoding='utf-8'))
                self.assertEqual(job['status'], 'prepared')
                self.assertIsNone(job['verified_engine'])
                self.assertTrue(job['spec']['transparent'])
                self.assertNotIn('submitted', [event['status'] for event in job['history']])
            with self.assertRaises(FileExistsError):
                build(out)

    def test_invalid_selection_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            for ids in [['unknown'], ['wing-foil','wing-foil']]:
                out = Path(directory) / 'invalid'
                with self.assertRaises(ValueError):
                    build(out, ids)
                self.assertFalse(out.exists())

    def test_recipe_boxes_keep_identity_and_footer_clear(self):
        for recipe in RECIPES.values():
            x,y,w,h = recipe['box_inches']
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, .1 * 7.5)
            self.assertLessEqual(x+w, 13.333)
            self.assertLessEqual(y+h, .925 * 7.5)
            self.assertTrue(recipe['source'])


if __name__ == '__main__':
    unittest.main()
