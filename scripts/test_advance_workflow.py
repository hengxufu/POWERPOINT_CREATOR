"""Synthetic local workflow tests. No web submission or production QA evidence."""
import tempfile
import unittest
from pathlib import Path
from auto_workflow import prepare, advance, status, job_inventory, select_job, write, load
from test_visual_review import fixture, synthetic_pass
from visual_review import prepare as prepare_review


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()
        self.workspace=self.root/'workspace'
        prepare(self.root,self.workspace)
        self.plan,self.deck,self.renders=fixture(self.workspace)
        for slide in self.plan['slides']:
            n=slide['slide_number']
            slide['asset_requests']=[{'request_id':f'icon{n}','object_id':'icon','kind':'icon',
                                      'single_subject_prompt':'One synthetic test icon','role':'ornament','box_inches':[9,2,1,1]}]
        write(self.workspace/'planning/deck_plan.json',self.plan)
        source=self.workspace/'sources/context.md'
        source.write_text('SYNTHETIC ONLY. One blue concept icon. No research claims.',encoding='utf-8')
        write(self.workspace/'planning/material-selection.json',{'schema':'web_material_selection_v1',
              'coverage':{'gpt':'Synthetic brief','image':'Synthetic appearance'},'missing':[],
              'materials':[{'id':'brief','path':str(source.relative_to(self.root)),'targets':['gpt','image'],
                            'mode':'inline','purpose':'Test context','locator':'Whole synthetic fixture'}]})

    def tearDown(self):self.temp.cleanup()

    def test_advance_prepares_only_representatives_and_is_idempotent(self):
        self.plan['design_system']={'color_roles':{'primary':'#123456'},'image_defaults':{'material':'Synthetic shared matte'}}
        self.plan['slides'][1]['asset_requests'][0]['palette']='Intentional synthetic palette'
        write(self.workspace/'planning/deck_plan.json',self.plan)
        first=advance(self.workspace)
        inventory=job_inventory(self.workspace)
        self.assertEqual(set(inventory),{'icon1','icon2','icon3'})
        self.assertEqual(first['actual_web_submissions'],0)
        tasks=load(first['revision_tasks']['json'])
        self.assertEqual(tasks['plan_sha256'],first['revision_tasks']['plan_sha256'])
        self.assertTrue(Path(first['revision_tasks']['markdown']).is_file())
        self.assertEqual(next(a for a in first['asset_actions'] if a['request_id']=='icon4')['action'],'wait_for_representative_review')
        before={p:p.read_bytes() for p in (self.workspace/'asset-jobs').glob('*/*/job.json')}
        advance(self.workspace)
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        self.assertEqual(job_inventory(self.workspace),inventory)
        self.assertTrue(all(load(p)['status']=='prepared' for p in before))
        one=load(next(iter(inventory['icon1']))/'job.json')['spec']
        two=load(next(iter(inventory['icon2']))/'job.json')['spec']
        self.assertIn('#123456',one['palette'])
        self.assertEqual(one['visual_context']['material'],'Synthetic shared matte')
        self.assertEqual(two['palette'],'Intentional synthetic palette')
        board=prepare_review(self.workspace,self.deck,self.renders)
        synthetic_pass(board['review_file'])
        advanced=advance(self.workspace)
        self.assertEqual(set(job_inventory(self.workspace)),{'icon1','icon2','icon3','icon4'})
        self.assertIn('prepare_missing_full_asset_jobs',advanced['completed_local_actions'])

    def test_single_job_plan_changes_require_inspection_before_reuse(self):
        advance(self.workspace)
        directory=next(iter(job_inventory(self.workspace)['icon1']))
        old=(directory/'job.json').read_bytes()
        self.plan['slides'][0]['asset_requests'][0]['single_subject_prompt']='Changed synthetic request'
        write(self.workspace/'planning/deck_plan.json',self.plan)
        result=advance(self.workspace)
        self.assertEqual(next(a for a in result['asset_actions'] if a['request_id']=='icon1')['state'],'plan_changed')
        self.assertEqual((directory/'job.json').read_bytes(),old)
        select_job(self.workspace,'icon1',directory,'SYNTHETIC explicit reinspection: existing spec still appropriate')
        result=status(self.workspace)
        self.assertEqual(next(a for a in result['asset_actions'] if a['request_id']=='icon1')['state'],'prepared')
        self.assertEqual((directory/'job.json').read_bytes(),old)

    def test_assets_queue_and_dispatch_intent_are_recovered_without_resubmit(self):
        directory=self.workspace/'assets/web-queue-v1/icon1'
        write(directory/'job.json',{'status':'prepared','spec':{'request_id':'icon1'},'history':[]})
        write(directory/'dispatch-intent.json',{'state':'dispatch_intent','note':'SYNTHETIC interrupted send'})
        write(directory.parent/'queue.json',{'jobs':[{'request_id':'icon1','job_dir':'icon1'}]})
        result=status(self.workspace)
        item=next(a for a in result['asset_actions'] if a['request_id']=='icon1')
        self.assertEqual(item['state'],'submission_unknown')
        self.assertEqual(item['action'],'inspect_original_conversation_do_not_resubmit')
        advance(self.workspace)
        self.assertEqual(job_inventory(self.workspace)['icon1'],{directory})
        (directory.parent/'queue.json').unlink()
        self.assertEqual(job_inventory(self.workspace)['icon1'],{directory})

    def test_duplicate_jobs_do_not_get_silently_selected(self):
        for queue in ('v1','v2'):
            write(self.workspace/f'asset-jobs/{queue}/icon1/job.json',{'status':'prepared','spec':{'request_id':'icon1'}})
        result=advance(self.workspace)
        self.assertEqual(result['next_action'],'resolve_duplicate_asset_queues')
        self.assertEqual(result['actual_web_submissions'],0)
        self.assertEqual(set(job_inventory(self.workspace)),{'icon1'})

    def test_explicit_revision_choice_preserves_old_jobs_and_invalidates_on_change(self):
        first=self.workspace/'asset-jobs/v1/icon1'
        second=self.workspace/'asset-jobs/v2/icon1'
        for directory,state in ((first,'rejected'),(second,'prepared')):
            write(directory/'job.json',{'status':state,'spec':{'request_id':'icon1'}})
        old_bytes=(first/'job.json').read_bytes()
        select_job(self.workspace,'icon1',second,'SYNTHETIC revised material after rejected first result')
        result=advance(self.workspace)
        self.assertNotEqual(result['next_action'],'resolve_duplicate_asset_queues')
        self.assertEqual(next(a for a in result['asset_actions'] if a['request_id']=='icon1')['job_dir'],str(second))
        self.assertEqual((first/'job.json').read_bytes(),old_bytes)
        self.plan['slides'][0]['asset_requests'][0]['single_subject_prompt']='Changed synthetic subject'
        write(self.workspace/'planning/deck_plan.json',self.plan)
        self.assertEqual(status(self.workspace)['next_action'],'resolve_duplicate_asset_queues')

    def test_selection_cannot_hide_an_unresolved_submission(self):
        first=self.workspace/'asset-jobs/v1/icon1'
        second=self.workspace/'asset-jobs/v2/icon1'
        for directory in (first,second):
            write(directory/'job.json',{'status':'prepared','spec':{'request_id':'icon1'}})
        write(first/'dispatch-intent.json',{'note':'SYNTHETIC ambiguous send'})
        with self.assertRaisesRegex(ValueError,'original conversation'):
            select_job(self.workspace,'icon1',second,'SYNTHETIC attempt')
        self.assertFalse((self.workspace/'planning/asset-job-selection.json').exists())

    def test_missing_materials_or_bad_geometry_do_not_create_jobs(self):
        selection=self.workspace/'planning/material-selection.json'
        data=load(selection);data['missing']=['SYNTHETIC missing reference'];write(selection,data)
        result=advance(self.workspace)
        self.assertEqual(result['next_action'],'prepare_asset_materials')
        self.assertFalse(list((self.workspace/'asset-jobs').glob('*/queue.json')))
        self.plan['design_system']={'theme_profile':'beihang-blue'}
        self.plan['slides'][0]['content_blocks'][0]['box_inches']=[10.6,.2,2,.4]
        write(self.workspace/'planning/deck_plan.json',self.plan)
        result=advance(self.workspace)
        self.assertEqual(result['next_action'],'repair_plan_geometry')
        self.assertFalse(list((self.workspace/'asset-jobs').glob('*/queue.json')))

    def test_advance_with_renders_creates_pending_board_only(self):
        result=advance(self.workspace,self.deck,self.renders)
        self.assertEqual(result['visual_board']['phase'],'representative')
        self.assertFalse(result['representative_review']['ready'])
        record=load(result['visual_board']['review_file'])
        self.assertTrue(all(page['status']=='pending' for page in record['pages']))
        self.assertEqual(result['actual_web_submissions'],0)

    def test_lost_legacy_queue_uses_target_identity_and_orphan_intents_block(self):
        directory=self.workspace/'assets/legacy-v1/sensor-old-name'
        write(directory/'job.json',{'status':'submitted','spec':{'slide_id':'s1','object_id':'icon'},'history':[{'status':'submitted'}]})
        result=status(self.workspace)
        item=next(a for a in result['asset_actions'] if a['request_id']=='icon1')
        self.assertEqual(item['state'],'submitted')
        write(self.workspace/'asset-jobs/interrupted/unknown/dispatch-intent.json',{'note':'SYNTHETIC unresolved dispatch'})
        before=job_inventory(self.workspace,self.plan)
        result=advance(self.workspace)
        self.assertEqual(result['next_action'],'inspect_orphaned_dispatch')
        self.assertEqual(before,job_inventory(self.workspace,self.plan))


if __name__=='__main__':unittest.main()
