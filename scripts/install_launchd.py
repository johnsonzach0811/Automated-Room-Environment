"""Preview or install one scheduler owner. No sudo and no lights are sent."""
import argparse
import datetime
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from validation import validate


def definition(repo, python, home):
    return {
        'Label': 'com.roomautomation.scheduler',
        'ProgramArguments': [str(python), '-B', str(repo / 'scheduler.py'), 'check'],
        'WorkingDirectory': str(repo),
        'StartCalendarInterval': [{'Minute': minute} for minute in range(60)],
        'StandardOutPath': str(home / 'Library/Logs/room-scheduler.log'),
        'StandardErrorPath': str(home / 'Library/Logs/room-scheduler-error.log'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Without this option, preview only')
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    repo, python, home = args.repo.resolve(), args.python.resolve(), Path.home()
    if sys.platform != 'darwin':
        parser.error('LaunchAgents require macOS')
    if not python.is_file() or not (repo / 'scheduler.py').is_file():
        parser.error('Python and repository paths must exist')
    source = repo / 'local/config.json'
    if not source.exists():
        source = repo / 'config.json'
    if not source.exists():
        parser.error('Copy config.example.json to local/config.json and set the device address first')
    validate(json.loads(source.read_text()))
    agents = home / 'Library/LaunchAgents'
    target = agents / 'com.roomautomation.scheduler.plist'
    data = plistlib.dumps(definition(repo, python, home))
    print(f'Job: {target}\nPython: {python}\nCheckout: {repo}\nTrigger: every local calendar minute')
    print('Preserve config; migrate it to ignored local/config.json; retire legacy/test lighting jobs; install scheduler.')
    if not args.apply:
        print('Preview only. Re-run with --apply to install.')
        return
    backup = repo / 'local' / ('installation-backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    shutil.copy2(source, backup / 'config.json')
    destination = repo / 'local/config.json'
    if source != destination:
        shutil.copy2(source, destination)
    agents.mkdir(parents=True, exist_ok=True)
    (home / 'Library/Logs').mkdir(parents=True, exist_ok=True)
    import os
    domain = f'gui/{os.getuid()}'
    # Restrict cleanup to this project's known legacy and temporary test jobs.
    labels = ['com.roomautomation.scheduler', 'com.roomautomation.morninglights', 'com.roomautomation.test1030']
    for label in labels:
        path = agents / (label + '.plist')
        if path.exists():
            shutil.copy2(path, backup / path.name)
        loaded = subprocess.run(['launchctl', 'print', domain + '/' + label], capture_output=True)
        if loaded.returncode == 0:
            subprocess.run(['launchctl', 'bootout', domain + '/' + label], check=True)
        if label != 'com.roomautomation.scheduler' and path.exists():
            path.unlink()
    temporary = target.with_suffix('.plist.tmp')
    temporary.write_bytes(data)
    temporary.replace(target)
    subprocess.run(['launchctl', 'enable', domain + '/com.roomautomation.scheduler'], check=True)
    subprocess.run(['launchctl', 'bootstrap', domain, str(target)], check=True)
    print(f'Installed. Backups: {backup}. No immediate lighting command was sent.')


if __name__ == '__main__':
    main()
