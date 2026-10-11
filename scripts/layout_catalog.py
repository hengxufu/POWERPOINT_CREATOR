"""Content-aware editable layout recipes in inches, not finished slide images."""
import argparse
import json
from pathlib import Path

LAYOUTS = {
    'evidence-zoom': {'best_for': '整体证据与局部细节联合解释', 'zones': {'source_figure': [.7, 1.85, 7.4, 4.75], 'detail_crop': [8.5, 1.85, 4.1, 2.6], 'native_interpretation': [8.5, 4.75, 4.1, 1.65]}, 'assembly': '保留整体图；放大区域来自真实源并标明对应位置，原生框线连接；禁止生成科学细节'},
    'technical-layers': {'best_for': '系统层级与模块协作', 'zones': {'native_architecture': [.7, 1.9, 8.2, 4.65], 'single_component': [9.35, 1.9, 3.25, 2.15], 'interface_conditions': [9.35, 4.4, 3.25, 2.1]}, 'assembly': '原生分层底板、模块、接口与箭头；颜色编码层级，独立部件插画只辅助识别'},
    'validation-dashboard': {'best_for': '同一论点的多项验证', 'zones': {'main_native_chart': [.7, 1.9, 7.1, 4.65], 'secondary_evidence': [8.25, 1.9, 4.35, 2.8], 'conditions_and_limits': [8.25, 5, 4.35, 1.5]}, 'assembly': '主图占优，副证据与条件分区；统一变量颜色与单位，不能把多个小图压成不可读仪表盘'},
    'problem-solution': {'best_for': '现实痛点到方案作用的解释', 'zones': {'real_context': [.7, 1.9, 4.15, 3.7], 'native_transition': [5.15, 2.5, 2.1, 2.5], 'solution_object': [7.6, 1.9, 5, 3.7], 'evidence_boundary': [.7, 5.95, 11.9, .65]}, 'assembly': '真实场景与单一方案主体并置，中间原生因果或作用链；区分已验证作用与设计预期'},
    'achievement-metrics': {'best_for': '个人贡献与真实成果证据', 'zones': {'main_contribution': [.7, 1.9, 6.2, 1.4], 'real_evidence': [.7, 3.65, 6.2, 2.8], 'native_metrics': [7.4, 1.9, 5.2, 2], 'role_and_scope': [7.4, 4.3, 5.2, 2.1]}, 'assembly': '贡献文字、真实证据和同口径数字互相支持；标清个人角色，不把团队成果全部算作个人'},
    'honor-gallery': {'best_for': '少量代表性荣誉与成果', 'zones': {'primary_real_certificate': [.7, 1.9, 6.4, 4.5], 'secondary_real_evidence': [7.55, 1.9, 5.05, 2.5], 'meaning_and_role': [7.55, 4.75, 5.05, 1.65]}, 'assembly': '主证据明显大于副证据，提取可读原生信息；避免缩略证书墙'},
    'user-scenario': {'best_for': '用户任务与产品使用场景', 'zones': {'real_scenario': [.7, 1.9, 7.5, 4.5], 'native_task_sequence': [8.65, 1.9, 3.95, 2.3], 'verified_value': [8.65, 4.65, 3.95, 1.75]}, 'assembly': '场景与任务序列对应；概念演示明确标记，不伪造客户照片或使用记录'},
    'business-flow': {'best_for': '价值交付与业务关系', 'zones': {'native_value_flow': [.7, 2, 11.9, 2.65], 'assumptions': [.7, 5.05, 5.7, 1.35], 'verified_conditions': [6.85, 5.05, 5.75, 1.35]}, 'assembly': '关系、资金与交付用不同原生线型并给图例；假设与已验证条件分列'},
    'roadmap': {'best_for': '阶段成果与下一步验证', 'zones': {'native_stage_axis': [.7, 2, 11.9, 1.2], 'stage_deliverables': [.7, 3.65, 11.9, 1.65], 'risks_and_next_test': [.7, 5.7, 11.9, .7]}, 'assembly': '时间轴配交付物和验证标准；已完成与计划用不同填充，不能只列日期口号'},
    'question-figure': {'best_for': '研究问题、缺口与观测对象', 'zones': {'specific_question': [.7, 1.9, 4.7, 1.7], 'gap_and_hypothesis': [.7, 4, 4.7, 2.4], 'real_or_concept_subject': [5.9, 1.9, 6.7, 4.5]}, 'assembly': '以问题组织对象与证据；概念插画标明示意，原生标注仅表达来源支持的关系'},
    'evidence-table': {'best_for': '多项研究证据的对应关系', 'zones': {'native_evidence_table': [.7, 1.9, 9.1, 4.5], 'native_synthesis': [10.15, 1.9, 2.45, 4.5]}, 'assembly': '表格保留条件、结果、来源与边界；右侧只提炼表中可支持的结论'},
    'portrait-hero': {'best_for': '个人定位/国奖开场', 'zones': {'headline': [.7, 1.4, 6.2, 1.5], 'story': [.7, 3.2, 6.2, 1.8], 'real_portrait': [7.7, 1.1, 4.9, 5.3]}},
    'product-hero': {'best_for': '产品与技术开场', 'zones': {'headline': [.7, 1.5, 6.1, 1.5], 'promise': [.7, 3.3, 5.8, 1.3], 'single_product': [7.4, 1.4, 5.1, 4.8], 'evidence_note': [.7, 5.8, 6, .6]}},
    'figure-analysis': {'best_for': '关键结果与来源图', 'zones': {'evidence': [.65, 1.9, 8.1, 4.65], 'interpretation': [9.1, 1.9, 3.55, 4.65]}},
    'paired-comparison': {'best_for': '同条件比较', 'zones': {'left_evidence': [.65, 2, 5.65, 3.5], 'right_evidence': [7, 2, 5.65, 3.5], 'shared_interpretation': [.65, 5.85, 12, .7]}},
    'comparison-matrix': {'best_for': '竞品/方案维度对比', 'zones': {'native_table': [.7, 2, 11.9, 3.9], 'boundary': [.7, 6.05, 11.9, .5]}},
    'method-process': {'best_for': '研究设计与验证顺序', 'zones': {'native_nodes_and_lines': [.7, 2.1, 11.9, 2.3], 'design_conditions': [.7, 4.8, 7.3, 1.6], 'local_concept': [8.6, 4.6, 3.4, 1.8]}},
    'growth-timeline': {'best_for': '个人成长与项目里程碑', 'zones': {'native_timeline': [.7, 2.2, 11.9, 1.3], 'evidence_photo': [.7, 4, 4.5, 2.3], 'milestone_explanation': [5.6, 4, 7, 2.3]}},
    'photo-evidence': {'best_for': '真实实践与实验场景', 'zones': {'real_photo': [6.7, 1.8, 5.9, 4.7], 'claim': [.7, 1.9, 5.5, 1.2], 'specific_contribution': [.7, 3.4, 5.5, 2.7]}},
    'traction-chart': {'best_for': '增长/趋势与落地', 'zones': {'native_chart': [.7, 2, 8.4, 4.5], 'metric_explanation': [9.5, 2, 3.1, 4.5]}},
    'section-wordmark': {'best_for': '章节切换', 'zones': {'native_section_title': [2.1, 2.3, 9.1, 1.2], 'optional_art_text': [4.4, 4, 4.5, 1.2], 'single_ornament': [9.8, .7, 2.6, 1.5]}},
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps({'canvas_inches': [13.333, 7.5], 'shared_title_box': [.65, .4, 12, 1],
                                    'source_footer_box': [.65, 6.9, 11.8, .3], 'recipes': LAYOUTS,
                                    'limits': 'Starting geometry only; adjust after rendering real content.'}, ensure_ascii=False, indent=2), encoding='utf-8')
