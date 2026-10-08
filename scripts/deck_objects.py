"""Display-order object inventory and preconditioned, package-preserving OOXML edits.
No renderer: reported font sizes, unbound lines and alt text are review signals.
"""
import argparse, copy, hashlib, json, posixpath, zipfile
from pathlib import Path
from defusedxml.minidom import parseString

def elements(node,tag):return list(node.getElementsByTagName(tag))
def direct(node,tag):return next((e for e in node.childNodes if getattr(e,'tagName',None)==tag),None)
def sha(data):return hashlib.sha256(data).hexdigest()
def slide_parts(z):
    p=parseString(z.read('ppt/presentation.xml'))
    r=parseString(z.read('ppt/_rels/presentation.xml.rels'))
    targets={e.getAttribute('Id'):e.getAttribute('Target') for e in elements(r,'Relationship')}
    out=[]
    for e in elements(p,'p:sldId'):
        t=targets[e.getAttribute('r:id')]
        out.append(t.lstrip('/') if t.startswith('/') else posixpath.normpath('ppt/'+t))
    return out,p
def shapes(d):
    out={}
    for tag in ('p:sp','p:pic','p:cxnSp','p:graphicFrame','p:grpSp'):
        for node in elements(d,tag):
            nv=next((e for e in node.childNodes if getattr(e,'tagName','').startswith('p:nv')),None)
            if nv:
                pr=direct(nv,'p:cNvPr')
                if pr:
                    sid=pr.getAttribute('id')
                    if sid in out:raise ValueError('duplicate object id '+sid)
                    out[sid]=(node,pr)
    return out
def inspect(path):
    result={'pptx':str(path),'sha256':sha(Path(path).read_bytes()),'pages':[],
      'limits':['Font size is stored size; group transforms and inherited fonts may change appearance.',
                'Unbound connectors can be intentional. No automatic endpoint guessing.',
                'No pixel-level overflow, reading-order, contrast or scientific truth certification.']}
    with zipfile.ZipFile(path) as z:
        names,p=slide_parts(z);sz=elements(p,'p:sldSz')[0];width=int(sz.getAttribute('cx'))/914400
        for page,name in enumerate(names,1):
            d=parseString(z.read(name));items=[];warnings=[]
            for sid,(node,pr) in shapes(d).items():
                runs=[e.firstChild.data if e.firstChild else '' for e in elements(node,'a:t')] if node.tagName!='p:grpSp' else []
                sizes=sorted({int(e.getAttribute('sz'))/100 for e in elements(node,'a:rPr') if e.hasAttribute('sz')}) if node.tagName!='p:grpSp' else []
                item={'id':sid,'key':f'S{page:02d}.{sid}','kind':node.tagName,'name':pr.getAttribute('name'),'runs':runs,'alt_text':pr.getAttribute('descr'),'font_pt':sizes}
                sppr=direct(node,'p:spPr');xf=direct(sppr,'a:xfrm') if sppr else direct(node,'p:xfrm')
                if xf:
                    item['local_transform_emu']={e.tagName:{k:e.getAttribute(k) for k in ('x','y','cx','cy') if e.hasAttribute(k)} for e in xf.childNodes if getattr(e,'tagName',None) in ('a:off','a:ext')}
                if node.tagName=='p:pic' and not item['alt_text']:warnings.append({'object':item['key'],'code':'picture_missing_alt_text'})
                if sizes and min(sizes)*13.333/width<14: warnings.append({'object':item['key'],'code':'small_normalized_font','normalized_min_pt':round(min(sizes)*13.333/width,1)})
                if node.tagName=='p:cxnSp':
                    starts=elements(node,'a:stCxn');ends=elements(node,'a:endCxn')
                    item['bindings']={'start':[{k:e.getAttribute(k) for k in ('id','idx')} for e in starts],'end':[{k:e.getAttribute(k) for k in ('id','idx')} for e in ends]}
                    if not starts or not ends:warnings.append({'object':item['key'],'code':'connector_not_bound_at_both_ends'})
                items.append(item)
            result['pages'].append({'page':page,'part':name,'objects':items,'review_signals':warnings})
    return result
def patch(src,plan,out):
    if Path(out).exists():raise ValueError('Output exists; choose a new version.')
    if Path(src).resolve()==Path(out).resolve():raise ValueError('Never overwrite input.')
    payload=json.loads(Path(plan).read_text(encoding='utf-8-sig'))
    if payload.get('input_sha256')!=sha(Path(src).read_bytes()):raise ValueError('Input hash mismatch; regenerate object inventory.')
    changed={};receipt=[]
    with zipfile.ZipFile(src) as z:
        names,_=slide_parts(z)
        for op in payload['operations']:
            page=op['page']
            if not isinstance(page,int) or not 1<=page<=len(names):raise ValueError('Invalid display page')
            part=names[page-1]
            if part not in changed:changed[part]=parseString(z.read(part))
            node,pr=shapes(changed[part])[str(op['id'])]
            if op['action'] in ('rename','alt_text'):
                attr='name' if op['action']=='rename' else 'descr'
                if pr.getAttribute(attr)!=op['expected']:raise ValueError('Stale object metadata')
                pr.setAttribute(attr,op['value'])
            elif op['action']=='text_run':
                if node.tagName=='p:grpSp':raise ValueError('Target a child shape, not a group.')
                t=elements(node,'a:t')[op['run_index']];current=t.firstChild.data if t.firstChild else ''
                if current!=op['expected']:raise ValueError('Stale text run')
                if '\n' in op['value']:raise ValueError('Use authoring engine for paragraph restructuring.')
                if t.firstChild:t.firstChild.data=op['value']
                else:t.appendChild(t.ownerDocument.createTextNode(op['value']))
                if op['value']!=op['value'].strip():t.setAttribute('xml:space','preserve')
            elif op['action']=='bind_connector':
                if node.tagName!='p:cxnSp':raise ValueError('Only native connectors may be bound.')
                nv=direct(node,'p:nvCxnSpPr');props=direct(nv,'p:cNvCxnSpPr')
                old={key:[{k:e.getAttribute(k) for k in ('id','idx')} for e in elements(node,tag)] for key,tag in [('start','a:stCxn'),('end','a:endCxn')]}
                if old!=op['expected']:raise ValueError('Stale connector binding')
                all_shapes=shapes(changed[part])
                for key,tag in [('start','a:stCxn'),('end','a:endCxn')]:
                    target=op[key];tn,_=all_shapes[str(target['id'])]
                    prst=elements(tn,'a:prstGeom')
                    if tn.tagName!='p:sp' or not prst or prst[0].getAttribute('prst') not in ('rect','roundRect','ellipse'):raise ValueError('Only explicit rectangle/roundRect/ellipse endpoints supported.')
                    if type(target['site']) is not int or target['site'] not in range(4):raise ValueError('Connection site must be 0..3')
                    for e in list(elements(props,tag)):props.removeChild(e)
                    e=changed[part].createElementNS('http://schemas.openxmlformats.org/drawingml/2006/main',tag);e.setAttribute('id',str(target['id']));e.setAttribute('idx',str(target['site']))
                    # stCxn precedes endCxn; extLst follows both.
                    anchor=direct(props,'a:endCxn') if key=='start' else direct(props,'a:extLst')
                    if anchor:props.insertBefore(e,anchor)
                    else:props.appendChild(e)
            else:raise ValueError('Unsupported action: '+op['action'])
            receipt.append(op)
        data={n:d.toxml(encoding='UTF-8') for n,d in changed.items()}
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dest:
            for info in z.infolist():dest.writestr(copy.copy(info),data.get(info.filename,z.read(info.filename)))
        with zipfile.ZipFile(out) as final:
            assert set(z.namelist())==set(final.namelist())
            assert all(z.read(n)==final.read(n) for n in z.namelist() if n not in changed)
    report={'input_sha256':payload['input_sha256'],'output_sha256':sha(Path(out).read_bytes()),'changed_slide_parts':list(changed),'operations':receipt,'visual_review':'pending if visible text changed; metadata-only edits preserve visual content'}
    Path(str(out)+'.patch.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True)
    a=sub.add_parser('inspect');a.add_argument('pptx');a.add_argument('--out',required=True)
    b=sub.add_parser('patch');b.add_argument('pptx');b.add_argument('--plan',required=True);b.add_argument('--out',required=True)
    args=ap.parse_args()
    if args.command=='inspect':
        report=inspect(args.pptx);Path(args.out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(args.out)
    else:print(json.dumps(patch(args.pptx,args.plan,args.out),ensure_ascii=True))
if __name__=='__main__':main()
