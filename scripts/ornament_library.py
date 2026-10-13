"""Prepare source-informed individual ornament jobs; never claim web submission."""
import argparse
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
from asset_job import prepare, prompt

RECIPES = {
    'cover': {'box_inches': [8.4, 1.4, 4.2, 4.7], 'hierarchy': '单一大主体偏右，左侧标题与问题原生；不做满版背景', 'source': '模版立体(2).pptx 第3页半幅主视觉结构'},
    'section': {'box_inches': [9.1, 2.0, 3.3, 3.6], 'hierarchy': '大章节号与较小配饰形成尺度差，给章节标题留白', 'source': '模版黄色.pptx 第3页章节尺度对比'},
    'method': {'box_inches': [10.7, 4.8, 1.1, 1.1], 'hierarchy': '局部概念图标辅助节点识别；节点连线、公式保持原生', 'source': '模版绿色.pptx 第8页左图右侧解读结构'},
    'result': {'box_inches': [11.7, 5.7, .65, .65], 'hierarchy': '证据图是主角，配饰小且低对比，只放解读外侧', 'source': '北京航空航天大学工作汇报ppt模板蓝(2).pptx 第8页图标与解读成组'},
    'comparison': {'box_inches': [11.1, 1.5, .8, .8], 'hierarchy': '同口径证据等尺度对齐；不在对比两侧使用大小不同的装饰', 'source': '模版绿色.pptx 第12页同尺度三组结构'},
    'closing': {'box_inches': [9.1, 2.0, 3.3, 3.6], 'hierarchy': '复现封面同一视觉母题的小尺度版本，不额外引入新材质', 'source': '北京航空航天大学工作汇报ppt模板蓝(2).pptx 第12页留白章节结构'},
}

SUBJECTS = [
    ('wing-foil', '钛蓝机翼曲面', 'ornament', '一枚独立的连续钛蓝机翼曲面雕塑，流线型薄壳、优雅扭转，只是一件抽象曲面，不带飞机机身或底座', '3:2', ['cover','section','closing']),
    ('orbital-arc', '开口轨道弧', 'ornament', '一枚独立连续的开口椭圆轨道弧雕塑，单根扁平钛蓝带材、非闭环，弧线有轻微立体透视，不带球体、星星或航天器', '1:1', ['cover','section','closing']),
    ('satellite', '卫星姿态概念体', 'concept', '一个完整独立的微型卫星概念模型，蓝银一体机身和连接其上的简洁太阳翼，三分之四视角，无轨道、坐标轴、粒子或外部场景', '1:1', ['cover','method']),
    ('lens-ring', '半透明镜头环', 'ornament', '一枚独立的半透明冰蓝光学环，薄壁环形玻璃、内缘一圈微弱银色反射，无镜头机身、光束或附加零件', '1:1', ['section','method']),
    ('ginkgo-leaf', '单枚银杏叶', 'ornament', '一枚独立完整的银杏叶，扇形脉络清晰、微微卷曲，钛蓝与银白的艺术材质，仅一片叶和连接叶柄，无树枝、叶堆或建筑', '1:1', ['section','closing']),
    ('optical-prism', '光学三棱镜', 'concept', '一枚独立的精密光学三棱镜，冰蓝透明玻璃、柔和边缘高光，无彩虹光束、底座或其他物体', '1:1', ['method','comparison']),
    ('sensor-module', '视觉传感器概念体', 'concept', '一个独立的蓝银视觉传感器概念模块，极简矩形外壳与嵌入式单镜头一体连接，三分之四视角，无品牌、线缆或背景设备', '1:1', ['method']),
    ('single-lens', '单枚非球面镜片', 'concept', '一枚独立完整的非球面光学镜片，冰蓝透明材质、轻微倾斜，细腻曲率反射，无镜架、光束或第二片镜片', '1:1', ['method','result']),
    ('folded-ribbon', '连续折叠飘带', 'ornament', '一条独立连续的钛蓝窄飘带，只有一次柔和折叠、两端完整、轮廓收敛，非蝴蝶结，无粒子或多个带片', '3:2', ['section','closing']),
    ('structural-hexagon', '蜂窝结构单元', 'icon', '一个独立完整的中空六边形航空结构单元，薄壁钛蓝金属、精密倒角，只有一个六边形，不是蜂窝阵列或多个单元', '1:1', ['method','comparison']),
    ('aero-vane', '单枚气动叶片', 'ornament', '一枚独立完整的航空发动机气动叶片概念雕塑，蓝银金属、细长扭转翼型，没有叶轮、底座或第二枚叶片', '3:2', ['section','closing']),
    ('calibration-sphere', '哑光标定球概念体', 'concept', '一枚独立完整的哑光钛蓝精密球体概念模型，柔和左上高光、轮廓干净，无网格、刻度、数字、坐标轴或支架', '1:1', ['method','result']),
]


def catalog():
    return {'schema': 'beihang_ornament_proposals_v1', 'origin': 'codex_local_proposals_from_template_object_layouts',
            'web_planning_received': False, 'image_generation_completed': False,
            'sample_ids': ['wing-foil', 'orbital-arc', 'lens-ring'],
            'design_system': {'palette': '主色#005BAB、冰蓝#C8E9FF、少量银白；白色页面',
                              'lighting': '左上大面积柔光、克制的接触阴影、不加光晕',
                              'material': '高级工业设计质感；钛蓝金属/光学玻璃，同一页面最多一种主材质'},
            'layout_recipes': RECIPES,
            'elements': [{'id': identifier, 'name': name, 'kind': kind, 'single_subject_prompt': subject,
                          'aspect': aspect, 'use_cases': cases} for identifier,name,kind,subject,aspect,cases in SUBJECTS]}


def build(out, selected=None):
    out = Path(out)
    if out.exists():
        raise FileExistsError('Use a new library version; never overwrite dispatched jobs')
    data = catalog()
    chosen = selected or data['sample_ids']
    if len(chosen) != len(set(chosen)) or set(chosen) - {item['id'] for item in data['elements']}:
        raise ValueError('Use unique known element ids')
    specs = []
    for item in data['elements']:
        if item['id'] not in chosen:
            continue
        style = data['design_system']
        spec = {'asset_id': item['id']+'-v1', 'kind': item['kind'], 'element': item['single_subject_prompt'],
                'slide_id': 'ornament-library', 'object_id': item['id'], 'palette': style['palette'],
                'style': '克制的航空航天工业美学；非霓虹、非塑料玩具、非厚重光晕', 'aspect': item['aspect'],
                'transparent': True, 'min_width': 1024, 'min_height': 1024,
                'visual_context': {'slide_background': '白色；不得把白色背景画进透明原图',
                                   'lighting': style['lighting'], 'material': style['material'],
                                   'viewpoint': '系列统一轻微三分之四视角；环形主体保持轮廓清晰',
                                   'silhouette': '完整单一主体；缩小到目标摆放尺寸仍可辨识，不靠微粒填充',
                                   'edge_treatment': '克制精密倒角、干净alpha边缘；无白边或光晕',
                                   'detail_level': '细节服务轮廓，避免缩小后成为噪点的微刻纹',
                                   'optical_padding': '四周约10%安全留白；后续按实际主体检查视觉重心，不拉伸',
                                   'placement': '独立小元素；按本库对应recipe后续选择位置，不能画出PPT布局',
                                   'avoid': '不生成校徽校名、真实校园建筑、数据图、公式或科研结果；不做拼贴，不复制主题标志凑数'}}
        prompt(spec)
        specs.append((item['id'], spec))
    out.mkdir(parents=True)
    (out / 'catalog.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    jobs = []
    for identifier, spec in specs:
        path = out / (identifier + '.spec.json')
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
        prepare(SimpleNamespace(spec=path, job=out / identifier))
        jobs.append({'request_id': identifier, 'job_dir': identifier, 'state': 'prepared_not_submitted'})
    (out / 'queue.json').write_text(json.dumps({'schema':'web_element_queue_v1','jobs':jobs}, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'proposals': len(data['elements']), 'prepared_jobs': len(jobs), 'actual_web_submissions': 0, 'out': str(out)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--ids', nargs='+')
    args = parser.parse_args()
    print(json.dumps(build(args.out, args.ids), ensure_ascii=False))
