"""Prepare a web planning packet or turn an observed web plan into individual jobs.

No browser calls occur here. Actual submission/download uses the browser workflow.
"""
import argparse
import json
import re
from pathlib import Path
from types import SimpleNamespace
from asset_job import prepare
from layout_catalog import LAYOUTS
from design_layout import DESIGN_BRIEF
from experimental_figures import FIGURE_BRIEF
from beihang_theme import contract as theme_contract, PROFILES as THEME_PROFILES

PROFILES = {
    'scholarship': {'name': '国奖答辩·成长与证据', 'palette': '深红 #991F28、暖金 #C49A4A、白色',
                    'arc': '个人定位→学业基础→科研/竞赛贡献→实践责任→成长与展望',
                    'layouts': ['portrait-hero', 'achievement-metrics', 'growth-timeline', 'photo-evidence', 'honor-gallery'],
                    'assets': '独立章节字标、单枚主题图标、轻薄弧形装饰；个人照和证书必须来自真实材料'},
    'research': {'name': '科研汇报·证据与结构', 'palette': '深蓝 #174B70、青色 #008E98、少量橙色 #DA9253',
                 'arc': '问题与缺口→研究假设→方法设计→关键证据→贡献与边界→后续验证',
                 'layouts': ['question-figure', 'method-process', 'figure-analysis', 'paired-comparison', 'evidence-table'],
                 'assets': '独立研究对象概念插画、设备概念或方法图标；数据图与节点关系原生绘制'},
    'challenge': {'name': '挑战杯·技术与验证', 'palette': '科技蓝 #0C5892、青色 #00A9B0、橙金 #DB8D3C',
                  'arc': '现实问题→原创方案→核心技术→实验/实践验证→同口径比较→应用价值',
                  'layouts': ['product-hero', 'problem-solution', 'technical-layers', 'validation-dashboard', 'comparison-matrix'],
                  'assets': '单一产品概念、独立部件、章节字标、单枚应用图标；按大挑/创业计划类别调整'},
    'innovation': {'name': '创新创业·产品与落地', 'palette': '深绿 #14776B、暖橙 #DE9744、深蓝灰 #304C69',
                   'arc': '用户痛点→产品→技术壁垒→市场与竞品→验证/客户→商业模式→团队与里程碑',
                   'layouts': ['product-hero', 'user-scenario', 'comparison-matrix', 'traction-chart', 'business-flow', 'roadmap'],
                   'assets': '单一产品概念、品牌字标、单枚用户场景图标；真实订单、客户、收入不能生成或虚构'},
}


def packet(args):
    brief = args.brief.read_text(encoding='utf-8')
    if getattr(args, 'materials', None):
        from material_handoff import select, load, inside
        from bridge_session import safe_root
        if not getattr(args, 'project_root', None):
            raise ValueError('--project-root required with --materials')
        root = safe_root(args.project_root)
        inside(root, args.out)
        selection = load(inside(root, args.materials))
        select(root, selection, 'gpt')
        select(root, selection, 'image')
    profile = PROFILES[args.profile]
    theme_profile = getattr(args, 'theme_profile', 'beihang-blue')
    theme = theme_contract(theme_profile) if theme_profile != 'none' else {'theme_profile': 'none'}
    palette = ('主色 #' + THEME_PROFILES[theme_profile] + '、白色、深灰正文；科学图配色保留语义') if theme_profile != 'none' else profile['palette']
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    payload = {'requested_profile': args.profile, **profile, 'brief': brief,
               'theme_contract': theme, 'effective_palette': palette,
               'web_response_received': False, 'observed_model': None}
    (args.out / 'planning-input.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    prompt = f'''请实际规划一份中国高校{profile['name']}可编辑PPT。先分析材料，再逐页规划，再审查。
材料：\n{brief}\n
设计候选：{palette}。用户模板优先。叙事参考：{profile['arc']}。
全篇主题合同：{json.dumps(theme, ensure_ascii=False)}。
候选构图：{', '.join(profile['layouts'])}；按内容选择，避免连续重复，不能全篇三卡片。
局部素材候选：{profile['assets']}。
请输出一个JSON对象：deck_thesis、audience、evidence_gaps、review_checklist、slides。
每页含slide_number、slide_id、title、takeaway、layout_family、visual_rationale、content_blocks、speaker_notes、evidence、asset_requests。
content_blocks每块给出具体text或data_ref/source_ref，并标明原生text/chart/table/process及建议box_inches。
每条asset_request给request_id、asset_id、object_id、kind、purpose、single_subject_prompt，默认decision=generate_web。
kind只能ornament/concept/art_text/icon/cutout；艺术字给exact_text。每条只有一个独立元素，无页面、正文、数据图、公式或拼贴。
版式坐标采用13.333×7.5英寸；主标题、中文说明、数据标注均原生，中文微软雅黑，西文Times New Roman。
预留证据图、概念元素、注释与引文的位置。不要用虚构事实填空。真实照片和证书不由图像模型生成。
请特别展开封面、最关键的技术/经历页和最密集结果页；指出如何将参考风格转化为本项目的构图。
额外输出design_system（背景、颜色角色、字号层级、间距、线条、材质与光照）和representative_slides（上述三类代表页）。
每页增加visual_hierarchy（primary/secondary/annotation）、composition_notes和native_details；说明一个主焦点、证据与解读的关系、原生标注/连接线/局部放大的具体用途。复杂度来自内容关系，不靠无意义堆图。
每条生成请求补充visual_context（slide_background、lighting、material、placement、avoid），并给建议box_inches；图标不混用线描和写实材质，艺术字只用于短章节词并另保留原生语义文字。
给出全篇视觉节奏：封面、章节、解释、密集证据、结论之间如何切换；连续相同构图需说明理由。必要时分两页，不能为复杂程度牺牲字号和证据可读性。
每一页至少40个独立PPT元素，封面、章节页、结尾页同样适用。每页提供element_budget（native_objects、generated_objects、total），规划真实独立对象而不是拆分文字段落或表格单元格凑数。总数不足40时，将缺口逐项列为网页版单元素asset_requests；每条给出具体主体、用途、布局位置和风格，逐个生成后由脚本插入。图表、表格、公式与科学标注保持原生，补充图片不能代替证据。按此密度规划留白与层级，先检查代表页可读性，再推广全篇。
遵循材料中的theme_contract；未明确其他学校时，本用户默认beihang-blue。全篇贯穿真实北航校徽+中英校名组合、原生校名署名、章节文字与页码四类对象。design_system写theme_profile及recurring_elements，每页写section（1到24字的具体章节名）及theme_variant（cover/section/content/closing）。右上角x=.79W,y=.025H,w=.185W,h=.075H和底部y=.925H以下为固定身份预留区，正文避开。封面/章节/结尾可复用本地校园照片；正文克制。真实校徽/校名/校园照片属于已有源素材，不列为generate_web，不用生成通用航天图标代替学校身份，不猜院系归属。不把模板观察颜色称为官方VI。主题固定但每页证据构图仍需变化；四个主题对象只计四个，不复制标志凑40。
以严格评审者身份检查材料充分性、内容空洞、图文比例、布局重复、证据与装饰混淆。
仅提供规划和批评，不执行shell、不写本地源、不生成整页图。
'''
    (args.out / 'gpt6-task-packet.md').write_text(prompt, encoding='utf-8')
    (args.out / 'layout-recipes.json').write_text(json.dumps(LAYOUTS, ensure_ascii=False, indent=2), encoding='utf-8')
    with (args.out / 'gpt6-task-packet.md').open('a', encoding='utf-8') as handle:
        handle.write('\n元素设计与排版合同：\n' + DESIGN_BRIEF)
        handle.write('\n实验数据图合同：\n' + FIGURE_BRIEF)
        handle.write('\n以下是可调整的原生构图起点，按真实内容选取并修订，不能照搬占位框：\n' + json.dumps(LAYOUTS, ensure_ascii=False))
        handle.write('\n资料合同：先确认正文资料与附件可读取。每页evidence引用资料ID和页码/图号；每个asset_request给material_ids，选取Image必需的主体/风格参考。文件路径不是文件内容；缺资料先报告，不推断。\n')
    if getattr(args, 'materials', None):
        from material_handoff import prepare as prepare_materials
        if not getattr(args, 'project_root', None):
            raise ValueError('--project-root required with --materials')
        prepare_materials(args.project_root, args.materials, 'gpt', args.out / 'gpt6-task-packet.md',
                          args.out / 'gpt-materials', 'gpt-planning')
        image_brief = args.out / 'image-planning-context.md'
        image_brief.write_text('本项目Image共用资料。逐元素任务另补主体、用途、准确文字、尺寸、背景、构图与科学边界。只生成单个局部元素，不生成整页、图表或实验结果。', encoding='utf-8')
        prepare_materials(args.project_root, args.materials, 'image', image_brief,
                          args.out / 'image-materials', 'image-planning-context')
    print(args.out)


def jobs(args):
    plan = json.loads(args.plan.read_text(encoding='utf-8-sig'))
    profile = PROFILES[args.profile]
    theme_profile = plan.get('design_system', {}).get('theme_profile')
    palette = ('主色 #' + THEME_PROFILES[theme_profile] + '、白色、深灰；仅次级概念与装饰') if theme_profile in THEME_PROFILES else profile['palette']
    requests = []
    used = set()
    for slide in plan['slides']:
        for request in slide.get('asset_requests', []):
            if request.get('decision', 'generate_web') == 'native_or_source':
                continue
            identifier = request['request_id']
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', identifier) or identifier in used:
                raise ValueError('Unique filename-safe request_id required')
            used.add(identifier)
            spec = {'asset_id': request.get('asset_id', identifier), 'kind': request['kind'],
                    'element': request['single_subject_prompt'], 'slide_id': slide['slide_id'],
                    'object_id': request['object_id'], 'palette': request.get('palette', palette),
                    'transparent': True, 'min_width': 1024, 'min_height': 1024,
                    'aspect': request.get('aspect', '3:1' if request['kind'] == 'art_text' else '1:1'),
                    'style': request.get('style', profile['name'] + '；清晰、精致、统一材质与光照'),
                    'visual_context': request.get('visual_context', {})}
            if 'material_ids' in request:
                spec['material_ids'] = request['material_ids']
            if request['kind'] == 'art_text':
                spec['exact_text'] = request['exact_text']
                spec['min_height'] = 384
            # Validate everything before creating jobs, so invalid plans leave no half-prepared queue.
            from asset_job import prompt
            prompt(spec)
            requests.append((identifier, slide['slide_number'], spec))
    if getattr(args, 'materials', None):
        from material_handoff import select, load, inside
        from bridge_session import safe_root
        if not getattr(args, 'project_root', None):
            raise ValueError('--project-root required with --materials')
        root = safe_root(args.project_root)
        inside(root, args.out)
        selection = load(inside(root, args.materials))
        select(root, selection, 'gpt')
        for _, _, spec in requests:
            select(root, selection, 'image', spec.get('material_ids'))
    if args.out.exists():
        raise FileExistsError('Use a new queue version; never overwrite dispatched jobs')
    args.out.mkdir(parents=True)
    queue = []
    for identifier, number, spec in requests:
        spec_path = args.out / (identifier + '.spec.json')
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
        job_dir = args.out / identifier
        prepare(SimpleNamespace(spec=spec_path, job=job_dir, materials=getattr(args, 'materials', None),
                                project_root=getattr(args, 'project_root', None)))
        queue.append({'request_id': identifier, 'slide_number': number, 'job_dir': identifier, 'state': 'prepared_not_submitted'})
    (args.out / 'queue.json').write_text(json.dumps({'schema': 'web_element_queue_v1', 'jobs': queue}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'prepared_jobs': len(queue), 'actual_web_submissions': 0}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('packet')
    command.add_argument('--brief', type=Path, required=True)
    command.add_argument('--theme-profile', choices=[*THEME_PROFILES, 'none'], default='beihang-blue')
    command.set_defaults(func=packet)
    command = commands.add_parser('jobs')
    command.add_argument('--plan', type=Path, required=True)
    command.set_defaults(func=jobs)
    for command in commands.choices.values():
        command.add_argument('--profile', choices=PROFILES, required=True)
        command.add_argument('--out', type=Path, required=True)
        command.add_argument('--materials', type=Path, help='Reviewed material selection for both GPT and Image')
        command.add_argument('--project-root', type=Path)
    args = parser.parse_args()
    args.func(args)
