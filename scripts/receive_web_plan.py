"""Import an observed assistant reply; never submit prompts or invent web evidence."""
import argparse
import hashlib
import json
import math
import re
import shutil
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


def receive(reply, evidence, session_url, model, out, materials=None):
    if not re.fullmatch(r'https://chatgpt\.com/c/[A-Za-z0-9-]+', session_url):
        raise ValueError('Observed ChatGPT conversation URL required')
    if not re.search(r'\bGPT[- ]?6\b', model, re.I):
        raise ValueError('Observed GPT-6 label required')
    from material_handoff import check as check_materials
    if materials is None:
        raise ValueError('Transferred planning material packet required')
    material_check = check_materials(materials, target='gpt', session_url=session_url, task_id='gpt-planning')
    if not material_check['ready']:
        raise ValueError('Planning materials: ' + '; '.join(material_check['problems']))
    raw = reply.read_text(encoding='utf-8-sig').strip()
    match = re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
    plan = validate(json.loads(match.group(1) if match else raw))
    from design_layout import audit
    layout_report = audit(plan)
    from audit_plan_content import audit as audit_content
    content_report = audit_content(plan)
    from art_direction import audit as audit_art
    art_report = audit_art(plan)
    proof = evidence.read_bytes()
    if not proof:
        raise ValueError('Nonempty actual browser observation required')
    if out.exists():
        raise FileExistsError('Use a new received-plan version')
    out.mkdir(parents=True)
    (out/'assistant-reply.txt').write_text(raw, encoding='utf-8')
    (out/'browser-observation.bin').write_bytes(proof)
    (out/'deck_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    layout_report['plan_sha256'] = hashlib.sha256((out/'deck_plan.json').read_bytes()).hexdigest()
    (out/'layout-plan-audit.json').write_text(json.dumps(layout_report, ensure_ascii=False, indent=2), encoding='utf-8')
    content_report['plan_sha256'] = layout_report['plan_sha256']
    (out/'content-plan-audit.json').write_text(json.dumps(content_report, ensure_ascii=False, indent=2), encoding='utf-8')
    art_report['plan_sha256'] = layout_report['plan_sha256']
    (out/'art-direction-audit.json').write_text(json.dumps(art_report, ensure_ascii=False, indent=2), encoding='utf-8')
    provenance = {'schema': 'observed_web_plan_v1', 'session_url': session_url, 'observed_model': model,
                  'material_bundle': str(Path(materials).resolve()),
                  'material_packet_sha256': hashlib.sha256((Path(materials)/'packet.json').read_bytes()).hexdigest(),
                  'response_file': 'assistant-reply.txt', 'response_sha256': hashlib.sha256((out/'assistant-reply.txt').read_bytes()).hexdigest(),
                  'evidence_file': 'browser-observation.bin', 'evidence_sha256': hashlib.sha256(proof).hexdigest(),
                  'verification_limit': 'Operator-supplied visible observation; does not authenticate backend model or factual claims',
                  'status': 'received_requires_content_and_visual_review'}
    provenance['layout_geometry_errors'] = layout_report['geometry_errors']
    provenance['layout_warnings'] = layout_report['warnings']
    provenance['content_review_signal_pages'] = sum(bool(page['review_signals']) for page in content_report['slides'])
    (out/'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')
    return provenance


def adopt_received_plan(workspace, received):
    """Promote one observed, geometry-valid plan to the workspace's canonical path."""
    workspace, received = Path(workspace).resolve(), Path(received).resolve()
    if workspace not in received.parents or received.parent != workspace / 'planning':
        raise ValueError('Received plan must be a version directory directly under workspace/planning')
    plan_path, proof_path = received / 'deck_plan.json', received / 'provenance.json'
    audit_path = received / 'layout-plan-audit.json'
    if not all(path.is_file() for path in (plan_path, proof_path, audit_path, received / 'assistant-reply.txt', received / 'browser-observation.bin')):
        raise ValueError('Incomplete received plan; preserve source files and browser observation')
    proof = json.loads(proof_path.read_text(encoding='utf-8-sig'))
    geometry = json.loads(audit_path.read_text(encoding='utf-8-sig'))
    if proof.get('status') != 'received_requires_content_and_visual_review':
        raise ValueError('Unexpected received-plan status')
    if proof.get('response_sha256') != hashlib.sha256((received / 'assistant-reply.txt').read_bytes()).hexdigest():
        raise ValueError('Assistant reply hash mismatch')
    if proof.get('evidence_sha256') != hashlib.sha256((received / 'browser-observation.bin').read_bytes()).hexdigest():
        raise ValueError('Browser observation hash mismatch')
    plan_bytes = plan_path.read_bytes()
    if geometry.get('plan_sha256') != hashlib.sha256(plan_bytes).hexdigest():
        raise ValueError('Received plan hash mismatch')
    if geometry.get('geometry_errors') or proof.get('layout_geometry_errors'):
        raise ValueError('Repair received plan geometry before adoption')
    validate(json.loads(plan_bytes.decode('utf-8-sig')))
    canonical = workspace / 'planning' / 'deck_plan.json'
    if canonical.exists():
        if canonical.read_bytes() != plan_bytes:
            raise FileExistsError('Canonical plan differs; preserve it and choose a new revision deliberately')
    else:
        shutil.copyfile(plan_path, canonical)
    active = {'received':str(received), 'plan_sha256':hashlib.sha256(plan_bytes).hexdigest(),
              'material_bundle':proof['material_bundle'], 'session_url':proof['session_url']}
    (workspace/'planning/active-plan.json').write_text(json.dumps(active,ensure_ascii=False,indent=2),encoding='utf-8')
    review_path = workspace/'qa/delivery_review.json'
    review = json.loads(review_path.read_text(encoding='utf-8-sig')) if review_path.is_file() else {}
    review['web_planning'] = {'session_url':proof['session_url'], 'response_file':str((received/'assistant-reply.txt').relative_to(workspace)),
                             'material_bundle':proof['material_bundle']}
    review_path.parent.mkdir(parents=True,exist_ok=True)
    review_path.write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'deck_plan': str(canonical), 'received': str(received),
            'plan_sha256': hashlib.sha256(plan_bytes).hexdigest(),
            'status': 'adopted_requires_content_and_visual_review'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('reply', 'evidence', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--session-url', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--materials', required=True, type=Path)
    parser.add_argument('--workspace', type=Path, help='Adopt the validated received plan into this workspace when geometry has no errors')
    args = parser.parse_args()
    result = receive(args.reply, args.evidence, args.session_url, args.model, args.out, args.materials)
    if args.workspace:
        result['adoption'] = adopt_received_plan(args.workspace, args.out)
    print(json.dumps(result, ensure_ascii=False))
