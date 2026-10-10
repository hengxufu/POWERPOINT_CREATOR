#!/usr/bin/env python3
"""Initialize a GPT-6 planned, element-composed research PPT workspace."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DIRECTORIES = (
    "planning",
    "sources",
    "asset-specs",
    "asset-jobs",
    "assets/accepted",
    "src",
    "build",
    "renders",
    "qa",
)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--scenario", default="科研工作汇报")
    parser.add_argument("--audience", default="课题组与同行专家")
    parser.add_argument("--duration-min", type=int, default=20)
    parser.add_argument("--project-root", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = args.out.resolve()
    project_root = args.project_root.resolve()
    if out.exists():
        raise SystemExit(f"Refusing to initialize an existing path: {out}")
    if args.duration_min <= 0:
        raise SystemExit("--duration-min must be positive")

    out.mkdir(parents=True)
    for relative in DIRECTORIES:
        (out / relative).mkdir(parents=True)

    created_at = datetime.now(timezone.utc).isoformat()
    session = {
        "schema": "research_ppt_session_v1",
        "title": args.title,
        "scenario": args.scenario,
        "audience": args.audience,
        "duration_min": args.duration_min,
        "project_root": str(project_root),
        "created_at": created_at,
        "planning_owner": "chatgpt-web:gpt-6-astra",
        "image_asset_owner": "chatgpt-web:gpt-image-2.5-sunburst",
        "assembly_owner": "codex-local-script",
        "connection_status": "pending",
    }
    write_json(out / "session.json", session)

    plan_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "GPT-6 research deck plan",
        "type": "object",
        "required": ["deck_thesis", "audience", "slides", "evidence_gaps", "review_checklist"],
        "properties": {
            "deck_thesis": {"type": "string"},
            "audience": {"type": "string"},
            "slides": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["slide_number", "title", "takeaway", "content_blocks", "speaker_notes", "asset_requests"],
                    "properties": {
                        "slide_number": {"type": "integer", "minimum": 1},
                        "title": {"type": "string"},
                        "takeaway": {"type": "string"},
                        "content_blocks": {"type": "array", "items": {"type": "object"}},
                        "speaker_notes": {"type": "string"},
                        "evidence": {"type": "array", "items": {"type": "object"}},
                        "asset_requests": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "purpose", "single_subject_prompt"],
                                "properties": {
                                    "kind": {"enum": ["ornament", "concept", "art_text", "icon", "cutout"]},
                                    "purpose": {"type": "string"},
                                    "single_subject_prompt": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
            "evidence_gaps": {"type": "array", "items": {"type": "string"}},
            "review_checklist": {"type": "array", "items": {"type": "string"}},
        },
    }
    write_json(out / "planning" / "deck_plan.schema.json", plan_schema)

    task_packet = f"""# GPT-6 网页端规划任务包

请为《{args.title}》制定中文科研汇报的结构化规划。

- 场景：{args.scenario}
- 受众：{args.audience}
- 时长：{args.duration_min} 分钟
- 输出必须符合 `deck_plan.schema.json`，保存为 `deck_plan.json`。
- 你负责叙事结构、逐页论点、信息密度、讲稿、证据缺口和全稿审查。
- 不生成 PPTX，不生成任何整页幻灯片图像，也不输出把标题、正文、页脚烘焙在一起的画面。
- 图片需求只能列为独立小元素；每条仅一个主体，kind 仅限 ornament、concept、art_text、icon、cutout。
- 图表、表格、公式、实验结果、流程节点、连接线和正文必须由本地脚本原生构建，不能交给图像模型。
- 不得把多个元素拼成一张图后再裁切。

完成初稿后，再以严格评审者身份检查：是否有证据越界、逻辑跳跃、重复页、信息密度失衡、公式未解释、视觉请求不适合生成等问题。
"""
    (out / "planning" / "gpt6_task_packet.md").write_text(task_packet, encoding="utf-8")

    manifest = {
        "schema": "ppt_element_manifest_v1",
        "canvas": {"width_in": 13.333, "height_in": 7.5},
        "max_generated_asset_area_fraction": 0.55,
        "native_objects": {"text": True, "charts": True, "tables": True, "formulas": True},
        "elements": [],
    }
    write_json(out / "assets" / "asset_manifest.json", manifest)

    contract = {
        "schema": "ppt_composition_contract_v1",
        "generated_asset_policy": {
            "one_independent_element_per_job": True,
            "allowed_kinds": ["ornament", "concept", "art_text", "icon", "cutout"],
            "forbidden": [
                "full_slide",
                "slide_screenshot",
                "complete_infographic",
                "chart_or_table_as_image",
                "formula_as_image",
                "experimental_result_as_image",
                "flattened_title_body_footer",
                "multi_element_collage_for_cropping",
            ],
        },
        "local_script_owns": [
            "titles_and_body_text",
            "citations_and_page_numbers",
            "charts_tables_and_formulas",
            "nodes_and_connectors",
            "layout_and_picture_insertion",
            "rendering_and_quality_assurance",
        ],
    }
    write_json(out / "composition_contract.json", contract)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
