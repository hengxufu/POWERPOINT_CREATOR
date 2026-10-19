"""Prepare a board from real renders and verify explicitly recorded visual reviews.

Never renders a deck, judges pixels, or fills a passing review automatically.
"""
import argparse
import base64
import hashlib
import html
import json
import shutil
from pathlib import Path

from art_direction import representatives
from material_handoff import inside, digest, load, write

CRITERIA = {
    'focus': '主焦点与结论是否清晰，装饰是否抢夺注意力',
    'hierarchy': '标题论点、主证据、解释和来源的大小层次；正文是否保留关键限定而非堆入整段讲稿',
    'spacing': '外边距、对齐、组内/组间距离及真实换行；孤行、文本溢出与图注是否贴近对应证据',
    'color': '真实背景下的色彩一致性、对比与投影可读性',
    'assets': '素材光照、材质、视角与光学大小；真实背景上的白边/暗边、阴影截断、接触位置及原生线宽一致性',
    'evidence': '图表、公式、坐标、图例、误差、单位和引用可读性'
}


def selection(plan, phase):
    if phase not in ('representative', 'full'):
        raise ValueError('Phase must be representative or full')
    ids = set(representatives(plan).values()) if phase == 'representative' else {s['slide_id'] for s in plan['slides']}
    return [s for s in plan['slides'] if s['slide_id'] in ids]


def signature(plan, phase):
    value = {'design_system': plan.get('design_system', {}), 'slides': selection(plan, phase)}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def prepare(workspace, pptx, render_index, phase='representative'):
    workspace = Path(workspace).resolve()
    pptx, render_index = inside(workspace, pptx), inside(workspace, render_index)
    plan_path = workspace/'planning/deck_plan.json'
    plan = load(plan_path)
    selected = selection(plan, phase)
    deck_hash = digest(pptx)
    renders = load(render_index)
    if renders.get('pptx_sha256') != deck_hash:
        raise ValueError('Render index belongs to another PPTX revision')
    from pptx import Presentation
    if len(Presentation(pptx).slides) != len(plan['slides']):
        raise ValueError('Render source must use the canonical slide order; reserve unbuilt pages in the draft')
    by_page = {}
    for item in renders.get('slides', []):
        number = item.get('slide_number')
        if type(number) is not int or number < 1 or number > len(plan['slides']) or number in by_page:
            raise ValueError('Render index needs unique in-range slide numbers')
        by_page[number] = item
    sources = []
    from PIL import Image
    for slide in selected:
        item = by_page.get(slide['slide_number'])
        if item is None:
            raise ValueError('Missing actual render for page ' + str(slide['slide_number']))
        source = inside(workspace, item['render_file'])
        if digest(source) != item.get('render_sha256'):
            raise ValueError('Render file/hash mismatch')
        with Image.open(source) as image:
            image.verify()
            if image.format not in ('PNG','JPEG','WEBP'):
                raise ValueError('Use actual PNG/JPEG/WEBP page renders')
            suffix = {'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}[image.format]
        sources.append((slide, source, suffix))
    visual_signature = signature(plan, phase)
    render_hash = hashlib.sha256(''.join(digest(p) for _,p,_ in sources).encode()).hexdigest()
    folder = inside(workspace, 'qa/visual-reviews/' + phase + '-' + deck_hash[:12] + '-' + visual_signature[:10] + '-' + render_hash[:8])
    if not folder.exists():
        folder.mkdir(parents=True)
        shutil.copyfile(pptx, folder/'source.pptx')
        shutil.copyfile(plan_path, folder/'plan.json')
        records, cards = [], []
        for slide, source, suffix in sources:
            filename = 'slide-' + str(slide['slide_number']) + suffix
            shutil.copyfile(source, folder/filename)
            records.append({'slide_number':slide['slide_number'], 'slide_id':slide['slide_id'],
                            'render_file':filename, 'render_sha256':digest(source),
                            'status':'pending', 'note':'', 'checks':{k:False for k in CRITERIA}, 'issues':[]})
            mime = {'.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'}[suffix]
            url = 'data:' + mime + ';base64,' + base64.b64encode(source.read_bytes()).decode('ascii')
            cards.append('<article><h2>' + html.escape(f"{slide['slide_number']:02d} · {slide.get('title',slide['slide_id'])}") +
                         '</h2><img alt="实际页面渲染，尚待审查" src="' + url + '"><p>' +
                         html.escape(str(slide.get('takeaway',''))) + '</p></article>')
        record = {'schema':'ppt_visual_review_v1', 'phase':phase, 'pptx_sha256':deck_hash,
                  'source_file':'source.pptx', 'plan_file':'plan.json', 'plan_sha256':digest(plan_path),
                  'visual_signature':visual_signature, 'pages':records,
                  'limit':'Pending observations only. Actual visual inspection required; no aesthetic score.'}
        write(folder/'review.json', record)
        checklist = ''.join('<li>' + html.escape(v) + '</li>' for v in CRITERIA.values())
        board = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>页面视觉审查</title>
<style>body{margin:0;background:#eef2f6;color:#18283b;font:16px/1.6 "Microsoft YaHei",sans-serif}header,main{max-width:1400px;margin:auto;padding:28px}h1{margin:0}article{margin:20px 0;background:white;padding:20px;border-radius:8px}img{width:100%;height:auto;display:block}h2{font-size:20px}p{color:#44566c}li{margin:5px 0}</style>
<header><h1>实际页面 · 待视觉审查</h1><p>逐页看原尺寸，再缩到投影阅读尺度。此页面不自动通过审查；在同目录review.json记录具体观察、对象与修订。</p><ul>''' + checklist + '</ul></header><main>' + ''.join(cards) + '</main></html>'
        (folder/'board.html').write_text(board, encoding='utf-8')
    elif not all((folder/name).is_file() for name in ('source.pptx','plan.json','review.json','board.html')):
        raise ValueError('Interrupted visual preparation; inspect existing directory before recovery')
    index_path = workspace/'qa/visual-review-index.json'
    index = load(index_path) if index_path.is_file() else {}
    index[phase] = str((folder/'review.json').relative_to(workspace))
    write(index_path, index)
    ready = check(workspace,plan,phase,pptx if phase=='full' else None)['ready']
    return {'review_file':str(folder/'review.json'), 'board_file':str(folder/'board.html'), 'phase':phase,
            'ready':ready, 'next_action':'continue_workflow' if ready else 'inspect_actual_render_and_record_review'}


def check(workspace, plan, phase, pptx=None):
    workspace = Path(workspace).resolve()
    problems = []
    try:
        index = load(workspace/'qa/visual-review-index.json')
        path = inside(workspace, index[phase])
        record = load(path)
        folder = path.parent
        if record.get('schema') != 'ppt_visual_review_v1' or record.get('phase') != phase:
            raise ValueError('Wrong visual review type or phase')
        if record.get('visual_signature') != signature(plan, phase):
            raise ValueError('Visual review is stale after design or selected-page changes')
        snapshot = inside(folder, record['plan_file'])
        if digest(snapshot) != record['plan_sha256'] or signature(load(snapshot),phase) != record['visual_signature']:
            raise ValueError('Review plan snapshot changed')
        if digest(inside(folder, record['source_file'])) != record['pptx_sha256']:
            raise ValueError('Reviewed PPTX snapshot changed')
        if pptx is not None and digest(pptx) != record['pptx_sha256']:
            raise ValueError('Full visual review belongs to another final PPTX')
        expected = [(s['slide_number'],s['slide_id']) for s in selection(plan,phase)]
        pages = record.get('pages', [])
        if [(p.get('slide_number'),p.get('slide_id')) for p in pages] != expected:
            raise ValueError('Missing, duplicated or out-of-order reviewed pages')
        for page in pages:
            if digest(inside(folder,page['render_file'])) != page['render_sha256']:
                raise ValueError('Reviewed render changed')
            if page.get('status') != 'pass' or not str(page.get('note','')).strip() or page.get('issues') != [] or not all(page.get('checks',{}).get(k) is True for k in CRITERIA):
                problems.append('Page ' + str(page['slide_number']) + ': actual visual observations or fixes still required')
    except (OSError, ValueError, KeyError, TypeError) as error:
        problems.append(str(error))
    return {'ready':not problems, 'problems':problems, 'phase':phase,
            'limits':'Hash and observation completeness only; review claims must come from viewing actual renders.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--pptx', type=Path, required=True)
    parser.add_argument('--renders', type=Path, required=True)
    parser.add_argument('--phase', choices=['representative','full'], default='representative')
    args = parser.parse_args()
    print(json.dumps(prepare(args.workspace,args.pptx,args.renders,args.phase),ensure_ascii=False))


if __name__ == '__main__':
    main()
