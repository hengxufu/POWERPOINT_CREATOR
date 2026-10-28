"""Run bundled presentation engines without external skill lookup."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', choices=['presentation', 'html', 'template', 'retention', 'merge'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    values = args.arguments
    if values[:1] == ['--']:
        values = values[1:]
    if args.engine == 'presentation':
        directory = ROOT / 'vendor/presentation-skill'
        command = [sys.executable, '-X', 'utf8', str(directory/'scripts/present.py'), *values]
    elif args.engine == 'html':
        directory = Path.cwd()
        browser_root = ROOT.parent/'.ppt-runtime/browser'
        browsers = sorted(browser_root.glob('**/chrome-headless-shell.exe')) if browser_root.exists() else []
        if browsers and not os.environ.get('PPT_BROWSER_PATH'):
            os.environ['PPT_BROWSER_PATH'] = str(browsers[-1])
        command = ['node', str(ROOT/'vendor/dom-to-pptx/bin/cli-exporter.js'), *values]
    else:
        directory = Path.cwd()
        script = {'template':'template_local.py', 'merge':'merge_decks.py', 'retention':'audit_source_retention.py'}[args.engine]
        command = [sys.executable, '-X', 'utf8', str(ROOT/'scripts'/script), *values]
    return subprocess.run(command, cwd=directory, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
