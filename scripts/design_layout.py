"""Advisory plan geometry audit. Never certifies rendered beauty or counts PPT objects."""
import argparse
import hashlib
import json
import math
from pathlib import Path

DESIGN_BRIEF = '''逐页先判断表达关系：整体-细节、流程-条件、并列比较、公式-物理解释或证据-边界，再选布局。
同页有一个primary视觉组（可含多个对象），secondary负责证据补充，annotation负责符号/单位/来源；不是只有一个大对象。
design_system给spacing_inches（建议.08/.16/.24/.40）、font_roles_pt、color_roles、stroke_pt、corner_radius_inches和asset_family。
每页content_blocks与实际摆放的asset_requests均给唯一object_id、role、box_inches；文本给font_pt，装饰role=ornament。
给alignment_groups（axis=left/right/top/bottom，members为对象ID）与reading_order（不含装饰），并标明主要视觉组。
容器用role=container，子项parent_id指向容器。必要叠放在子项allowed_overlaps中逐项写object_id和具体reason，禁止整页豁免。
普通正文以18–24pt为起点；复杂公式先拆推导步骤/符号区/物理解释区，不缩字堆满。不把建议字号当成投影可读的保证。
单元素除材质光照外，还要写viewpoint、silhouette、edge_treatment、detail_level、optical_padding；配饰放大看精致、缩小看轮廓。
同一图标系列统一视角、笔画和光源；结果页装饰退到最弱层，不能遮住坐标轴、误差条、单位或引用。
40元素是独立可见对象要求，不是美观评分；先组织为少量有意义的信息组，不能拆字、拆表格或复制无用装饰凑数。
布局完成后运行design_layout.py预检，修复几何错误，再实际渲染审查；预检不能替代像素级排版、图表或科学正确性审查。'''


def intersection(a, b):
    return max(0, min(a[0]+a[2], b[0]+b[2])-max(a[0], b[0])) * max(0, min(a[1]+a[3], b[1]+b[3])-max(a[1], b[1]))


def box_valid(box):
    return (isinstance(box, list) and len(box) == 4 and
            all(type(v) in (int, float) and math.isfinite(v) for v in box) and min(box[2:]) > 0)


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
