"""Inspect native PPTX objects. Structural evidence only, not visual/science QA."""
import argparse
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}

def audit(path):
    slides = []
    with zipfile.ZipFile(path) as z:
        parts = z.namelist()
        size = ET.fromstring(z.read('ppt/presentation.xml')).find('p:sldSz', NS)
        canvas = int(size.get('cx')) * int(size.get('cy'))
        names = sorted((n for n in parts if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)),
                       key=lambda n: int(re.search(r'(\d+)\.xml', n).group(1)))
        for name in names:
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
            slides.append({'part': name, 'native_text_runs': len(text),
                           'native_shapes': len(root.findall('.//p:sp', NS)),
                           'native_tables': len(root.findall('.//a:tbl', NS)),
                           'native_chart_refs': len(root.findall('.//c:chart', NS)),
                           'pictures': len(pictures), 'object_names': ids, 'warnings': warnings})
        return {'scope': 'structural_only', 'slides': slides,
                'chart_parts': sum(bool(re.fullmatch(r'ppt/charts/chart\d+\.xml', n)) for n in parts),
                'embedded_workbooks': sum(n.startswith('ppt/embeddings/') and n.endswith('.xlsx') for n in parts),
                'limitations': ['不判断内容真实性、字体替换、视觉美观、文字溢出或图表数据语义',
                                'slideN 为部件编号；重排后的显示顺序须由制作引擎映射',
                                '组对象变换和图片背景不纳入大图面积检测；警告须人工复核']}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pptx')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    Path(args.out).write_text(json.dumps(audit(args.pptx), ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.out)
