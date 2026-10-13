"""Offline contract tests; generated data are explicit synthetic fixtures, not research."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from experimental_figures import prepare, run, validate, TOOLS


def spec():
    return {'figure_id':'synthetic-test','backend':'python','plot_type':'paired',
        'scientific_question':'SYNTHETIC TEST ONLY','bounded_claim':'No scientific claim',
        'evidence_role':'adapter verification','source_ref':'synthetic fixture',
        'unit':'arbitrary test unit','independent_unit':'synthetic ID',
        'n_definition':'3 synthetic paired IDs','uncertainty_definition':'Raw values, boxplot summary, no inferred tests',
        'mapping':{'id-col':'id','condition-col':'condition','value-col':'value'},
        'options':{'condition-order':'Before,After','value-label':'Synthetic value'}, 'size_inches':[8,4.8]}


class FigureTests(unittest.TestCase):
    def fixture(self, root):
        source = root/'input.csv'
        source.write_text('id,condition,value\n1,Before,1\n1,After,2\n2,Before,2\n2,After,4\n3,Before,3\n3,After,5\n',encoding='utf-8')
        contract = root/'spec.json'
        contract.write_text(json.dumps(spec()),encoding='utf-8')
        return contract,source

    def test_missing_mapping_and_reporting_refused(self):
        headers = ['id','condition','value']
        for key in ('unit','n_definition','independent_unit','uncertainty_definition'):
            value = spec(); value.pop(key)
            with self.assertRaises(ValueError): validate(value,headers)
        value = spec(); value['mapping']['value-col'] = 'absent'
        with self.assertRaises(ValueError): validate(value,headers)

    def test_no_injected_flags_exclusions_or_backend_fallback(self):
        for key,value in [('backend','r'),('exclusions','drop inconvenient rows'),('size_inches',[float('nan'),5])]:
            data = spec(); data[key] = value
            with self.assertRaises(ValueError): validate(data,['id','condition','value'])
        data = spec(); data['options']['demo'] = 'true'
        with self.assertRaises(ValueError): validate(data,['id','condition','value'])

    def test_five_explicit_template_contracts(self):
        from experimental_figures import REQUIRED
        for kind,keys in REQUIRED.items():
            data = spec(); data.update(plot_type=kind,options={},mapping={k:k for k in keys})
            validate(data,list(data['mapping'].values()))

    def test_snapshot_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); contract,source = self.fixture(root)
            tools = root/'nature/scripts'; tools.mkdir(parents=True)
            for name in TOOLS: (tools/name).write_text('# synthetic source fixture\n    output = normalize_prefix(output)\n    paths = {\n',encoding='utf-8')
            out = root/'bundle'; record = prepare(contract,source,tools.parent,out)
            self.assertEqual(record['source_rows'],6)
            self.assertEqual(record['state'],'prepared_not_rendered')
            self.assertEqual((out/'source-data.csv').read_bytes(),source.read_bytes())
            self.assertEqual(record['visual_review'],'not_performed')
            with self.assertRaises(FileExistsError): prepare(contract,source,tools.parent,out)
            (out/'source-data.csv').write_text('tampered',encoding='utf-8')
            with self.assertRaises(ValueError): run(out)

    @unittest.skipUnless(os.environ.get('NATURE_FIGURE_TEST_ROOT'), 'Set local Nature root for explicit offline rendering integration test')
    def test_actual_nature_render_and_qa_are_never_visual_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); contract,source = self.fixture(root)
            out = root/'bundle'; prepare(contract,source,Path(os.environ['NATURE_FIGURE_TEST_ROOT']),out)
            result = run(out)
            self.assertEqual(result['qa']['render']['exit_code'],0,(out/'render.log').read_text(encoding='utf-8'))
            for name in ('figure.pdf','figure.svg','figure.tiff','figure.png','figure.alignment.json','figure.qa.json'):
                self.assertIn(name,result['exports'])
            qa = json.loads((out/'figure.qa.json').read_text(encoding='utf-8'))
            self.assertFalse(qa['demo'])
            self.assertEqual(qa['rows_input'],6)
            self.assertEqual(result['visual_review'],'not_performed')
            self.assertIn(result['state'],('blocked_qa','rendered_requires_visual_review'))
            print('Synthetic paired figure QA:', json.dumps({name:q['exit_code'] for name,q in result['qa'].items()}))
            with self.assertRaises(ValueError): run(out)

    @unittest.skipUnless(os.environ.get('NATURE_FIGURE_TEST_ROOT'), 'Explicit local Nature integration tests only')
    def test_other_real_csv_templates_keep_data_and_honest_blockers(self):
        cases = {
            'roc': ('fpr,A,B\n0,0,0\n0.2,0.6,0.4\n0.7,0.9,0.8\n1,1,1\n',{'fpr-col':'fpr','tpr-cols':'A,B'},{}),
            'volcano': ('gene,effect,p\na,-2,0.01\nb,0.1,0.8\nc,2,0.02\n',{'gene-col':'gene','effect-col':'effect','p-col':'p'},{'top-labels':0}),
            'dotplot': ('row,col,size,color\na,x,10,1\na,y,20,2\nb,x,30,3\nb,y,40,4\n',{'row-col':'row','column-col':'col','size-col':'size','color-col':'color'},{}),
            'marginal': ('x,y,group\n1,2,A\n2,3,A\n3,2,B\n4,5,B\n',{'x-col':'x','y-col':'y','group-col':'group'},{'bins':4})}
        for kind,(csv_text,mapping,options) in cases.items():
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); data = spec(); data.update(plot_type=kind,mapping=mapping,options=options)
                (root/'spec.json').write_text(json.dumps(data),encoding='utf-8')
                (root/'data.csv').write_text(csv_text,encoding='utf-8')
                prepare(root/'spec.json',root/'data.csv',Path(os.environ['NATURE_FIGURE_TEST_ROOT']),root/'bundle')
                result = run(root/'bundle')
                print('Synthetic '+kind+' QA:',json.dumps({name:q['exit_code'] for name,q in result['qa'].items()}))
                self.assertEqual(result['visual_review'],'not_performed')
                if result['qa']['render']['exit_code'] == 0:
                    self.assertIn('figure.pdf',result['exports'])
                    qa = json.loads((root/'bundle/figure.qa.json').read_text(encoding='utf-8'))
                    self.assertFalse(qa['demo'])
                    self.assertEqual(qa['excluded_rows'],0)
                else:
                    self.assertEqual(result['state'],'blocked_qa')
                    self.assertTrue((root/'bundle/figure.alignment.json').is_file(),(root/'bundle/render.log').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
