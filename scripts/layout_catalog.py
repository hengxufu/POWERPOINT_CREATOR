"""Content-aware editable layout recipes in inches, not finished slide images."""
import argparse
import json
from pathlib import Path

LAYOUTS = {
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
