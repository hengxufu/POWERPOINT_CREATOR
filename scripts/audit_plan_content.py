"""Surface content-depth review signals; never certify factual correctness."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(plan):
    pages = []
    for slide in plan.get('slides', []):
        signals = []
        variant = slide.get('theme_variant', 'content')
        blocks = slide.get('content_blocks', [])
        if variant not in ('cover', 'section', 'closing'):
            words = ''.join(str(block.get('text', '')) for block in blocks)
            if len(words.strip()) < 30 and not any(block.get('data_ref') for block in blocks):
                signals.append('thin_explanation: check whether the slide explains its claim, method or result')
            if not slide.get('evidence') and not any(block.get('source_ref') or block.get('data_ref') for block in blocks):
                signals.append('no_evidence_locator: identify a source, label the claim as a hypothesis, or record a real gap')
        if not str(slide.get('speaker_notes', '')).strip():
            signals.append('no_speaker_notes: provide a short explanation of the reasoning and transition')
        pages.append({'slide_number': slide.get('slide_number'), 'slide_id': slide.get('slide_id'),
                      'review_signals': signals})
    return {'schema': 'ppt_plan_content_advisory_v1', 'slides': pages,
            'review_required': any(p['review_signals'] for p in pages),
            'limits': 'Heuristic signals only; source existence, claim validity and adequate depth require reading actual materials.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.resolve() == args.plan.resolve():
        parser.error('Report must not overwrite plan')
    raw = args.plan.read_bytes()
    result = audit(json.loads(raw.decode('utf-8-sig')))
    result['plan_sha256'] = hashlib.sha256(raw).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'review_required': result['review_required'], 'signal_pages': sum(bool(p['review_signals']) for p in result['slides'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
