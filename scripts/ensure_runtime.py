"""Prepare project-local Python packages needed by the PPT workflow."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from bridge_session import safe_root

PROBE = 'import pptx, PIL, defusedxml'


def ensure(project_root, python_executable, requirements, install=True):
    root = safe_root(project_root)
    runtime = root / '.ppt-runtime'
    deps = runtime / 'deps'
    requirements = Path(requirements).resolve(strict=True)
    if not requirements.is_file():
        raise ValueError('Requirements file is missing')
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(deps) + (os.pathsep + environment['PYTHONPATH'] if environment.get('PYTHONPATH') else '')
    probe = subprocess.run([str(python_executable), '-c', PROBE], env=environment,
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
    installed = False
    if probe.returncode and install:
        runtime.mkdir(parents=True, exist_ok=True)
        temp = runtime / 'tmp'
        temp.mkdir(exist_ok=True)
        environment.update(TEMP=str(temp), TMP=str(temp))
        result = subprocess.run([str(python_executable), '-m', 'pip', 'install', '--target', str(deps),
                                 '-r', str(requirements)], env=environment, capture_output=True,
                                text=True, encoding='utf-8', errors='replace')
        if result.returncode:
            raise RuntimeError('Project-local dependency install failed: ' + result.stderr[-1500:])
        installed = True
        probe = subprocess.run([str(python_executable), '-c', PROBE], env=environment,
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
    if probe.returncode:
        raise RuntimeError('PPT Python dependencies unavailable: ' + probe.stderr[-1000:])
    return {'python_executable': str(python_executable), 'python_path': str(deps) if deps.is_dir() else None,
            'dependencies_installed_now': installed, 'ready': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', required=True, type=Path)
    parser.add_argument('--python-executable', type=Path, default=Path(sys.executable))
    parser.add_argument('--requirements', type=Path, default=Path(__file__).resolve().parent.parent/'requirements.txt')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(ensure(args.project_root, args.python_executable, args.requirements,
                            install=not args.check_only), ensure_ascii=True))


if __name__ == '__main__':
    main()
