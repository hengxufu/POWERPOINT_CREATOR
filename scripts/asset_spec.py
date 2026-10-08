"""Create one style-consistent element spec; does not submit a web generation."""
import argparse,json
from pathlib import Path
PRESETS={
 'orbital_accent':{'element':'一个抽象轨道环装饰，轻微倾斜的单个椭圆环，主体连续完整，无航天器或其他主体','kind':'ornament','aspect':'1:1'},
 'spacecraft_concept':{'element':'一艘独立航天器的概念模型，三分之四视角，细节克制，不带坐标轴、标签或轨道场景','kind':'concept','aspect':'1:1'},
 'thermal_concept':{'element':'一艘独立航天器的热红外概念外观，暖色局部与冷色主体区分，不附加色标或温度数值','kind':'concept','aspect':'1:1'},
 'section_wordart':{'element':'一组独立的章节艺术字，简洁轻立体、轮廓清楚','kind':'art_text','aspect':'3:1'},
}
def main():
 p=argparse.ArgumentParser();p.add_argument('--preset',choices=PRESETS,required=True);p.add_argument('--asset-id',required=True);p.add_argument('--slide-id',required=True);p.add_argument('--object-id',required=True);p.add_argument('--exact-text');p.add_argument('--palette',default='北航蓝 #005BAC、深蓝 #164D80、少量浅蓝高光');p.add_argument('--out',required=True);a=p.parse_args()
 spec=dict(PRESETS[a.preset]);spec.update(asset_id=a.asset_id,slide_id=a.slide_id,object_id=a.object_id,palette=a.palette,transparent=True,min_width=1536,min_height=1024,style='中国科研汇报；克制、清晰、轻立体；无厚重光晕',visual_context={'slide_background':'白色或浅蓝','lighting':'左上柔和光源','material':'哑光，少量高光','placement':'局部独立装饰，保持证据与正文优先','avoid':'不生成页面、数据、标签或多个变体'})
 if spec['kind']=='art_text':
  if not a.exact_text:p.error('--exact-text is required for section_wordart')
  spec['exact_text']=a.exact_text
 out=Path(a.out)
 if out.exists():raise FileExistsError('Choose a new version; spec exists.')
 out.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
if __name__=='__main__':main()
