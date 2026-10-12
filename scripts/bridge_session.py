"""Fresh scoped connection contract; browser observations are agent attestations.

Never equate a local MCP health check with a verified ChatGPT model or image tool.
"""
import argparse
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_root(value):
    root = Path(value).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Project root must be a directory')
    home = Path.home().resolve()
    forbidden = [home, home / 'Desktop', home / 'Documents']
    if root == Path(root.anchor) or any(root == item or root in item.parents for item in forbidden):
        raise ValueError('Drive, home, desktop, documents or their ancestors cannot be exposed')
    for name in ('USERPROFILE', 'OneDrive'):
        if os.environ.get(name):
            candidate = Path(os.environ[name]).resolve()
            if root == candidate or root in candidate.parents:
                raise ValueError('Broad profile roots are forbidden')
    return root


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def prepare(workspace, root):
    root = safe_root(root)
    workspace = Path(workspace).resolve()
    if workspace != root and root not in workspace.parents:
        raise ValueError('PPT workspace must be inside the exact project root')
    data = {'schema': 'ppt_bridge_session_v2', 'connection_id': str(uuid.uuid4()),
            'project_root': str(root), 'allowed_roots': [str(root)], 'created_at': now(),
            'local_profile_configured': False, 'mcp_service_started': False,
            'browser_connected': False, 'planning_model': None, 'image_model': None,
            'image_tool_visible': False, 'evidence': [], 'ready': False,
            'permission': 'L1_READ_ONLY_ADVICE', 'public_tunnel': False,
            'shell_access': False, 'workspace_write_access': False,
            'status': 'requires_controller_configuration_and_browser_observation'}
    write(workspace / 'bridge-connect.json', data)
    return data


def check(workspace, max_age_hours=4):
    workspace = Path(workspace).resolve()
    errors = []
    try:
        data = json.loads((workspace / 'bridge-connect.json').read_text(encoding='utf-8-sig'))
        if data.get('schema') != 'ppt_bridge_session_v2':
            raise ValueError('Start this workspace with the embedded bridge adapter')
        root = safe_root(data['project_root'])
        if str(root) != data['project_root'] or data.get('allowed_roots') != [str(root)]:
            errors.append('ProjectRoot and sole allowed root must match exactly')
        if workspace != root and root not in workspace.parents:
            errors.append('Connection belongs to another project')
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(data.get('observed_at') or data['created_at'])).total_seconds()
        if age < -60 or age > max_age_hours * 3600:
            errors.append('Connection observation expired; refresh before use')
        for flag in ('local_profile_configured', 'browser_connected', 'image_tool_visible'):
            if data.get(flag) is not True:
                errors.append('Not verified: ' + flag)
        if data.get('status') == 'closed':
            errors.append('Connection session has ended')
        if data.get('public_tunnel') or data.get('shell_access') or data.get('workspace_write_access'):
            errors.append('PPT advice profile cannot escalate access')
        if not re.search(r'GPT[\s-]*6(?:\b|[.])', str(data.get('planning_model', '')), re.I):
            if not data.get('unverified_planning_user_authorization'):
                errors.append('GPT-6 must be observed in the actual model selector; explicit unverified-model exception required')
        image = str(data.get('image_model', ''))
        if not re.search(r'(?:image|图像)[\s-]*2[.]5', image, re.I):
            if not data.get('unverified_image_user_authorization'):
                errors.append('Image 2.5 not visibly verified; explicit unverified-engine exception required')
        evidence = data.get('evidence', [])
        if not evidence:
            errors.append('No current browser evidence recorded')
        for item in evidence:
            path = workspace / item['file']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                errors.append('Browser evidence missing or changed')
        if data.get('observed_connection_id') != data.get('connection_id'):
            errors.append('Browser observation belongs to an older startup')
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(str(error))
    return {'ready': not errors, 'problems': errors,
            'limits': 'Model labels and evidence notes are observed attestations, not proof of hidden backend identity.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'observe', 'check', 'close'])
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--project-root', type=Path)
    parser.add_argument('--planning-model')
    parser.add_argument('--image-model')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--session-url')
    parser.add_argument('--note')
    parser.add_argument('--allow-unverified-image-note')
    parser.add_argument('--allow-unverified-planning-note')
    args = parser.parse_args()
    path = args.workspace / 'bridge-connect.json'
    if args.action == 'prepare':
        if not args.project_root:
            parser.error('--project-root required')
        result = prepare(args.workspace, args.project_root)
    elif args.action == 'check':
        result = check(args.workspace)
    else:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if args.action == 'close':
            data.update(status='closed', ready=False, browser_connected=False)
        else:
            if not args.evidence or not args.note or not args.planning_model or not args.image_model:
                parser.error('observe requires actual evidence, note and observed model labels')
            if not str(args.session_url).startswith('https://chatgpt.com/'):
                parser.error('Observed ChatGPT session URL required')
            relative = args.evidence.resolve().relative_to(args.workspace.resolve())
            data.update(browser_connected=True, image_tool_visible=True,
                        planning_model=args.planning_model, image_model=args.image_model,
                        session_url=args.session_url, observation_note=args.note,
                        observed_connection_id=data['connection_id'], observed_at=now(), status='observed',
                        unverified_image_user_authorization=args.allow_unverified_image_note,
                        unverified_planning_user_authorization=args.allow_unverified_planning_note,
                        evidence=[{'file': str(relative), 'sha256': hashlib.sha256(args.evidence.read_bytes()).hexdigest()}])
        write(path, data)
        result = check(args.workspace)
        if args.action == 'observe':
            data['ready'] = result['ready']
            write(path, data)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if args.action in ('prepare', 'close') or result.get('ready') else 1


if __name__ == '__main__':
    raise SystemExit(main())
