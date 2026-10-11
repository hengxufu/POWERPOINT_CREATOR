"""Import an observed assistant reply; never submit prompts or invent web evidence."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def validate(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get('slides'), list) or not plan['slides']:
        raise ValueError('Nonempty slides required')
    slide_ids, request_ids, objects = set(), set(), set()
    for number, slide in enumerate(plan['slides'], 1):
        if slide.get('slide_number') != number:
            raise ValueError('Slides must be ordered and consecutively numbered')
        for key in ('slide_id', 'title', 'takeaway', 'layout_family', 'visual_rationale'):
            if not isinstance(slide.get(key), str) or not slide[key].strip():
                raise ValueError('Missing slide field: ' + key)
        if slide['slide_id'] in slide_ids:
            raise ValueError('Duplicate slide_id')
        slide_ids.add(slide['slide_id'])
        blocks = slide.get('content_blocks')
        if not isinstance(blocks, list) or not blocks:
            raise ValueError('Concrete content_blocks required')
        for block in blocks:
            if not any(isinstance(block.get(k), str) and block[k].strip() for k in ('text', 'data_ref', 'source_ref')):
                raise ValueError('Heading-only/empty content block')
            box = block.get('box_inches')
            if not isinstance(box, list) or len(box) != 4 or not all(type(v) in (int, float) and math.isfinite(v) for v in box):
                raise ValueError('Finite box_inches [x,y,w,h] required')
            x, y, w, h = box
            if min(x, y) < 0 or min(w, h) <= 0 or x+w > 13.333+1e-6 or y+h > 7.5+1e-6:
                raise ValueError('Content block outside canvas')
        for request in slide.get('asset_requests', []):
            identifier = request.get('request_id', '')
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', identifier) or identifier in request_ids:
                raise ValueError('Unique filename-safe request_id required')
            request_ids.add(identifier)
            if request.get('decision', 'generate_web') == 'native_or_source':
                if not request.get('decision_reason') or not request.get('replacement_object'):
                    raise ValueError('Native/source replacement needs reason and object')
                continue
            if request.get('decision', 'generate_web') != 'generate_web':
                raise ValueError('Unknown asset decision')
            from asset_job import prompt
            prompt({'asset_id': request.get('asset_id', identifier), 'kind': request.get('kind'),
                    'element': request.get('single_subject_prompt'), 'slide_id': slide['slide_id'],
                    'object_id': request.get('object_id'), 'exact_text': request.get('exact_text')})
            target = (slide['slide_id'], request['object_id'])
            if target in objects:
                raise ValueError('Duplicate asset object on slide')
            objects.add(target)
    return plan


def receive(reply, evidence, session_url, model, out):
    if not re.fullmatch(r'https://chatgpt\.com/c/[A-Za-z0-9-]+', session_url):
        raise ValueError('Observed ChatGPT conversation URL required')
    if not re.search(r'\bGPT[- ]?6\b', model, re.I):
        raise ValueError('Observed GPT-6 label required')
    raw = reply.read_text(encoding='utf-8-sig').strip()
    match = re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
    plan = validate(json.loads(match.group(1) if match else raw))
    proof = evidence.read_bytes()
    if not proof:
        raise ValueError('Nonempty actual browser observation required')
    if out.exists():
        raise FileExistsError('Use a new received-plan version')
    out.mkdir(parents=True)
    (out/'assistant-reply.txt').write_text(raw, encoding='utf-8')
    (out/'browser-observation.bin').write_bytes(proof)
    (out/'deck_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    provenance = {'schema': 'observed_web_plan_v1', 'session_url': session_url, 'observed_model': model,
                  'response_file': 'assistant-reply.txt', 'response_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                  'evidence_file': 'browser-observation.bin', 'evidence_sha256': hashlib.sha256(proof).hexdigest(),
                  'verification_limit': 'Operator-supplied visible observation; does not authenticate backend model or factual claims',
                  'status': 'received_requires_content_and_visual_review'}
    (out/'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')
    return provenance


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('reply', 'evidence', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--session-url', required=True)
    parser.add_argument('--model', required=True)
    args = parser.parse_args()
    print(json.dumps(receive(args.reply, args.evidence, args.session_url, args.model, args.out), ensure_ascii=False))
