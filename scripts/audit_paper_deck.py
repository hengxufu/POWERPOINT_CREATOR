"""Paper-report QA using actual display order; structural signals, not visual proof."""
import argparse, json, zipfile
from pathlib import Path
from defusedxml.minidom import parseString
from deck_objects import slide_parts, elements, direct

def audit(path,plan=None):
    findings=[];summaries=[]
    def add(severity,page,code,message):findings.append(dict(severity=severity,page=page,code=code,message=message))
    with zipfile.ZipFile(path) as z:
        parts,p=slide_parts(z);size=elements(p,'p:sldSz')[0]
        width,height=int(size.getAttribute('cx')),int(size.getAttribute('cy'))
        for number,part in enumerate(parts,1):
            d=parseString(z.read(part));tree=elements(d,'p:spTree')[0]
            text='\n'.join(n.firstChild.data for n in elements(d,'a:t') if n.firstChild)
            images=len(elements(d,'p:pic'))
            for node in tree.childNodes:
                kind=getattr(node,'tagName','')
                if kind=='p:grpSp':
                    add('low',number,'group_transform_review','Grouped coordinates need rendered review; no untransformed child bounds assertion.')
                    continue
                if kind not in ('p:sp','p:pic','p:graphicFrame','p:cxnSp'):continue
                sp=direct(node,'p:spPr');xf=direct(sp,'a:xfrm') if sp else direct(node,'p:xfrm')
                if xf:
                    off=direct(xf,'a:off');ext=direct(xf,'a:ext')
                    if off and ext:
                        x,y=int(off.getAttribute('x')),int(off.getAttribute('y'));w,h=int(ext.getAttribute('cx')),int(ext.getAttribute('cy'))
                        if min(x,y)<-12700 or x+w>width+12700 or y+h>height+12700:
                            add('high',number,'shape_out_of_bounds','Top-level object exceeds canvas; inspect content and intended edge decoration.')
                count=sum(len(n.firstChild.data) for n in elements(node,'a:t') if n.firstChild)
                if count>240:add('medium',number,'dense_text_review','Text exceeds 240 characters in one object; review layout, notes or split. Not pixel overflow proof.')
            if elements(d,'a:srcRect'):add('medium',number,'cropped_image_review','Image crop detected; verify axes, labels, conditions and scale bars. A crop alone is not a failure.')
            for phrase in ('一句话总结','最有价值的后续方向','提供了新的视角'):
                if phrase in text:add('low',number,'generic_wording_review','Review source-specific wording: '+phrase)
            summaries.append({'page':number,'part':part,'images':images,'text_chars':len(text)})
        notes=[n for n in z.namelist() if n.startswith('ppt/notesSlides/notesSlide') and n.endswith('.xml')]
    if plan:
        if plan.get('paper_type') not in ('discovery','methods','resource','clinical','materials','review'):
            add('high',None,'invalid_paper_type','Plan needs one of six supported paper types.')
        seen=set()
        for slide in plan.get('slides',[]):
            page=slide.get('page');sid=slide.get('slide_id')
            if not isinstance(page,int) or isinstance(page,bool) or not 1<=page<=len(summaries):
                add('high',None,'plan_page_missing','Planned page not in deck.');continue
            if not sid or sid in seen:add('high',page,'slide_id_missing_or_duplicate','Stable unique slide_id required.')
            seen.add(sid)
            if slide.get('claim_status')=='source_supported' and not slide.get('source_refs'):
                add('high',page,'unsupported_claim','Plan marks claim source-supported without source references.')
            if slide.get('role')=='result' and not slide.get('source_refs'):
                add('medium',page,'result_source_missing','Result plan needs source page/figure/table reference or explicit unavailable-source status.')
            for asset in slide.get('figure_assets',[]):
                if asset.get('crop_review')!='pass':add('high',page,'figure_crop_unreviewed','Evidence asset crop review is not passed; inspect before delivery.')
    counts={level:sum(f['severity']==level for f in findings) for level in ('high','medium','low')}
    return {'scope':'structural_and_plan_metadata','slide_count':len(summaries),'notes_parts':len(notes),
      'findings':findings,'finding_counts':counts,'slides':summaries,
      'limits':['Not a source-truth, pixel overflow, crop completeness or aesthetic certification.',
                'Only top-level bounds; grouped transformations require rendered review.',
                'A source reference field does not prove the referenced paper supports the claim.',
                'OOXML note part count does not prove useful speaker notes.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pptx');p.add_argument('--plan');p.add_argument('--report',required=True);p.add_argument('--json');p.add_argument('--fail-on',choices=['high','medium','low','none'],default='high');a=p.parse_args()
    plan=json.loads(Path(a.plan).read_text('utf-8-sig')) if a.plan else None;r=audit(a.pptx,plan)
    lines=['# 论文汇报PPT检查','',f"页数：{r['slide_count']}；high={r['finding_counts']['high']}，medium={r['finding_counts']['medium']}，low={r['finding_counts']['low']}",'','|级别|显示页|代码|检查事项|','|---|---|---|---|']
    lines += [f"|{f['severity']}|{f['page'] or ''}|{f['code']}|{f['message']}|" for f in r['findings']]
    lines += ['','局限：']+['- '+v for v in r['limits']]
    report=Path(a.report);report.parent.mkdir(parents=True,exist_ok=True);report.write_text('\n'.join(lines)+'\n','utf-8')
    if a.json:Path(a.json).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(r['finding_counts']))
    rank={'low':1,'medium':2,'high':3,'none':99};raise SystemExit(int(any(rank[f['severity']]>=rank[a.fail_on] for f in r['findings'])))

if __name__=='__main__':main()
