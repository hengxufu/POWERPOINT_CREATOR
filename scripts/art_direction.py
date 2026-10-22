"""Reusable visual defaults and advisory checks; never an aesthetic verdict."""
import copy
import math
import re

PRESETS = {
    'research-editorial': {
        'intent': '白底证据主导，清晰的大小层次，少量精致概念主体；结果页避免装饰竞争。',
        'image_defaults': {'material': '细腻哑光，克制的体积层次', 'lighting': '左上方柔和主光，低强度阴影',
                           'viewpoint': '同系列统一三分之四视角', 'edge_treatment': '边缘干净，无白边和光晕',
                           'silhouette': '完整、易识别的单一主体轮廓', 'detail_level': '缩小到实际摆放尺寸仍可辨识；省略细碎纹理',
                           'optical_padding': '四周约10%留白，阴影不截断'}},
    'technical-product': {
        'intent': '装置/产品为主焦点，原生编号、接口与部件解释组成信息层，避免廉价霓虹科技背景。',
        'image_defaults': {'material': '统一的哑光工程材质，局部金属细节', 'lighting': '左上柔光，弱轮廓光，不过曝',
                           'viewpoint': '统一轻等距三分之四视角', 'edge_treatment': '精确轮廓与克制倒角，无泛光',
                           'silhouette': '保留功能部件轮廓，结构忠于参考', 'detail_level': '优先功能结构，不添加虚构接口与刻度',
                           'optical_padding': '主体完整，四周约10%安全留白'}},
    'achievement-story': {
        'intent': '真实人物/经历与证据组成叙事，时间节奏与数字层次明确，装饰克制且一致。',
        'image_defaults': {'material': '简洁哑光，温和细腻质感', 'lighting': '柔和左上光源，低对比阴影',
                           'viewpoint': '同系列统一正面或浅三分之四视角', 'edge_treatment': '干净轮廓，避免厚重浮雕',
                           'silhouette': '清楚的独立主体，不附带背景场景', 'detail_level': '投影尺寸下清楚，不依赖微小细节',
                           'optical_padding': '四周约10%留白，避免贴边'}}
}

ART_BRIEF = '''视觉美术合同：design_system.art_direction从research-editorial、technical-product、achievement-story选适用方向，用户参考优先。
design_system用color_roles（background/surface/text/muted/primary/accent）、font_roles_pt（title/body/caption）、image_defaults统一材质、光照、视角、轮廓、边缘与缩小后细节。
这些是可调整的设计起点，不是自动美观保证。明确主焦点、主次尺度、外边距和组内/组间距离；40个独立对象组织为少量语义组，不能碎片化凑数。
每页可用background_color和visual_context，单素材可覆盖，但系列中改变光照/材质/视角需style_override_reason。文本在纯色背景声明text_color/background_color便于对比检查；照片/渐变/透明叠层须渲染后判断。
representative_slides用{cover:slide_id,technical:slide_id,dense:slide_id}选择封面、关键方法/解释、密集证据页。先实际渲染和查看，再推广全篇。
封面以主体和题目形成大小对比；解释页用主证据+原生解读；密集结果页保留坐标、图例、误差和来源空间。配饰、阴影与艺术字不得抢主证据。
逐素材声明aspect为宽:高，并结合box_inches设计完整轮廓与安全留白；默认普通元素1:1、艺术字3:1。主概念承担焦点，辅助图标帮助辨识，ornament只作低对比陪衬。比例不匹配先等比留白或调整构图，不拉伸、不裁切科学证据；原生与来源对象不套用生成素材的材质光照要求。
内容排版用一句论点引导阅读；标题、证据、解释、条件/来源分层，不把整段讲稿塞进正文。比较页对齐基线与尺度，密集页优先拆成概览和关键证据两层，保留条件与不确定性。
美术精修先统一线宽、圆角、边缘和阴影强度；同系列素材按主体可见轮廓而非PNG外框比较光学大小。在实际背景上检查白边、暗边、阴影截断与接触位置，不给每个文本框加阴影，不给证据图添加虚构景深、透视或颜色修饰。
审查逐项记录焦点、层级、对齐留白、色彩与可读性、素材融合、证据可读性；给具体对象与修订，禁止只写高级/美观/通过。'''


def direction(design=None, profile='research'):
    design = design or {}
    key = design.get('art_direction', {'scholarship': 'achievement-story', 'challenge': 'technical-product',
                                     'innovation': 'technical-product'}.get(profile, 'research-editorial'))
    if key not in PRESETS:
        raise ValueError('Unknown art_direction preset; keep custom tokens in design_system')
    from beihang_theme import PROFILES
    primary, accent = {'scholarship': ('991F28', 'C49A4A'), 'challenge': ('0C5892', 'DB8D3C'),
                       'innovation': ('14776B', 'DE9744')}.get(profile, ('174B70', 'DA9253'))
    colors = {'background': '#FFFFFF', 'surface': '#F1F5F9', 'text': '#172638', 'muted': '#526274',
              'primary': '#' + PROFILES.get(design.get('theme_profile'), primary), 'accent': '#' + accent}
    result = {'art_direction': key, **copy.deepcopy(PRESETS[key]), 'color_roles': colors,
              'font_roles_pt': {'title': 32, 'body': 21, 'caption': 13}, 'spacing_inches': [.08, .16, .24, .40]}
    for field in ('color_roles', 'font_roles_pt', 'image_defaults'):
        if field in design:
            if not isinstance(design[field], dict):
                raise ValueError(field + ' must be an object')
            result[field].update(copy.deepcopy(design[field]))
    return result


def asset_context(plan, slide, request, profile='research'):
    resolved = direction(plan.get('design_system', {}), profile)
    context = copy.deepcopy(resolved['image_defaults'])
    context['slide_background'] = slide.get('background_color', resolved['color_roles']['background'])
    context['placement'] = '页面用途：' + str(slide.get('takeaway') or slide.get('title') or slide['slide_id'])
    if request.get('box_inches'):
        context['placement'] += '；目标框（英寸）' + str(request['box_inches'])
    for overrides in (slide.get('visual_context', {}), request.get('visual_context', {})):
        if not isinstance(overrides, dict):
            raise ValueError('visual_context must be an object')
        context.update(copy.deepcopy(overrides))
    return context


def contrast(foreground, background):
    def luminance(color):
        if not isinstance(color, str) or not re.fullmatch(r'#?[0-9a-fA-F]{6}', color):
            raise ValueError('Only explicit six-digit solid RGB colors can be measured')
        rgb = [int(color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(a*b for a,b in zip(rgb, (.2126, .7152, .0722)))
    a,b = sorted((luminance(foreground), luminance(background)))
    return (b+.05)/(a+.05)


def representatives(plan):
    slides = plan['slides']
    by_id = {s['slide_id']: s for s in slides}
    declared = plan.get('representative_slides', {})
    if not isinstance(declared, dict):
        declared = {}  # Older lists remain advisory; derive roles from actual pages.
    cover = next((s for s in slides if s.get('theme_variant') == 'cover'), slides[0])
    content = [s for s in slides if s.get('theme_variant') not in ('cover','section','closing')] or slides
    technical = next((s for s in content if re.search(r'method|process|technical|formula|system', s.get('layout_family',''))), content[0])
    dense = max(content, key=lambda s: len(s.get('content_blocks',[])) + 2*sum(bool(b.get('data_ref') or b.get('source_ref')) for b in s.get('content_blocks',[])))
    chosen = {}
    for role, default in (('cover', cover), ('technical', technical), ('dense', dense)):
        sid = declared.get(role, default['slide_id'])
        if sid not in by_id:
            raise ValueError('Representative page does not exist: ' + str(sid))
        chosen[role] = sid
    return chosen


def audit(plan):
    resolved = direction(plan.get('design_system', {}))
    findings = []
    for slide in plan['slides']:
        for block in slide.get('content_blocks', []):
            if not block.get('text'):
                continue
            foreground = block.get('text_color', resolved['color_roles']['text'])
            background = block.get('background_color', slide.get('background_color', resolved['color_roles']['background']))
            try:
                ratio = contrast(foreground, background)
            except ValueError:
                findings.append({'slide_id':slide['slide_id'], 'object_id':block.get('object_id'), 'code':'contrast_needs_render',
                                 'action':'在真实背景检查渐变、照片或透明叠层；无法从纯色声明测量。'})
                continue
            if ratio < 4.5:
                findings.append({'slide_id':slide['slide_id'], 'object_id':block.get('object_id'), 'code':'low_contrast',
                                 'ratio':round(ratio,2), 'action':'提高文字与背景明暗差，再按投影尺寸检查；4.5为本技能建议预警值。'})
        for request in slide.get('asset_requests', []):
            if request.get('decision') == 'native_or_source':
                continue
            from design_layout import box_valid
            box = request.get('box_inches')
            aspect = str(request.get('aspect', '3:1' if request.get('kind') == 'art_text' else '1:1'))
            try:
                w, h = map(float, aspect.split(':'))
                ratio = w / h if math.isfinite(w) and math.isfinite(h) and w > 0 and h > 0 else None
            except (ValueError, ZeroDivisionError):
                ratio = None
            if ratio is None or not math.isfinite(ratio) or ratio <= 0:
                findings.append({'slide_id':slide['slide_id'], 'object_id':request.get('object_id'), 'code':'invalid_asset_aspect',
                                 'action':'用正数宽:高声明 aspect，核对实际生成端支持的比例。'})
            elif box_valid(box) and max(ratio/(box[2]/box[3]), (box[2]/box[3])/ratio) > 1.8:
                findings.append({'slide_id':slide['slide_id'], 'object_id':request.get('object_id'), 'code':'asset_aspect_fit',
                                 'action':'检查主体轮廓与摆放框；等比留白、调整框或重新构图，不拉伸素材、不裁掉科学证据。'})
            context = asset_context(plan, slide, request)
            drift = [k for k in ('material','lighting','viewpoint') if context.get(k) != resolved['image_defaults'].get(k)]
            if drift and not request.get('style_override_reason') and not slide.get('style_override_reason'):
                findings.append({'slide_id':slide['slide_id'], 'object_id':request.get('object_id'), 'code':'asset_family_drift',
                                 'fields':drift, 'action':'统一同系列材质/光照/视角，或说明内容驱动的变化理由。'})
    return {'schema':'ppt_art_direction_advisory_v1', 'resolved_direction':resolved, 'findings':findings,
            'representative_slides':representatives(plan), 'visual_review_required':True,
            'limits':'Design proposals and solid-color signals only; no rendered appearance or scientific claims certified.'}
