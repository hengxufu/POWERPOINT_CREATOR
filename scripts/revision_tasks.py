"""Build actionable plan-review tasks; never amend content or certify appearance."""
import hashlib
import json


def request_signature(plan, slide, request):
    design = plan.get('design_system',{})
    value = {'design_system':{k:design[k] for k in ('theme_profile','art_direction','image_defaults','color_roles') if k in design}, 'slide_id':slide['slide_id'],
             'background_color':slide.get('background_color'), 'visual_context':slide.get('visual_context',{}),
             'request':request}
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()


def reviewed_choice(choice, workspace, directory, plan, slide, request, spec):
    """Check a deliberate current-plan reuse attestation, not the truth of its review."""
    from material_handoff import inside
    try:
        return (inside(workspace,choice['job_dir']) == directory.resolve() and
                bool(str(choice.get('reason','')).strip()) and
                choice.get('request_signature') == request_signature(plan,slide,request) and
                choice.get('spec_sha256') == hashlib.sha256(json.dumps(spec,sort_keys=True).encode('utf-8')).hexdigest())
    except (KeyError,TypeError,ValueError,OSError):
        return False


CONTENT_ACTIONS = {
    'thin_explanation':'对照资料补足证据如何支持本页论点；无需为消除字数信号填充套话。',
    'no_evidence_locator':'定位具体材料ID与页码/图号；无法支撑时改为假设或记录真实缺口。',
    'no_speaker_notes':'补充从证据到结论的解释及下一页过渡，不新增无来源事实。',
}
LAYOUT_ACTIONS = {
    'text_pressure':'核对实际文本框参数，优先重组、扩大解释区或递进拆页；保留条件、单位、不确定性，再渲染查看。',
    'small_text':'先重新分组或拆页，再校验实际投影尺寸；不直接把所有文字统一放大。',
    'overlap':'查看相交对象；移动遮挡项或说明必要叠层，再用真实渲染确认。',
    'tight_spacing':'按信息分组调整声明间距，保留组内紧、组间松的层次。',
    'detached_caption':'把图注移近对应证据，必要时使用清楚的原生引线并实际查看。',
    'repeated_layout':'核对是否服务同口径比较；否则改变证据组织方式，而非随机换装饰。',
    'reading_order':'核对证据与解释的顺序，只包含有意义的信息对象，排除装饰。',
    'decoration_budget':'减少与证据竞争的装饰面积；不删真实证据或用隐藏对象补数量。',
}


def build(plan, content, layout, art):
    tasks = []
    pages = {s['slide_id']:(s.get('slide_number',i),s.get('title','')) for i,s in enumerate(plan['slides'],1)}
    def add(sid,category,code,objects,priority,observation,action):
        identity = [sid,category,code,objects,observation]
        task_id = hashlib.sha256(json.dumps(identity,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16]
        number,title = pages.get(sid,(0,''))
        tasks.append({'task_id':task_id,'slide_id':sid,'slide_number':number,'title':title,'objects':objects,
                      'category':category,'code':code,'priority':priority,'observation':observation,
                      'action':action,'status':'needs_review'})
    for page in content.get('slides',[]):
        for signal in page.get('review_signals',[]):
            code = signal.split(':',1)[0]
            add(page['slide_id'],'content',code,[],0 if code=='no_evidence_locator' else 2,
                signal,CONTENT_ACTIONS.get(code,'对照实际资料复核本页内容。'))
    for finding in layout.get('findings',[]):
        code,severity = finding['code'],finding['severity']
        add(finding['slide_id'],'layout',code,finding.get('objects',[]),1 if severity=='error' else 4 if severity=='info' else 2,
            finding['message'],LAYOUT_ACTIONS.get(code,finding['message']))
    for finding in art.get('findings',[]):
        add(finding['slide_id'],'art',finding['code'],[finding['object_id']] if finding.get('object_id') else [],
            2 if finding['code']=='low_contrast' else 3,finding['code'],finding['action'])
    unique = {t['task_id']:t for t in tasks}
    tasks = sorted(unique.values(),key=lambda t:(t['priority'],t['slide_number'],t['category'],t['code'],t['task_id']))
    return {'schema':'ppt_revision_tasks_v1','tasks':tasks,'count':len(tasks),'automatic_fixes':0,
            'limits':'Current-plan signals only. Disappearing signals are not proof of factual or visual correctness; inspect actual sources and renders.'}


def markdown(report):
    def plain(value):
        return str(value).replace('\r',' ').replace('\n',' ').replace('<','&lt;').replace('>','&gt;')
    lines=['# 当前规划修订任务','', '按优先级处理；每项默认待复核。消除信号不等于实际视觉或事实验收。','']
    for task in report['tasks']:
        lines += [f"## P{task['priority']} · 第{task['slide_number']}页 · {plain(task['title'])}",'',
                  f"- 任务：{task['task_id']} / {task['category']} / {task['code']}",
                  '- 对象：'+plain(', '.join(task['objects']) or '整页'),
                  '- 观察：'+plain(task['observation']),'- 修订：'+plain(task['action']),'']
    if not report['tasks']:
        lines += ['本次启发式审计未产生任务；仍需核对真实资料并查看实际渲染。','']
    return '\n'.join(lines)
