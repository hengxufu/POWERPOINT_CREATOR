"""Bounded paper intake and traceable PDF figure extraction; no OCR or web access."""
import argparse, hashlib, json, re
from pathlib import Path

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_new(path, data):
    path=Path(path)
    if path.exists(): raise ValueError('Output exists; choose a new version.')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def pdf_module():
    try: import pymupdf
    except ImportError as exc:
        raise SystemExit('PDF support requires PyMuPDF; install requirements-paper.txt in a project environment.') from exc
    return pymupdf

def pages(spec, count):
    if not spec: return list(range(min(2,count)))
    selected=set()
    for part in spec.split(','):
        if not re.fullmatch(r'\d+(?:-\d+)?',part.strip()): raise ValueError('Pages must be 1,3-5 style, one-based.')
        values=[int(n) for n in part.strip().split('-')]
        lo,hi=(values*2 if len(values)==1 else values)
        if lo<1 or hi<lo or hi>count: raise ValueError('Page range is outside the PDF.')
        selected.update(range(lo-1,hi))
    return sorted(selected)

def intake(args):
    source=Path(args.source)
    result={'schema':'paper_source_packet_v1','source_id':args.source_id,
            'source_file':str(source.resolve()),'source_sha256':digest(source),
            'metadata_verified':False,'pages':[],'warnings':[]}
    if source.suffix.lower()=='.pdf':
        pdf=pdf_module()
        with pdf.open(source) as doc:
            result['page_count']=len(doc)
            result['pdf_metadata']=doc.metadata
            result['scope']='selected_pages_only'
            for i in pages(args.pages,len(doc)):
                text=doc[i].get_text('text',sort=True)
                result['pages'].append({'page':i+1,'text':text[:args.max_chars],
                  'truncated':len(text)>args.max_chars,
                  'caption_candidates':[line.strip() for line in text.splitlines()
                    if re.match(r'^(?:Fig(?:ure)?\.?\s*\d|Table\s*\d|图\s*\d|表\s*\d)',line.strip(),re.I)]})
            if len(result['pages'])<len(doc): result['warnings'].append('Only selected pages read; select required result/method/legend pages before asserting full-paper coverage.')
            if not any(p['text'].strip() for p in result['pages']): result['warnings'].append('No selectable text on selected pages; scanned PDF may require separately authorized OCR.')
    elif source.suffix.lower() in ('.md','.txt'):
        if args.pages: raise ValueError('--pages applies only to PDFs.')
        text=source.read_text(encoding='utf-8-sig')
        result['scope']='provided_text_only'
        result['pages']=[{'page':None,'text':text[:args.max_chars],'truncated':len(text)>args.max_chars}]
    else: raise ValueError('Supported source files: PDF, UTF-8 Markdown or text.')
    if any(p['truncated'] for p in result['pages']): result['warnings'].append('Text truncated; revisit needed passages, do not infer omitted content.')
    result['warnings'].append('PDF metadata and caption candidates need source checking; no scientific claim verification is performed.')
    write_new(args.out,result)

def crop(args):
    out=Path(args.out);manifest=out.with_suffix(out.suffix+'.source.json')
    if out.suffix.lower()!='.png': raise ValueError('Figure output must be PNG.')
    if out.exists() or manifest.exists(): raise ValueError('Asset or manifest exists; choose a new version.')
    if not 72<=args.dpi<=600: raise ValueError('DPI must be between 72 and 600.')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',args.asset_id): raise ValueError('Use a filename-safe asset ID.')
    pdf=pdf_module()
    with pdf.open(args.source) as doc:
        if not 1<=args.page<=len(doc): raise ValueError('Page is outside PDF.')
        page=doc[args.page-1];rect=pdf.Rect(args.rect)
        if rect.is_empty or rect.is_infinite or not page.rect.contains(rect): raise ValueError('Crop must be non-empty and inside the displayed page rectangle.')
        pix=page.get_pixmap(clip=rect,dpi=args.dpi,alpha=False)
        out.parent.mkdir(parents=True,exist_ok=True)
        pix.save(out)
        record={'schema':'paper_figure_asset_v1','asset_id':args.asset_id,'source_id':args.source_id,
           'source_file':str(Path(args.source).resolve()),'source_sha256':digest(args.source),
           'page':args.page,'figure_label':args.label,'claim':args.claim,
           'crop_rect_pdf_points':list(rect),'page_rotation':page.rotation,'dpi':args.dpi,
           'asset_file':out.name,'asset_sha256':digest(out),'pixel_size':[pix.width,pix.height],
           'scientific_evidence':True,'crop_review':'pending',
           'required_review':['panel letters','axes and ticks','legend/colorbar','scale bar','conditions/units','caption and source','readability at slide size']}
    write_new(manifest,record)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('intake');a.add_argument('--source',required=True);a.add_argument('--source-id',default='paper-1');a.add_argument('--pages');a.add_argument('--max-chars',type=int,default=20000);a.add_argument('--out',required=True);a.set_defaults(func=intake)
    a=sub.add_parser('crop');a.add_argument('--source',required=True);a.add_argument('--source-id',default='paper-1');a.add_argument('--page',type=int,required=True);a.add_argument('--rect',type=float,nargs=4,required=True);a.add_argument('--dpi',type=int,default=300);a.add_argument('--asset-id',required=True);a.add_argument('--label',required=True);a.add_argument('--claim',required=True);a.add_argument('--out',required=True);a.set_defaults(func=crop)
    args=p.parse_args()
    if getattr(args,'max_chars',1)<1: p.error('--max-chars must be positive')
    args.func(args);print(args.out)

if __name__=='__main__':main()
