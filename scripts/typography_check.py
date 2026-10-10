"""Audit or normalize editable DrawingML fonts without round-tripping the deck.

Coverage requires explicit declarations on visible text runs, including chart text.
MathML/OMML and bitmap lettering are outside the normal-text font policy.
"""
import argparse
import json
import re
import zipfile
from pathlib import Path
from lxml import etree as E

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS = {'a': A}
POLICY = {'latin': 'Times New Roman', 'ea': 'Microsoft YaHei', 'cs': 'Times New Roman'}


def relevant(name):
    return name.endswith('.xml') and name.startswith((
        'ppt/slides/', 'ppt/theme/', 'ppt/slideMasters/', 'ppt/slideLayouts/',
        'ppt/charts/', 'ppt/notesSlides/', 'ppt/notesMasters/'))


def parse(data):
    return E.fromstring(data, E.XMLParser(resolve_entities=False, no_network=True))


def text_runs(root):
    for node in root.iter():
        if node.tag not in (f'{{{A}}}r', f'{{{A}}}fld'):
            continue
        if any(parent.tag.startswith(f'{{{M}}}') for parent in node.iterancestors()):
            continue
        text = ''.join(node.xpath('./a:t/text()', namespaces=NS))
        if text.strip():
            yield node, text


def audit(path):
    mismatches, missing = [], []
    counts = dict(latin=0, east_asian=0, office_equations=0,
                  latex_compatibility_pictures=0, text_runs=0)
    parts = 0
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not relevant(name):
                continue
            root = parse(archive.read(name))
            parts += 1
            for tag, allowed, label in (
                ('latin', {'Times New Roman'}, 'latin'),
                ('ea', {'Microsoft YaHei', '微软雅黑'}, 'east_asian')):
                for element in root.iter(f'{{{A}}}{tag}'):
                    if any(parent.tag.startswith(f'{{{M}}}') for parent in element.iterancestors()):
                        continue
                    counts[label] += 1
                    if element.get('typeface') not in allowed:
                        mismatches.append(dict(part=name, script=label, typeface=element.get('typeface')))
            for run, text in text_runs(root):
                counts['text_runs'] += 1
                # Demand only scripts actually present; normalization writes all three.
                scripts = []
                if re.search(r'[\u2e80-\u9fff\uf900-\ufaff\U00020000-\U0003134f]', text):
                    scripts.append('ea')
                if re.search(r'[A-Za-z0-9\u00c0-\u024f]', text):
                    scripts.append('latin')
                for script in scripts:
                    face = run.find(f'{{{A}}}rPr/{{{A}}}{script}')
                    if face is None or not face.get('typeface'):
                        missing.append(dict(part=name, script=script, text=text[:80]))
            counts['office_equations'] += len(list(root.iter(f'{{{M}}}oMath')))
            counts['latex_compatibility_pictures'] += sum(
                element.get('name', '').startswith('LaTeX-fallback-')
                for element in root.iter(f'{{{P}}}cNvPr'))
    return dict(font_policy={'chinese': 'Microsoft YaHei / 微软雅黑', 'western': 'Times New Roman'},
                counts=counts, mismatches=mismatches, missing_run_fonts=missing,
                passed_explicit_font_check=not mismatches and not missing,
                parts_checked=parts,
                limits=['Inherited fonts are flagged for explicit normalization, not declared visually incorrect.',
                        'Chart auto-generated labels can inherit chart/theme defaults; rendering is still required.',
                        'Bitmap lettering, installed fonts and scientific correctness are not verified.',
                        'OMML is counted structurally; inspect equations in the target PowerPoint version.'])


def normalize(source, output):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Use a new output path; in-place writes and overwrites are refused.')
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(output, 'x') as target:
        for info in archive.infolist():
            data = archive.read(info.filename)
            if relevant(info.filename):
                root = parse(data)
                # Leave Office equation descendants alone, including DrawingML fallbacks inside math.
                for element in list(root.iter()):
                    if any(parent.tag.startswith(f'{{{M}}}') for parent in element.iterancestors()):
                        continue
                    if element.tag in [f'{{{A}}}{key}' for key in POLICY]:
                        element.set('typeface', POLICY[E.QName(element).localname])
                    if element.tag == f'{{{A}}}font' and element.get('script') in ('Hans', 'Hant'):
                        element.set('typeface', POLICY['ea'])
                    if element.tag in (f'{{{A}}}rPr', f'{{{A}}}defRPr', f'{{{A}}}endParaRPr'):
                        set_fonts(element)
                for run, _ in text_runs(root):
                    properties = run.find(f'{{{A}}}rPr')
                    if properties is None:
                        properties = E.Element(f'{{{A}}}rPr')
                        run.insert(0, properties)
                    set_fonts(properties)
                data = E.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
            target.writestr(info, data)


def set_fonts(properties):
    # CT_TextCharacterProperties orders latin/ea/cs before sym/hlink/extLst.
    before = {f'{{{A}}}{tag}' for tag in ('sym', 'hlinkClick', 'hlinkMouseOver', 'rtl', 'extLst')}
    for key, value in POLICY.items():
        existing = properties.find(f'{{{A}}}{key}')
        if existing is not None:
            properties.remove(existing)
    insertion = next((i for i, child in enumerate(properties) if child.tag in before), len(properties))
    for offset, (key, value) in enumerate(POLICY.items()):
        element = E.Element(f'{{{A}}}{key}', typeface=value)
        properties.insert(insertion + offset, element)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx')
    parser.add_argument('--out', required=True, help='JSON audit report')
    parser.add_argument('--normalize-to', help='New PPTX with explicit fonts; original is preserved')
    args = parser.parse_args()
    if args.normalize_to:
        normalize(args.pptx, args.normalize_to)
    result = audit(args.normalize_to or args.pptx)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))
    raise SystemExit(0 if result['passed_explicit_font_check'] else 1)
