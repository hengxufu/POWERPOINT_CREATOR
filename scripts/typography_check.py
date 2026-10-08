"""Audit explicit CJK/Latin font declarations and native equation representation.
Does not inspect text baked into bitmaps or prove application-level math rendering.
"""
import argparse,json,zipfile
import xml.etree.ElementTree as E
from pathlib import Path
A='http://schemas.openxmlformats.org/drawingml/2006/main';M='http://schemas.openxmlformats.org/officeDocument/2006/math'
def audit(path):
 mismatches=[];counts={'latin':0,'east_asian':0,'office_equations':0,'latex_compatibility_pictures':0};parts=[]
 with zipfile.ZipFile(path) as z:
  for name in z.namelist():
   if not name.endswith('.xml') or not name.startswith(('ppt/slides/','ppt/theme/','ppt/slideMasters/','ppt/slideLayouts/')):continue
   root=E.fromstring(z.read(name));parts.append(name)
   for tag,allowed,label in [('latin',{'Times New Roman'},'latin'),('ea',{'Microsoft YaHei','微软雅黑'},'east_asian')]:
    for el in root.iter('{'+A+'}'+tag):
     counts[label]+=1
     if el.get('typeface') not in allowed:mismatches.append({'part':name,'script':label,'typeface':el.get('typeface')})
   counts['office_equations']+=sum(1 for _ in root.iter('{'+M+'}oMath'))
   counts['latex_compatibility_pictures']+=sum(el.get('name','').startswith('LaTeX-fallback-') for el in root.iter('{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr'))
 return {'font_policy':{'chinese':'Microsoft YaHei / 微软雅黑','western':'Times New Roman'},'counts':counts,'mismatches':mismatches,'passed_explicit_font_check':not mismatches,'parts_checked':len(parts),'limits':['Bitmap labels, school logos and generated artistic glyphs have no editable font declaration.','Inherited theme styling still needs actual rendering review.','OMML count is structural evidence; verify native equations in the target PowerPoint version.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pptx');p.add_argument('--out',required=True);a=p.parse_args();r=audit(a.pptx);Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=True));raise SystemExit(0 if r['passed_explicit_font_check'] else 1)
