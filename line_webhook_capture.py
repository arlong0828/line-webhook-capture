#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_dotenv(path=ROOT / '.env'):
    if not path.exists():
        return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()
LOG = Path(os.environ.get('LINE_CAPTURE_LOG', ROOT / 'data' / 'events.jsonl')).expanduser()
LAST = Path(os.environ.get('LINE_CAPTURE_LAST_ID', ROOT / 'data' / 'last-user-id.txt')).expanduser()
BIND_HOST = os.environ.get('LINE_CAPTURE_HOST', '127.0.0.1')
BIND_PORT = int(os.environ.get('LINE_CAPTURE_PORT', '8787'))

class Handler(BaseHTTPRequestHandler):
    def _send(self, code=200, body=b'OK'):
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/callback'):
            self._send(200, b'LINE webhook capture is running')
        else:
            self._send(404, b'Not Found')

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length)
        record = {
            'ts': datetime.now().isoformat(timespec='seconds'),
            'path': self.path,
            'headers': {
                k: ('[REDACTED]' if k.lower() in {'authorization', 'cookie'} else v)
                for k, v in self.headers.items()
            },
            'raw': raw.decode('utf-8', errors='replace'),
        }
        try:
            payload = json.loads(record['raw']) if record['raw'] else {}
            record['json'] = payload
            for ev in payload.get('events', []):
                src = ev.get('source', {})
                uid = src.get('userId') or src.get('groupId') or src.get('roomId')
                if uid:
                    LAST.parent.mkdir(parents=True, exist_ok=True)
                    LAST.write_text(uid + '\n', encoding='utf-8')
        except Exception as e:
            record['json_error'] = repr(e)
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        self._send(200, b'OK')

    def log_message(self, fmt, *args):
        print('%s - %s' % (self.address_string(), fmt % args), flush=True)

if __name__ == '__main__':
    print(f'Listening on http://{BIND_HOST}:{BIND_PORT}/callback', flush=True)
    ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler).serve_forever()
