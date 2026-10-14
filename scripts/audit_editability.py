"""Inspect native PPTX objects. Structural evidence only, not visual/science QA."""
import argparse
import json
import re
import hashlib
import io
import posixpath
import zipfile
from defusedxml import ElementTree as ET
from pathlib import Path

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def relationships(z, part):
    relpart = posixpath.join(posixpath.dirname(part), '_rels', posixpath.basename(part) + '.rels')
    if relpart not in z.namelist():
        return {}
    return {node.get('Id'): node.attrib for node in ET.fromstring(z.read(relpart))}

def target_part(part, relation):
    target = relation.get('Target', '')
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))

def chart_workbook(z, slide_part, chart_ref, slide_rels):
    result = {'relationship_id': chart_ref.get('{' + NS['r'] + '}id')}
    relation = slide_rels.get(result['relationship_id'])
    if not relation or relation.get('TargetMode') == 'External':
        return dict(result, status='missing_or_external_chart')
    chart = target_part(slide_part, relation)
    result['chart_part'] = chart
    if chart not in z.namelist():
        return dict(result, status='missing_chart_part')
    external = ET.fromstring(z.read(chart)).find('c:externalData', NS)
    if external is None:
        return dict(result, status='no_workbook_reference')
    relation = relationships(z, chart).get(external.get('{' + NS['r'] + '}id'))
    if not relation or relation.get('TargetMode') == 'External':
        return dict(result, status='missing_or_external_workbook')
    workbook = target_part(chart, relation)
    result['workbook_part'] = workbook
    if workbook not in z.namelist():
        return dict(result, status='missing_workbook_part')
    try:
        with zipfile.ZipFile(io.BytesIO(z.read(workbook))) as embedded:
            valid = 'xl/workbook.xml' in embedded.namelist() and embedded.testzip() is None
            if valid:
                ET.fromstring(embedded.read('xl/workbook.xml'))
    except (zipfile.BadZipFile, ET.ParseError):
        valid = False
    return dict(result, status='embedded_workbook_present' if valid else 'invalid_workbook_package')

def audit(path):
    slides = []
    with zipfile.ZipFile(path) as z:
        parts = z.namelist()
        size = ET.fromstring(z.read('ppt/presentation.xml')).find('p:sldSz', NS)
        canvas = int(size.get('cx')) * int(size.get('cy'))
        presentation = ET.fromstring(z.read('ppt/presentation.xml'))
        rels = relationships(z, 'ppt/presentation.xml')
        names = [target_part('ppt/presentation.xml', rels[node.get('{' + NS['r'] + '}id')])
                 for node in presentation.findall('p:sldIdLst/p:sldId', NS)]
        for number, name in enumerate(names, 1):
            root = ET.fromstring(z.read(name))
            pictures = root.findall('.//p:pic', NS)
            warnings = []
            for pic in pictures:
                extent = pic.find('p:spPr/a:xfrm/a:ext', NS)
                if extent is not None and int(extent.get('cx')) * int(extent.get('cy')) > .8 * canvas:
                    warnings.append('large_picture: 人工区分原始证据图与整页截图')
            text = [t.text or '' for t in root.findall('.//a:t', NS)]
            if pictures and not any(t.strip() for t in text):
                warnings.append('picture_without_native_text: 人工检查图片页是否承载正文')
            ids = [n.get('name') for n in root.findall('.//p:cNvPr', NS) if n.get('id') != '1']
            charts = [chart_workbook(z, name, ref, relationships(z, name))
                      for ref in root.findall('.//c:chart', NS)]
            warnings.extend('chart_workbook: ' + item['status'] for item in charts
                            if item['status'] != 'embedded_workbook_present')
            slides.append({'slide_number': number, 'part': name, 'native_text_runs': len(text),
                           'native_shapes': len(root.findall('.//p:sp', NS)),
                           'native_tables': len(root.findall('.//a:tbl', NS)),
                           'native_chart_refs': len(root.findall('.//c:chart', NS)),
                           'pictures': len(pictures), 'object_names': ids, 'charts': charts, 'warnings': warnings})
        return {'scope': 'structural_only', 'pptx_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(), 'slides': slides,
                'chart_parts': sum(bool(re.fullmatch(r'ppt/charts/chart\d+\.xml', n)) for n in parts),
                'embedded_workbooks': sum(n.startswith('ppt/embeddings/') and n.endswith('.xlsx') for n in parts),
                'limitations': ['不判断内容真实性、字体替换、视觉美观、文字溢出或图表数据语义',
                                '按presentation.xml显示页序报告；工作簿存在不证明单元格与图表缓存一致或可在Office更新',
                                '组对象变换和图片背景不纳入大图面积检测；警告须人工复核']}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pptx')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if Path(args.out).resolve() == Path(args.pptx).resolve():
        parser.error('Report must not overwrite input PPTX')
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(audit(args.pptx), ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.out)
