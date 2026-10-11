"""Synthetic connection records: no actual model/network claims."""
import copy
import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from bridge_session import prepare, check, safe_root


def main():
    passed = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        workspace = root / 'ppt'
        data = prepare(workspace, root)
        assert not check(workspace)['ready']
        passed.append('fresh prepare is not a connected-model claim')
        evidence = workspace / 'qa/observed.txt'
        evidence.parent.mkdir()
        evidence.write_text('Synthetic selector/image entry fixture only', encoding='utf-8')
        data.update(local_profile_configured=True, browser_connected=True, image_tool_visible=True,
                    planning_model='GPT-6', image_model='Image-2.5', observed_connection_id=data['connection_id'],
                    evidence=[{'file': 'qa/observed.txt', 'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest()}])
        record = workspace / 'bridge-connect.json'
        def save(value): record.write_text(json.dumps(value), encoding='utf-8')
        save(data)
        assert check(workspace)['ready']
        passed.append('complete scoped synthetic observation passes')
        for key, value, label in [
            ('allowed_roots', [str(root), str(root.parent)], 'multiple roots rejected'),
            ('planning_model', 'GPT-5', 'wrong text model rejected'),
            ('image_model', 'unverified', 'hidden image engine requires explicit exception'),
            ('observed_connection_id', 'old', 'old startup observation rejected'),
            ('created_at', (datetime.now(timezone.utc)-timedelta(hours=5)).isoformat(), 'expired observation rejected'),
            ('browser_connected', False, 'disconnected browser rejected'),
            ('status', 'closed', 'closed session rejected'),
            ('public_tunnel', True, 'implicit public exposure rejected'),
            ('shell_access', True, 'shell permission rejected'),
        ]:
            save({**data, key: value})
            assert not check(workspace)['ready'], label
            passed.append(label)
        save({**data, 'image_model': 'unverified', 'unverified_image_user_authorization': 'Synthetic explicit user exception'})
        assert check(workspace)['ready']
        passed.append('explicit unverified-engine exception remains distinguishable')
        save(data)
        evidence.write_text('changed', encoding='utf-8')
        assert not check(workspace)['ready']
        passed.append('changed browser evidence rejected')
        first = data['connection_id']
        assert prepare(workspace, root)['connection_id'] != first
        passed.append('restart invalidates previous observations')
        try: safe_root(Path.home())
        except ValueError: pass
        else: raise AssertionError('broad home root accepted')
        passed.append('broad home root rejected')
    for label in passed: print('PASS:', label)
    print(f'{len(passed)} checks passed')


if __name__ == '__main__': main()
