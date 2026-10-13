"""Snapshot local Nature plotting tools, run CSV figures and retain honest QA state."""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

FIELDS = {
    'roc': ['fpr-col', 'tpr-cols'],
    'paired': ['id-col', 'condition-col', 'value-col', 'condition-order', 'value-label'],
    'volcano': ['gene-col', 'effect-col', 'p-col', 'effect-label', 'p-threshold', 'effect-threshold', 'top-labels'],
    'dotplot': ['row-col', 'column-col', 'size-col', 'color-col', 'row-order', 'column-order', 'size-label', 'color-label'],
    'marginal': ['x-col', 'y-col', 'group-col', 'group-order', 'x-label', 'y-label', 'bins'],
}
REQUIRED = {'roc':['fpr-col','tpr-cols'], 'paired':['id-col','condition-col','value-col'],
            'volcano':['gene-col','effect-col','p-col'], 'dotplot':['row-col','column-col','size-col','color-col'],
            'marginal':['x-col','y-col']}
TOOLS = ['plot_templates.py','audit_panel_alignment.py','validate_figure.py','audit_pdf_text.py','audit_figure_collisions.py']
FIGURE_BRIEF = '''实验数据图必须另列data_figures，不放进generate_web的asset_requests。
每图写figure_id、scientific_question、bounded_claim、evidence_role、source_ref、字段映射、单位、独立实验单位、n定义、配对关系、中心/误差含义、转换/排除规则、目标摆放尺寸。
常规图优先native_data原生chart/table；复杂分布、配对、ROC、火山、矩阵气泡或边际图用nature-figure本地数据绘图，保留CSV、绘图源和SVG/PDF及QA，不使用图像模型画数据。
按科学问题选图，不按美观猜列；原始观测/汇总数据必须区分，SD/SEM/CI不可互换，不猜p值或显著性；缺材料写AUTHOR_INPUT_NEEDED。
PPT图按实际摆放尺寸检查字号和有效分辨率；不要照搬期刊5–7pt。每次修订重跑源、面板对齐、PDF文字和碰撞检查，再实际查看各panel与整页。图形内文字可在SVG/PDF编辑不等于PPT原生对象。
非原生数据图独立入稿，标题、解读与来源继续原生；一张数据图按一个图片对象计，不能拆子图凑40。'''


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def find_nature_root(explicit=None):
    candidates = [Path(explicit)] if explicit else []
    if not explicit:
        if os.environ.get('NATURE_FIGURE_SKILL'):
            candidates.append(Path(os.environ['NATURE_FIGURE_SKILL']))
        candidates.append(Path.home()/'.codex/skills/nature-figure')
        candidates.extend(parent/'nature-figure' for parent in Path(__file__).resolve().parents if parent.name=='skills')
    for path in candidates:
        if all((path/'scripts'/name).is_file() for name in TOOLS):
            return path
    raise FileNotFoundError('Local nature-figure unavailable; provide --nature-skill or use the native chart route')


def validate(spec, headers):
    for key in ('figure_id','scientific_question','bounded_claim','evidence_role','source_ref','unit','independent_unit','n_definition','uncertainty_definition'):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ValueError('Required figure contract field: '+key)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', spec['figure_id']):
        raise ValueError('Filename-safe figure_id required')
    if spec.get('backend') != 'python':
        raise ValueError('This adapter supports the established Python track only; use nature-figure R route for R, never cross-render')
    kind = spec.get('plot_type')
    if kind not in FIELDS:
        raise ValueError('Supported CSV template: '+', '.join(FIELDS))
    mapping = spec.get('mapping', {})
    options = spec.get('options', {})
    if not isinstance(mapping, dict) or not isinstance(options, dict) or set(mapping) & set(options):
        raise ValueError('Separate mapping and options objects required')
    values = {**mapping, **options}
    if set(values) - set(FIELDS[kind]) or any(key not in mapping for key in REQUIRED[kind]):
        raise ValueError('Explicit required fields and allowlisted template options only; no arbitrary CLI flags')
    for key in REQUIRED[kind] + [k for k in mapping if k.endswith('-col')]:
        columns = str(mapping[key]).split(',') if key == 'tpr-cols' else [mapping[key]]
        if any(not isinstance(column,str) or column not in headers for column in columns):
            raise ValueError('Mapped column missing from CSV: '+key)
    if spec.get('exclusions') not in (None, [], 'none'):
        raise ValueError('No automatic exclusion in this adapter; use an explicitly reviewed custom Nature source for filtering')
    dimensions = spec.get('size_inches', [8, 4.8])
    if not isinstance(dimensions,list) or len(dimensions) != 2 or not all(type(v) in (int,float) and math.isfinite(v) and 1 <= v <= 20 for v in dimensions):
        raise ValueError('size_inches must contain two finite dimensions in 1..20')
    for value in values.values():
        if not isinstance(value,(str,int,float)) or isinstance(value,bool) or isinstance(value,float) and not math.isfinite(value):
            raise ValueError('Template values must be finite scalar values')
    return values


def prepare(spec_path, csv_path, nature_root, out):
    nature_root = find_nature_root(nature_root)
    spec_path, csv_path, out = map(Path, (spec_path,csv_path,out))
    spec = json.loads(spec_path.read_text(encoding='utf-8-sig'))
    with csv_path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        rows = sum(1 for _ in reader)
    if not headers or len(headers) != len(set(headers)) or not rows:
        raise ValueError('Nonempty CSV with unique headers required')
    values = validate(spec, headers)
    if out.exists():
        raise FileExistsError('Use a new figure bundle version')
    for name in TOOLS:
        if not (nature_root/'scripts'/name).is_file():
            raise FileNotFoundError('Local Nature plotting/QA component unavailable: '+name)
    upstream_source = (nature_root/'scripts/plot_templates.py').read_text(encoding='utf-8')
    hook = '    output = normalize_prefix(output)\n    paths = {'
    if upstream_source.count(hook) != 1:
        raise ValueError('Nature export implementation changed; review adapter before rendering')
    adapted_source = upstream_source.replace(hook,
        '    output = normalize_prefix(output)\n'
        '    # PPT integration: measure final axes before any export.\n'
        '    from audit_panel_alignment import require_matplotlib_panel_alignment\n'
        '    fig.canvas.draw()\n'
        '    require_matplotlib_panel_alignment(fig, json_out="figure.alignment.json",\n'
        '        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,\n'
        '        exclude_axes=[ax for ax in fig.axes if ax.get_label() == "<colorbar>"])\n'
        '    paths = {')
    out.mkdir(parents=True)
    (out/'tools').mkdir()
    shutil.copyfile(csv_path, out/'source-data.csv')
    write(out/'figure-spec.json', spec)
    for name in TOOLS:
        shutil.copyfile(nature_root/'scripts'/name, out/'tools'/name)
    shutil.copyfile(nature_root/'scripts/plot_templates.py', out/'tools/plot_templates.upstream.py')
    (out/'tools/plot_templates.py').write_text(adapted_source,encoding='utf-8')
    shutil.copyfile(Path(__file__).with_name('nature_plot_runner.py'), out/'rebuild.py')
    width,height = spec.get('size_inches',[8,4.8])
    arguments = [spec['plot_type'],'--input','source-data.csv','--output','figure',
                 '--width-mm',str(width*25.4),'--height-mm',str(height*25.4)]
    for key,value in values.items():
        arguments.extend(['--'+key,str(value)])
    write(out/'plot-arguments.json', arguments)
    tracked = ['source-data.csv','figure-spec.json','rebuild.py','plot-arguments.json','tools/plot_templates.upstream.py'] + ['tools/'+name for name in TOOLS]
    record = {'schema':'experimental_figure_bundle_v1','figure_id':spec['figure_id'],'backend':'python',
              'state':'prepared_not_rendered','source_rows':rows,'exclusions':[],
              'files':{name:digest(out/name) for name in tracked}, 'qa':{},
              'visual_review':'not_performed','ppt_editability':'image_not_native_chart',
              'upstream':'Local nature-figure tools; original source notices retained; no journal compliance claim'}
    write(out/'figure-bundle.json', record)
    return record


def run(bundle):
    bundle = Path(bundle).resolve()
    record = json.loads((bundle/'figure-bundle.json').read_text(encoding='utf-8'))
    if record['state'] != 'prepared_not_rendered':
        raise ValueError('Already attempted; preserve reports and prepare a new version')
    for name, expected in record['files'].items():
        target = (bundle/name).resolve()
        if bundle not in target.parents or digest(target) != expected:
            raise ValueError('Bundle input/source changed; prepare a new version')
    record['state'] = 'running'
    write(bundle/'figure-bundle.json', record)
    stages = [
        ('source',[sys.executable,'tools/validate_figure.py','tools/plot_templates.py','--json']),
        ('render',[sys.executable,'rebuild.py']),
        ('pdf_text',[sys.executable,'tools/audit_pdf_text.py','figure.pdf','--min-pt','12','--json']),
        ('collisions',[sys.executable,'tools/audit_figure_collisions.py','figure.pdf','--json-out','figure.collisions.json','--overlay-pdf','figure.collisions.pdf','--strict'])]
    for name,command in stages:
        result = subprocess.run(command,cwd=bundle,capture_output=True,text=True,encoding='utf-8',errors='replace')
        # Logs stay local; no credentials or web calls are involved.
        (bundle/(name+'.log')).write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        record['qa'][name] = {'exit_code':result.returncode,'log':name+'.log'}
        if name == 'render' and result.returncode:
            break
    exports = [name for name in ('figure.svg','figure.pdf','figure.tiff','figure.png','figure.alignment.json','figure.qa.json','figure.collisions.json') if (bundle/name).is_file()]
    record['exports'] = {name:digest(bundle/name) for name in exports}
    all_ok = len(record['qa']) == len(stages) and all(q['exit_code']==0 for q in record['qa'].values())
    record['state'] = 'rendered_requires_visual_review' if all_ok else 'blocked_qa'
    record['visual_review'] = 'not_performed'
    write(bundle/'figure-bundle.json',record)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    p = commands.add_parser('prepare')
    for field in ('spec','csv','out'):
        p.add_argument('--'+field,required=True,type=Path)
    p.add_argument('--nature-skill',type=Path)
    p = commands.add_parser('run')
    p.add_argument('--bundle',required=True,type=Path)
    args = parser.parse_args()
    result = prepare(args.spec,args.csv,args.nature_skill,args.out) if args.command=='prepare' else run(args.bundle)
    print(json.dumps({'figure_id':result['figure_id'],'state':result['state'],'visual_review':result['visual_review']},ensure_ascii=False))
    raise SystemExit(1 if result['state']=='blocked_qa' else 0)
