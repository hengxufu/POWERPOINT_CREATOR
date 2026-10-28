"""Merge selected slides by copying complete OPC relationship graphs."""
import argparse
import copy
import json
import posixpath as pp
import zipfile
from pathlib import Path
from lxml import etree as E

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'


def xml(data):
    return E.fromstring(data, E.XMLParser(resolve_entities=False, no_network=True))


def relpath(part):
    return pp.join(pp.dirname(part), '_rels', pp.basename(part)+'.rels')


def target(part, value):
    resolved = pp.normpath(pp.join(pp.dirname(part), value)) if not value.startswith('/') else value[1:]
    if resolved.startswith('../'):
        raise ValueError('Relationship escapes package')
    return resolved


def merge(spec, output):
    output = Path(output)
    if output.exists():
        raise ValueError('Output already exists')
    entries = spec['sources']
    if not entries:
        raise ValueError('No source decks')
    with zipfile.ZipFile(entries[0]['path']) as z:
        data = {n: z.read(n) for n in z.namelist()}
    presentation = xml(data['ppt/presentation.xml'])
    relationships = xml(data['ppt/_rels/presentation.xml.rels'])
    types = xml(data['[Content_Types].xml'])
    size = tuple(presentation.find('{'+P+'}sldSz').get(k) for k in ('cx', 'cy'))
    slides = presentation.find('{'+P+'}sldIdLst')
    if slides is None:
        slides = E.SubElement(presentation, '{'+P+'}sldIdLst')
    slides.clear()
    # Source sections and custom shows reference old slide IDs/order.
    for node in list(presentation.iter()):
        if E.QName(node).localname in ('sectionLst', 'custShowLst'):
            node.getparent().remove(node)
    # Old slide parts may remain unreachable; remove their presentation links.
    for rel in list(relationships):
        if rel.get('Type', '').endswith('/slide'):
            relationships.remove(rel)
    used = {r.get('Id') for r in relationships}
    def register(part, kind):
        i = 1
        while 'rId'+str(i) in used:
            i += 1
        rid = 'rId'+str(i); used.add(rid)
        E.SubElement(relationships, '{'+REL+'}Relationship', Id=rid, Type=R+'/'+kind,
                     Target=pp.relpath(part, 'ppt'))
        return rid
    receipt = []
    for index, entry in enumerate(entries):
        with zipfile.ZipFile(entry['path']) as z:
            src = xml(z.read('ppt/presentation.xml'))
            if tuple(src.find('{'+P+'}sldSz').get(k) for k in ('cx', 'cy')) != size:
                raise ValueError('Slide sizes differ; normalize source dimensions explicitly')
            rels = {r.get('Id'): r for r in xml(z.read('ppt/_rels/presentation.xml.rels'))}
            ids = list(src.find('{'+P+'}sldIdLst'))
            numbers = entry.get('slides', list(range(1, len(ids)+1)))
            overrides = {v.get('PartName')[1:]: v.get('ContentType') for v in xml(z.read('[Content_Types].xml')) if v.tag.endswith('Override')}
            defaults = {v.get('Extension'): v.get('ContentType') for v in xml(z.read('[Content_Types].xml')) if v.tag.endswith('Default')}
            mapped = {}
            def clone(part):
                if part in mapped:
                    return mapped[part]
                if part not in z.namelist():
                    raise ValueError('Missing dependency: '+part)
                new = 'ppt/import'+str(index+1)+'/'+part
                mapped[part] = new
                data[new] = z.read(part)
                content = overrides.get(part, defaults.get(part.rsplit('.', 1)[-1]))
                if not content:
                    raise ValueError('Missing content type: '+part)
                E.SubElement(types, '{'+CT+'}Override', PartName='/'+new, ContentType=content)
                rp = relpath(part)
                if rp in z.namelist():
                    graph = xml(z.read(rp))
                    for rel in graph:
                        if rel.get('TargetMode') != 'External':
                            destination = clone(target(part, rel.get('Target')))
                            rel.set('Target', pp.relpath(destination, pp.dirname(new)))
                    data[relpath(new)] = E.tostring(graph, xml_declaration=True, encoding='UTF-8')
                return new
            selected = set()
            for number in numbers:
                if type(number) is not int or not 1 <= number <= len(ids):
                    raise ValueError('Invalid source slide number')
                part = target('ppt/presentation.xml', rels[ids[number-1].get('{'+R+'}id')].get('Target'))
                # A new map per duplicate selection preserves notes back-links.
                if number in selected:
                    raise ValueError('Duplicate selections within a source are unsupported')
                selected.add(number)
                new = clone(part)
                E.SubElement(slides, '{'+P+'}sldId', id=str(256+len(slides)), attrib={'{'+R+'}id': register(new, 'slide')})
                receipt.append({'source': str(entry['path']), 'slide': number, 'part': new})
            for old, new in list(mapped.items()):
                if old.startswith('ppt/slideMasters/') and old.endswith('.xml'):
                    container = presentation.find('{'+P+'}sldMasterIdLst')
                    if container is None:
                        container = E.Element('{'+P+'}sldMasterIdLst'); presentation.insert(0, container)
                    E.SubElement(container, '{'+P+'}sldMasterId', id=str(2147483648+len(container)), attrib={'{'+R+'}id': register(new, 'slideMaster')})
            if index > 0:
                font_list = src.find('{'+P+'}embeddedFontLst')
                if font_list is not None:
                    destination = presentation.find('{'+P+'}embeddedFontLst')
                    if destination is None:
                        destination = E.Element('{'+P+'}embeddedFontLst')
                        notes_size = presentation.find('{'+P+'}notesSz')
                        presentation.insert(list(presentation).index(notes_size)+1, destination)
                    for font in font_list:
                        new_font = copy.deepcopy(font)
                        for node in new_font.iter():
                            rid = node.get('{'+R+'}id')
                            if rid:
                                relation = rels[rid]
                                font_part = clone(target('ppt/presentation.xml', relation.get('Target')))
                                node.set('{'+R+'}id', register(font_part, relation.get('Type').rsplit('/',1)[-1]))
                        destination.append(new_font)
    data['ppt/presentation.xml'] = E.tostring(presentation, xml_declaration=True, encoding='UTF-8')
    data['ppt/_rels/presentation.xml.rels'] = E.tostring(relationships, xml_declaration=True, encoding='UTF-8')
    data['[Content_Types].xml'] = E.tostring(types, xml_declaration=True, encoding='UTF-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, blob in data.items():
            z.writestr(name, blob)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(merge(json.loads(args.spec.read_text('utf-8-sig')), args.out), ensure_ascii=False))
