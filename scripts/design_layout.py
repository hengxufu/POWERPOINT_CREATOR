"""Advisory plan geometry audit. Never certifies rendered beauty or counts PPT objects."""
import argparse
import hashlib
import json
import math
import unicodedata
from pathlib import Path

DESIGN_BRIEF = '''逐页先判断表达关系：整体-细节、流程-条件、并列比较、公式-物理解释或证据-边界，再选布局。
同页有一个primary视觉组（可含多个对象），secondary负责证据补充，annotation负责符号/单位/来源；不是只有一个大对象。
design_system给spacing_inches（建议.08/.16/.24/.40）、font_roles_pt、color_roles、stroke_pt、corner_radius_inches和asset_family。
每页content_blocks与实际摆放的asset_requests均给唯一object_id、role、box_inches；文本给font_pt，装饰role=ornament。
给alignment_groups（axis=left/right/top/bottom，members为对象ID）与reading_order（不含装饰），并标明主要视觉组。
容器用role=container，子项parent_id指向容器。必要叠放在子项allowed_overlaps中逐项写object_id和具体reason，禁止整页豁免。
普通正文以18–24pt为起点；复杂公式先拆推导步骤/符号区/物理解释区，不缩字堆满。不把建议字号当成投影可读的保证。
正文用结论句+支持证据+解释/边界组织，标题表述该页问题或可证实结论，避免目录标签。细节移入讲稿时保留影响结论的条件、单位、不确定性和来源。
文本可声明text_layout={margin_inches:[左,上,右,下],line_spacing:1.2,paragraph_space_after_pt:4}，用于容量预警；实际换行仍须渲染。文字拥挤先重新分组、扩大解释区或拆成递进页，不自动缩字或删关键限定。
有统一左缩进时在text_layout声明indent_pt（默认0，非负点数），从每行净宽扣除；复杂悬挂缩进与项目符号必须在实际原生文本框及渲染中核对。
spacing_groups={axis:horizontal或vertical,members:[按空间顺序的对象ID],min_gap_inches:.16}以数组提供，区分组内/组间距离；caption_for关联真实证据对象，让图注靠近来源图而非漂在页底。
单元素除材质光照外，还要写viewpoint、silhouette、edge_treatment、detail_level、optical_padding；配饰放大看精致、缩小看轮廓。
同一图标系列统一视角、笔画和光源；结果页装饰退到最弱层，不能遮住坐标轴、误差条、单位或引用。
40元素是独立可见对象要求，不是美观评分；先组织为少量有意义的信息组，不能拆字、拆表格或复制无用装饰凑数。
布局完成后运行design_layout.py预检，修复几何错误，再实际渲染审查；预检不能替代像素级排版、图表或科学正确性审查。'''


def intersection(a, b):
    return max(0, min(a[0]+a[2], b[0]+b[2])-max(a[0], b[0])) * max(0, min(a[1]+a[3], b[1]+b[3])-max(a[1], b[1]))


def box_valid(box):
    return (isinstance(box, list) and len(box) == 4 and
            all(type(v) in (int, float) and math.isfinite(v) for v in box) and min(box[2:]) > 0)


def text_pressure(item):
    """Rough character-width estimate, never a font-shaping or PPT overflow test."""
    text, size = item.get('text'), item.get('font_pt')
    if not isinstance(text,str) or not text.strip() or not box_valid(item.get('box_inches')):
        return None
    if type(size) not in (int,float) or not math.isfinite(size) or size <= 0:
        return None
    if item.get('type') in ('chart','table','formula','equation'):
        return None
    settings = item.get('text_layout',{})
    if not isinstance(settings,dict):
        raise ValueError('text_layout must be an object')
    margins = settings.get('margin_inches',[.08,.08,.08,.08])
    spacing, after = settings.get('line_spacing',1.2), settings.get('paragraph_space_after_pt',4)
    if not isinstance(margins,list) or len(margins)!=4 or not all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in margins):
        raise ValueError('Text margins require four finite nonnegative inches')
    if type(spacing) not in (int,float) or not math.isfinite(spacing) or spacing<=0 or type(after) not in (int,float) or not math.isfinite(after) or after<0:
        raise ValueError('Invalid text spacing')
    indent = settings.get('indent_pt', 0)
    if type(indent) not in (int,float) or not math.isfinite(indent) or indent < 0:
        raise ValueError('Text indent requires finite nonnegative points')
    width = (item['box_inches'][2]-margins[0]-margins[2])*72 - indent
    height = (item['box_inches'][3]-margins[1]-margins[3])*72
    paragraphs = text.replace('\r\n','\n').replace('\r','\n').split('\n')
    lines, wide_glyph = 0, False
    for paragraph in paragraphs:
        used = 0
        lines += 1
        for char in paragraph:
            advance = 0 if unicodedata.combining(char) else size*(1 if unicodedata.east_asian_width(char) in ('W','F') else .55)
            wide_glyph = wide_glyph or advance>width
            if used and used+advance>max(width,1):
                lines += 1
                used = 0
            used += advance
    needed = lines*size*spacing + max(0,len(paragraphs)-1)*after
    return {'estimated_lines':lines,'estimated_height_pt':round(needed,1),'available_height_pt':round(max(0,height),1),
            'width_pressure':width<=0 or wide_glyph,
            'pressure':width<=0 or height<=0 or wide_glyph or needed>height,
            'method':'Approximate CJK/Latin widths with declared uniform indent; no font shaping, word breaking, hanging indents or renderer measurements.'}


def audit(plan):
    canvas = plan.get('canvas_inches', [13.333, 7.5])
    if not isinstance(canvas, list) or len(canvas) != 2 or not all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in canvas):
        raise ValueError('Finite positive canvas_inches required')
    slides = plan.get('slides')
    if not isinstance(slides, list) or not slides:
        raise ValueError('Nonempty slides required')
    width, height = canvas
    theme = plan.get('design_system', {}).get('theme_profile', 'none')
    if not isinstance(theme, str):
        raise ValueError('theme_profile must be a string')
    findings, pages = [], []

    def issue(slide_id, code, objects, message, severity='warning'):
        findings.append(dict(slide_id=slide_id, code=code, objects=objects, message=message, severity=severity))

    families = []
    for number, slide in enumerate(slides, 1):
        if not isinstance(slide, dict):
            raise ValueError('Each slide must be an object')
        sid = slide.get('slide_id', str(number))
        items = list(slide.get('content_blocks', [])) + [a for a in slide.get('asset_requests', []) if a.get('decision', 'generate_web') == 'generate_web']
        by_id = {}
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get('allowed_overlaps', []), list):
                raise ValueError('Objects and allowed_overlaps must be structured records')
            oid = item.get('object_id')
            if not isinstance(oid, str) or not oid.strip() or oid in by_id:
                issue(sid, 'object_id', [str(oid or index)], 'Provide a unique nonempty object_id.', 'error')
                continue
            box = item.get('box_inches')
            if not box_valid(box):
                issue(sid, 'box', [oid], 'Provide finite [x,y,w,h] with positive size.', 'error')
                continue
            by_id[oid] = item
            x,y,w,h = box
            if x < 0 or y < 0 or x+w > width+1e-6 or y+h > height+1e-6:
                issue(sid, 'outside_canvas', [oid], 'Move or resize object inside the canvas.', 'error')
            if theme.startswith('beihang-') and item.get('role') not in ('background', 'theme'):
                if intersection(box, [.79*width, .025*height, .185*width, .075*height]) > 1e-6 or y+h > .925*height+1e-6:
                    issue(sid, 'theme_collision', [oid], 'Keep university identity and footer clear.', 'error')
            if item.get('role') not in ('primary', 'secondary', 'annotation', 'ornament', 'container', 'background', 'theme'):
                issue(sid, 'role', [oid], 'Assign a semantic visual role.')
            if 'text' in item and item.get('role') not in ('container', 'background'):
                size = item.get('font_pt')
                threshold = 12 if item.get('role') in ('annotation', 'theme') else 18
                if type(size) not in (int, float) or not math.isfinite(size) or size <= 0:
                    issue(sid, 'font_missing', [oid], 'Declare a finite positive font_pt; check actual rendering later.')
                elif size < threshold:
                    issue(sid, 'small_text', [oid], f'Below advisory {threshold}pt; reorganize before shrinking text.')
                pressure = text_pressure(item)
                if pressure and pressure['pressure']:
                    width_note = 'Estimated glyph width exceeds the usable box width. ' if pressure['width_pressure'] else ''
                    issue(sid, 'text_pressure', [oid], width_note+f"Estimated {pressure['estimated_lines']} lines / {pressure['estimated_height_pt']}pt into {pressure['available_height_pt']}pt. Reflow, enlarge or split; preserve scientific qualifiers. Verify real wrapping.")
            parent = item.get('parent_id')
            if parent == oid:
                issue(sid, 'parent', [oid], 'An object cannot contain itself.', 'error')
        for oid, item in by_id.items():
            parent = item.get('parent_id')
            if parent and parent != oid:
                container = by_id.get(parent)
                if not container or container.get('role') != 'container' or intersection(item['box_inches'], container['box_inches']) < item['box_inches'][2]*item['box_inches'][3]-1e-6:
                    issue(sid, 'parent', [oid, parent], 'Parent must be an enclosing container.', 'error')
        ids = list(by_id)
        for i, left in enumerate(ids):
            a = by_id[left]
            for right in ids[i+1:]:
                b = by_id[right]
                if 'background' in (a.get('role'), b.get('role')) or a.get('parent_id') == right or b.get('parent_id') == left:
                    continue
                area = intersection(a['box_inches'], b['box_inches'])
                if area < .01:
                    continue
                exemptions = [(a, right), (b, left)]
                explained = any(isinstance(e, dict) and e.get('object_id') == other and isinstance(e.get('reason'), str) and e['reason'].strip()
                                for obj, other in exemptions for e in obj.get('allowed_overlaps', []))
                if explained:
                    issue(sid, 'intentional_overlap', [left, right], 'Declared layering still requires rendered inspection.', 'info')
                else:
                    issue(sid, 'overlap', [left, right], 'Separate boxes or document purposeful layering; bounding boxes may overestimate transparent-image overlap.')
        for group in slide.get('alignment_groups', []):
            axis, members = group.get('axis'), group.get('members', [])
            if not isinstance(members, list) or not all(isinstance(m, str) for m in members):
                raise ValueError('Alignment members must be object ID strings')
            if axis not in ('left','right','top','bottom') or len(members) < 2 or len(set(members)) != len(members) or any(m not in by_id for m in members):
                issue(sid, 'alignment_group', members, 'Use an axis and at least two unique known object IDs.', 'error')
                continue
            positions = []
            for member in members:
                x,y,w,h = by_id[member]['box_inches']
                positions.append({'left':x,'right':x+w,'top':y,'bottom':y+h}[axis])
            if max(positions)-min(positions) > .04:
                issue(sid, 'alignment_drift', members, 'Declared aligned edges differ by more than .04 inches.')
        for group in slide.get('spacing_groups',[]):
            if not isinstance(group,dict):
                raise ValueError('spacing_groups must contain objects')
            axis, members, gap = group.get('axis'), group.get('members',[]), group.get('min_gap_inches',.16)
            if axis not in ('horizontal','vertical') or not isinstance(members,list) or not all(isinstance(m,str) for m in members) or len(members)<2 or len(set(members))!=len(members) or any(m not in by_id for m in members) or type(gap) not in (int,float) or not math.isfinite(gap) or gap<0:
                issue(sid,'spacing_group',[], 'Declare ordered known IDs, an axis and a finite nonnegative minimum gap.','error')
                continue
            coordinate, extent = (0,2) if axis=='horizontal' else (1,3)
            for left,right in zip(members,members[1:]):
                a,b = by_id[left]['box_inches'],by_id[right]['box_inches']
                actual = b[coordinate]-a[coordinate]-a[extent]
                if actual<gap-1e-6:
                    issue(sid,'tight_spacing',[left,right],f'Declared gap {gap:.2f}in, actual {actual:.2f}in; inspect grouping and object order.')
        for oid,item in by_id.items():
            target = item.get('caption_for')
            if target is None:
                continue
            if not isinstance(target,str) or target not in by_id or target==oid:
                issue(sid,'caption_target',[oid], 'caption_for must identify another evidence object.','error')
                continue
            a,b = item['box_inches'],by_id[target]['box_inches']
            distance = math.hypot(max(0,a[0]-b[0]-b[2],b[0]-a[0]-a[2]),max(0,a[1]-b[1]-b[3],b[1]-a[1]-a[3]))
            if distance>.6:
                issue(sid,'detached_caption',[oid,target], 'Caption is over .6in from its evidence; move closer or explain the visual link during rendered review.')
        reading = slide.get('reading_order', [])
        if not isinstance(reading, list) or not all(isinstance(m, str) for m in reading):
            raise ValueError('reading_order must be a list of object ID strings')
        if not reading or len(set(reading)) != len(reading) or any(m not in by_id for m in reading):
            issue(sid, 'reading_order', reading, 'Declare a unique known-object reading order, excluding ornaments.')
        if not any(item.get('role') == 'primary' for item in by_id.values()):
            issue(sid, 'primary_missing', [], 'Identify the main evidence/argument visual group.')
        decor_area = sum(item['box_inches'][2]*item['box_inches'][3] for item in by_id.values() if item.get('role') == 'ornament')
        if slide.get('theme_variant', 'content') == 'content' and decor_area/(width*height) > .12:
            issue(sid, 'decoration_budget', [], 'Ornament bounding-box area exceeds advisory 12% on content pages; inspect competition with evidence.')
        family = slide.get('layout_family')
        families.append(family)
        if len(families) >= 3 and family and len(set(families[-3:])) == 1 and not slide.get('layout_repeat_reason'):
            issue(sid, 'repeated_layout', [], 'Three successive identical families; vary evidence organization or explain comparability.')
        pages.append(dict(slide_id=sid, planned_boxes=len(by_id)))
    return dict(schema='design_layout_advisory_v1', geometry_errors=sum(f['severity']=='error' for f in findings),
                warnings=sum(f['severity']=='warning' for f in findings), findings=findings, slides=pages,
                visual_review_required=True, limits='Plan boxes only, not actual PPTX geometry, object count, text wrapping, transparency, scientific correctness or rendered aesthetics.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('Use a new audit report; preserve previous review versions')
    raw = args.plan.read_bytes()
    result = audit(json.loads(raw.decode('utf-8-sig')))
    result['plan_sha256'] = hashlib.sha256(raw).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'geometry_errors':result['geometry_errors'], 'warnings':result['warnings'], 'visual_review_required':True}))
    return 1 if result['geometry_errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
