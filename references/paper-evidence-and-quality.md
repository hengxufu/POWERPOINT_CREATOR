# 论文证据资产与验收

## 选页和提取

普通PDF先读取可选文本；只在选图位置不清时做低分辨率定位，再提取需要的页面与子图。OCR和完整补充材料处理需要实际理由或用户要求。安装可选requirements-paper.txt以启用PDF工具；文本材料不需要PyMuPDF。

```powershell
python scripts/paper_source.py intake --source paper.pdf --pages 1,4-6 --out paper-packet.json
# 根据实际查看的PDF位置填写矩形，单位PDF points，页码从1起；以下是命令格式，不是实际图坐标。
python scripts/paper_source.py crop --source paper.pdf --page 4 --rect 30 80 560 420 --dpi 300 --asset-id fig2b --label 'Fig. 2b' --claim '填写该图支撑的主张' --out output/assets/figures/fig2b.png
```

crop保存来源哈希、页码、矩形、DPI、图号、主张和图片哈希。不会自动证明裁剪正确。查看原页面与导出的PNG，确认面板字母、轴/刻度、图例/色条、比例尺、条件/样本/单位和表头。失去关键语义就扩大矩形、拆页、换清晰原图或依据明确数值建原生表格。通过后将source.json的crop_review设为pass，注明实际检查和有意省略的内容；保留原始PDF。

## 引用和视觉

封面注明题名、作者/期刊、年份和DOI（有证据时）；每张证据图注明图号、子图、原文页或来源。改绘注明整理自/改绘自，不能隐藏对照和比例尺。综述中的关键结果尽量追溯原始研究。整张PDF页面不能当作PPT内容页；必要证据子图可独立插入，注释和来源文字原生可编辑。

构图依据证据几何选择主图、横向流程、非对称图文、对比表或开放讨论。不要全篇套同一三卡片或左右均分布局。长解释放备注，字号按投影场景和主技能调节，不直接套用上游较小的论文阅读字号。保留现有模板，允许用户已要求的封面艺术字和局部渐变，但装饰不得盖住数据。

## 检查链

```powershell
python scripts/audit_paper_deck.py output/final_presentation_cn.pptx --plan paper-plan.json --report output/paper-audit.md --json output/paper-audit.json --fail-on high
python scripts/audit_editability.py output/final_presentation_cn.pptx --out output/editability.json
python scripts/typography_check.py output/final_presentation_cn.pptx --out output/typography.json
```

paper-plan.json为可选元数据；不提供时仍检查PPTX结构。审计按实际显示顺序报告页码，检查顶层对象出界、文字密度、裁剪信号、泛化措辞；提供计划时检查重复ID、不存在页、缺少支持来源和未复核证据裁剪。组内坐标、像素文字溢出、真实数据和审美由人工/渲染核对。来源字段存在不等于来源支持主张。

high：关键证据缺失/误导、裁剪丢失语义、真实内容越界或不可读、无来源的确切结论；medium：密度过大、引用不明、重复布局、备注不足；low：小幅对齐和配色细节。脚本报high先定位和判读，确认缺陷则修复，不靠降低级别掩盖问题。已安装nature-paper2ppt时，可额外运行其原始audit_pptx_quality.py；该脚本未随本模块复制，原结果可能按部件页号报告，重排页须对照显示序。

QA记录实际检查的图、页、缺陷/修复与未完成项；不能宣称XML检查证明PowerPoint显示或全部科学主张正确。
