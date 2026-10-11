"""Loopback-only room controls; no scheduler or device polling is started here."""
import argparse
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile

import scheduler
from validation import ConfigError, require, validate

ROOT = Path(__file__).resolve().parent


def read_config(path):
    raw = path.read_bytes()
    return validate(json.loads(raw)), hashlib.sha256(raw).hexdigest(), raw


def save_schedules(path, payload):
    require(set(payload) == {'schedules', 'revision'}, 'Expected schedules and revision')
    config, revision, raw = read_config(path)
    require(payload['revision'] == revision, 'Configuration changed. Reload before saving.')
    require(isinstance(payload['schedules'], list) and len(payload['schedules']) <= 100,
            'At most 100 schedules are allowed')
    config['schedules'] = payload['schedules']
    validate(config)
    # Same-directory replacement ensures scheduler readers see a complete file.
    path.with_suffix('.json.bak').write_bytes(raw)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as f:
            temp = f.name
            os.chmod(temp, path.stat().st_mode & 0o777)
            json.dump(config, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def control(config, payload):
    require(isinstance(payload, dict), 'Expected an object')
    if set(payload) == {'preset'}:
        require(isinstance(payload['preset'], str) and payload['preset'] in config['presets'],
                'Unknown preset')
        scheduler.apply_preset(config, payload['preset'])
        return
    require(bool(payload) and set(payload) <= {'power', 'brightness', 'color'}, 'Unknown control fields')
    # Reuse preset validation without changing saved presets or schedules.
    candidate = copy.deepcopy(config)
    candidate['presets']['__manual__'] = dict(power=True, brightness=30, color=dict(r=255, g=210, b=160))
    candidate['presets']['__manual__'].update(payload)
    validate(candidate)
    if 'color' in payload:
        require(set(payload['color']) == {'r', 'g', 'b'}, 'Expected exactly r, g, b')
    device = config['device']
    with scheduler.open_socket() as sock:
        if 'power' in payload:
            scheduler.send(sock, device['ip'], device.get('port', 4003), 'turn', {'value': int(payload['power'])})
        if 'brightness' in payload:
            scheduler.send(sock, device['ip'], device.get('port', 4003), 'brightness', {'value': payload['brightness']})
        if 'color' in payload:
            scheduler.send(sock, device['ip'], device.get('port', 4003), 'colorwc',
                           {'color': payload['color'], 'colorTemInKelvin': 0})


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def reply(self, status, data, kind='application/json'):
        body = (json.dumps(data) if kind == 'application/json' else data).encode()
        self.send_response(status)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def allowed(self):
        port = self.server.server_port
        return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

    def do_GET(self):
        if not self.allowed():
            return self.reply(403, {'error': 'Local host required'})
        try:
            if self.path == '/':
                html = (ROOT / 'dashboard.html').read_text().replace('__TOKEN__', self.server.token)
                return self.reply(200, html, 'text/html')
            if self.path == '/api/config':
                config, revision, _ = read_config(self.server.config_path)
                return self.reply(200, {'presets': config['presets'], 'schedules': config['schedules'], 'revision': revision})
            self.reply(404, {'error': 'Not found'})
        except (ValueError, OSError) as exc:
            self.reply(500, {'error': f'Cannot read configuration: {exc}'})

    def do_POST(self):
        port = self.server.server_port
        origin = self.headers.get('Origin')
        if (not self.allowed() or origin not in (None, f'http://127.0.0.1:{port}', f'http://localhost:{port}')
                or not secrets.compare_digest(self.headers.get('X-Room-Token', '').encode('utf-8'), self.server.token.encode('ascii'))):
            return self.reply(403, {'error': 'Local dashboard session required'})
        if self.path not in ('/api/control', '/api/schedules'):
            return self.reply(404, {'error': 'Not found'})
        try:
            require(self.headers.get('Content-Type') == 'application/json', 'JSON required')
            require(self.headers.get('Transfer-Encoding') is None, 'Transfer encoding unsupported')
            length = int(self.headers.get('Content-Length', '0'))
            require(0 < length <= 65536, 'Request must be 1–65536 bytes')
            payload = json.loads(self.rfile.read(length))
            require(isinstance(payload, dict), 'Expected a JSON object')
            if self.path == '/api/schedules':
                save_schedules(self.server.config_path, payload)
                self.reply(200, {'message': 'Schedules saved. Existing scheduler reads them on its next check.'})
            else:
                config, _, _ = read_config(self.server.config_path)
                control(config, payload)
                self.reply(200, {'message': 'Commands sent; light delivery is not confirmed.'})
        except (ValueError, UnicodeError) as exc:
            self.reply(400, {'error': str(exc)})
        except OSError:
            self.reply(503, {'error': 'Could not complete operation. Check configuration permissions or the LAN connection. Some commands may have been sent.'})


def create_server(port=8765, config_path=scheduler.CONFIG):
    server = HTTPServer(('127.0.0.1', port), Handler)
    server.token = secrets.token_hex(32)
    server.config_path = Path(config_path)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    with create_server(args.port) as server:
        print(f'Room dashboard: http://127.0.0.1:{server.server_port} (Ctrl-C to stop)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
