"""List LAN lights or update the saved address of one explicitly selected device."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import lan
from validation import validate
from devices import default_device_name


def select(results, identity):
    matches = [device for device in results if device['device'] == identity]
    if len(matches) != 1:
        raise ValueError('Expected exactly one reply for the selected device identity')
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--name', help='Configured Govee device name; defaults to the default device')
    parser.add_argument('--device-id', help='Exact identity printed by discovery; never select by model alone')
    args = parser.parse_args()
    devices = lan.discover()
    print(json.dumps(devices, indent=2))
    if args.update:
        path = ROOT / 'local/config.json'
        config = validate(json.loads(path.read_text()))
        name = args.name or default_device_name(config)
        if name == 'default' and 'device' in config:
            entry = config['device']
        else:
            entry = next((e for e in config.get('devices', []) if e['name'] == name), None)
        if entry is None or entry.get('type', 'govee') != 'govee':
            parser.error('Select a configured Govee device with --name')
        identity = args.device_id or entry.get('identity')
        if not identity:
            parser.error('--device-id is required for the first update')
        found = select(devices, identity)
        entry['ip'] = found['ip']
        entry['identity'] = identity
        validate(config)
        path.with_suffix('.json.bak').write_bytes(path.read_bytes())
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(config, indent=2) + '\n')
        temporary.replace(path)
        print('Local address updated; presets and schedules preserved.')


if __name__ == '__main__':
    main()
