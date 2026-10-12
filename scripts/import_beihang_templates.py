"""Package selected, unchanged assets from the user's Beihang template folder."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def ingest(source, out):
    source, out = Path(source), Path(out)
    if out.exists():
        raise FileExistsError('Use a new asset-pack directory; never overwrite an existing pack')
    selected = {
        'wordmark-blue.png': ('北京航空航天大学工作汇报ppt模板蓝(2).pptx', 'ppt/media/image3.png', 'university_identity'),
        'campus-panorama.png': ('北京航空航天大学工作汇报ppt模板蓝(2).pptx', 'ppt/media/image1.png', 'campus_photo'),
        'main-building.jpeg': ('北航PPT模板.pptx', 'ppt/media/image3.jpeg', 'campus_photo'),
    }
    # Read and validate all inputs before writing anything.
    assets, blobs, templates = {}, {}, []
    for filename, (template, part, role) in selected.items():
        original = source / template
        with zipfile.ZipFile(original) as archive:
            blob = archive.read(part)
        blobs[filename] = blob
        assets[filename] = {'file': filename, 'sha256': digest(blob), 'role': role,
                            'source_file': template, 'source_part': part,
                            'source_sha256': digest(original.read_bytes()), 'transform': 'none'}
    ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    for template in sorted(source.glob('*.pptx')):
        with zipfile.ZipFile(template) as archive:
            names = archive.namelist()
            colors = Counter()
            for name in names:
                if name.startswith(('ppt/slides/', 'ppt/theme/', 'ppt/slideMasters/')) and name.endswith('.xml'):
                    tree = ET.fromstring(archive.read(name))
                    colors.update(n.get('val') for n in tree.findall('.//a:srgbClr', ns))
            templates.append({'file': template.name, 'sha256': digest(template.read_bytes()),
                              'slide_count': sum(n.startswith('ppt/slides/slide') and n.endswith('.xml') for n in names),
                              'common_explicit_colors': colors.most_common(8)})
    manifest = {'schema': 'beihang_source_assets_v1', 'source_directory': str(source),
                'provenance_status': 'user_provided_templates_not_official_brand_standard',
                'reuse_scope': 'User-requested local presentations; no claim of public redistribution rights.',
                'assets': assets, 'templates': templates}
    out.mkdir(parents=True)
    for filename, blob in blobs.items():
        (out / filename).write_bytes(blob)
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'templates_analyzed': len(templates), 'assets_packaged': len(assets), 'out': str(out)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(ingest(args.source, args.out), ensure_ascii=False))
