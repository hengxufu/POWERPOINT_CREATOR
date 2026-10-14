"""Synthetic offline material-transfer tests; never evidence of a real web exchange."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from material_handoff import prepare, record, check, write, load


def fixture_bundle(root, bundle, target='gpt', task_id='gpt-planning', route='builtin_browser',
                   url='https://chatgpt.com/c/test-fixture', transferred=True, prompt_file=None):
    root, bundle = Path(root).resolve(), Path(bundle).resolve()
    source = root/'synthetic-material.txt'
    source.write_text('SYNTHETIC CONTENT: one blue concept icon. No research claim.', encoding='utf-8')
    selection = root/'synthetic-selection.json'
    write(selection, {'schema': 'web_material_selection_v1', 'coverage': {'gpt': 'Synthetic brief only', 'image': 'Synthetic appearance only'},
                      'missing': [], 'materials': [{'id': 'brief', 'path': source.name, 'targets': ['gpt', 'image'],
                                                  'purpose': 'Test context', 'locator': 'Synthetic fixture full text', 'mode': 'inline'}]})
    bundle.parent.mkdir(parents=True, exist_ok=True)
    prompt = Path(prompt_file) if prompt_file else bundle.parent/(bundle.name+'-prompt.txt')
    if not prompt.exists():
        prompt.write_text('SYNTHETIC TASK ONLY', encoding='utf-8')
    prepare(root, selection, target, prompt, bundle, task_id)
    observation = {'route': route, 'session_url': url, 'message_visible': True, 'note': 'SYNTHETIC OBSERVATION ONLY',
                   'materials': [{'id': 'brief', 'mode': 'inline', 'visible_note': 'Synthetic visible inline text'}],
                   'evidence_file': str(source.relative_to(root))}
    observation_path = bundle/'synthetic-observation.json'
    write(observation_path, observation)
    if transferred:
        record(bundle, observation_path)
    return bundle, observation_path


class MaterialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_both_routes_require_actual_transfer_record(self):
        for route in ('builtin_browser', 'playwright_cli'):
            bundle, observation = fixture_bundle(self.root, self.root/route, route=route, transferred=False)
            self.assertTrue(check(bundle, require_transfer=False)['ready'])
            self.assertFalse(check(bundle)['ready'])
            self.assertIn('SYNTHETIC CONTENT:', (bundle/'message.txt').read_text(encoding='utf-8'))
            record(bundle, observation)
            self.assertTrue(check(bundle)['ready'])

    def test_wrong_conversation_target_task_or_root_rejected(self):
        bundle, _ = fixture_bundle(self.root, self.root/'bundle')
        for arguments in ({'target': 'image'}, {'session_url': 'https://chatgpt.com/c/another'},
                          {'task_id': 'another-task'}, {'project_root': self.root/'another'}):
            self.assertFalse(check(bundle, **arguments)['ready'])

    def test_changed_source_message_prompt_selection_or_evidence_rejected(self):
        for name in ('source', 'message', 'prompt', 'selection', 'evidence', 'copy'):
            root = self.root/name
            root.mkdir()
            bundle, _ = fixture_bundle(root, root/'bundle')
            path = {'source': root/'synthetic-material.txt', 'message': bundle/'message.txt',
                    'prompt': root/'bundle-prompt.txt', 'selection': root/'synthetic-selection.json',
                    'evidence': bundle/'transfer-evidence.bin', 'copy': bundle/'files/brief.txt'}[name]
            path.write_text('CHANGED SYNTHETIC CONTENT', encoding='utf-8')
            self.assertFalse(check(bundle)['ready'], name)

    def test_missing_image_materials_blocks_gpt_packet(self):
        _, _ = fixture_bundle(self.root, self.root/'seed', transferred=False)
        selection_path = self.root/'synthetic-selection.json'
        selection = load(selection_path)
        selection['materials'][0]['targets'] = ['gpt']
        write(selection_path, selection)
        with self.assertRaisesRegex(ValueError, 'required for image'):
            prepare(self.root, selection_path, 'gpt', self.root/'seed-prompt.txt', self.root/'new', 'gpt-planning')
        self.assertFalse((self.root/'new').exists())

    def test_path_only_and_incomplete_observation_rejected(self):
        bundle, observation_file = fixture_bundle(self.root, self.root/'bundle', transferred=False)
        observation = load(observation_file)
        for changes in ({'materials': []}, {'message_visible': False}, {'route': 'unknown'},
                        {'materials': [{'id': 'brief', 'mode': 'attachment', 'visible_note': 'Wrong mode'}]}):
            write(observation_file, {**observation, **changes})
            with self.assertRaises(ValueError): record(bundle, observation_file)
        selection_path = self.root/'synthetic-selection.json'
        selection = load(selection_path)
        selection['materials'][0]['mode'] = 'local_path'
        write(selection_path, selection)
        with self.assertRaisesRegex(ValueError, 'local paths'):
            prepare(self.root, selection_path, 'gpt', self.root/'bundle-prompt.txt', self.root/'new', 'gpt-planning')

    def test_attachment_requires_separate_visible_confirmation(self):
        bundle, observation_file = fixture_bundle(self.root, self.root/'seed', transferred=False)
        selection_path = self.root/'synthetic-selection.json'
        selection = load(selection_path)
        from PIL import Image
        Image.new('RGB', (20, 20), 'blue').save(self.root/'reference.png')
        selection['materials'].append({'id': 'reference', 'path': 'reference.png', 'targets': ['image'],
                                       'purpose': 'Synthetic color reference', 'locator': 'Whole image', 'mode': 'attachment'})
        write(selection_path, selection)
        bundle = self.root/'image'
        prepare(self.root, selection_path, 'image', self.root/'seed-prompt.txt', bundle, 'icon')
        with self.assertRaisesRegex(ValueError, 'every necessary material'):
            record(bundle, observation_file)
        observation = load(observation_file)
        observation['materials'].append({'id': 'reference', 'mode': 'attachment', 'visible_note': 'Synthetic sent attachment chip'})
        write(observation_file, observation)
        record(bundle, observation_file)
        self.assertTrue(check(bundle, target='image')['ready'])
        self.assertTrue((bundle/'files/reference.png').is_file())

    def test_no_overwrite_or_root_escape(self):
        bundle, observation = fixture_bundle(self.root, self.root/'bundle')
        with self.assertRaises(FileExistsError): record(bundle, observation)
        with self.assertRaises(ValueError):
            prepare(self.root, self.root/'synthetic-selection.json', 'gpt', self.root/'bundle-prompt.txt', self.root.parent/'escape', 'gpt-planning')

    def test_image_submission_requires_matching_transferred_materials(self):
        from asset_job import prepare as prepare_job, event, read
        spec = self.root/'spec.json'
        write(spec, {'asset_id': 'icon', 'kind': 'icon', 'element': 'Synthetic icon', 'slide_id': 's1', 'object_id': 'icon'})
        job = self.root/'job'
        prepare_job(SimpleNamespace(spec=spec, job=job))
        args = SimpleNamespace(job=job, status='submitted', session_url='https://chatgpt.com/c/test-fixture', engine='unverified', note='SYNTHETIC')
        with self.assertRaisesRegex(ValueError, 'Image materials'): event(args)
        self.assertEqual(read(job)['status'], 'prepared')
        fixture_bundle(self.root, job/'materials', target='image', task_id='icon', prompt_file=job/'prompt.txt')
        event(args)
        self.assertEqual(read(job)['status'], 'submitted')
        with self.assertRaisesRegex(ValueError, 'already recorded'): event(args)

    def test_unrelated_prompt_and_partial_gpt_context_rejected(self):
        bundle, _ = fixture_bundle(self.root, self.root/'bundle')
        other_prompt = self.root/'unrelated.txt'
        other_prompt.write_text('OTHER SYNTHETIC TASK', encoding='utf-8')
        self.assertFalse(check(bundle, prompt_file=other_prompt)['ready'])
        selection_path = self.root/'synthetic-selection.json'
        selection = load(selection_path)
        selection['materials'].append({**selection['materials'][0], 'id': 'evidence'})
        write(selection_path, selection)
        with self.assertRaisesRegex(ValueError, 'every selected'):
            prepare(self.root, selection_path, 'gpt', other_prompt, self.root/'new', 'gpt-planning', ['brief'])

    def test_jobs_propagate_image_context_and_reject_missing_references(self):
        from plan_workflow import jobs
        fixture_bundle(self.root, self.root/'seed', transferred=False)
        plan_path = self.root/'plan.json'
        plan = {'slides': [{'slide_number': 1, 'slide_id': 's1', 'asset_requests': [
            {'request_id': 'icon', 'object_id': 'icon', 'kind': 'icon', 'single_subject_prompt': 'Synthetic device', 'material_ids': ['brief']}]}]}
        write(plan_path, plan)
        args = SimpleNamespace(plan=plan_path, profile='research', out=self.root/'queue',
                               materials=self.root/'synthetic-selection.json', project_root=self.root)
        jobs(args)
        bundle = args.out/'icon/materials'
        self.assertIn('SYNTHETIC CONTENT:', (bundle/'message.txt').read_text(encoding='utf-8'))
        self.assertTrue(check(bundle, require_transfer=False, target='image', task_id='icon', prompt_file=args.out/'icon/prompt.txt')['ready'])
        plan['slides'][0]['asset_requests'][0]['material_ids'] = ['missing-reference']
        write(plan_path, plan)
        args.out = self.root/'invalid-queue'
        with self.assertRaisesRegex(ValueError, 'Selected material IDs'): jobs(args)
        self.assertFalse(args.out.exists())


if __name__ == '__main__':
    unittest.main()
