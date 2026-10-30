"""Local layout review with fictional records. Never connect this to field logs."""
import json
import time
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from preview_web import Preview, ROOT

PREVIEW_START = time.monotonic()

SAMPLES = [
    dict(id=101, originNode=2, origin='V2', priority=1, packetType=0,
         location='SAMPLE — Purok 3, near the basketball court',
         message='SAMPLE ONLY: Medical assistance requested for an injured resident. Two people are waiting near the covered entrance.',
         route='V2 -> V1', rxTime=66400, arrival=1, latencyMs=None, crypto='Authenticated'),
    dict(id=101, originNode=3, origin='V3', priority=2, packetType=2,
         location='SAMPLE — Main road', message='SAMPLE ONLY: Floodwater is blocking the evacuation route. Please advise another route.',
         route='V3 -> V2 -> V1', rxTime=80300, arrival=2, latencyMs=13000, crypto='Authenticated'),
    dict(id=102, originNode=6, origin='V6', priority=3, packetType=2,
         location='SAMPLE — Evacuation area', message='SAMPLE ONLY: Supplies arrived. Volunteers are preparing the registration table.',
         route='V6 -> V4 -> V1', rxTime=85200, arrival=3, latencyMs=None, crypto='Authenticated'),
]
SAMPLES = [{**SAMPLES[i % 3], 'id': i + 101, 'arrival': i + 1, 'rxTime': 66400 + i * 1000} for i in range(120)]


class LayoutPreview(Preview):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/phone':
            self.reply(200, '<!doctype html><html><head><title>Phone-width sample preview</title></head><body style="margin:12px;background:#eef1f5;font-family:sans-serif"><p>390px phone-width layout — fictional sample reports</p><iframe title="Sample dashboard at phone width" src="/admin" style="width:390px;height:1100px;border:1px solid #68788c;max-width:100%"></iframe></body></html>', 'text/html; charset=utf-8')
        elif path in ('/', '/admin'):
            html = (ROOT / 'admin.html').read_text(encoding='utf-8')
            html = html.replace('<body>', '<body><aside style="padding:16px;background:#ffe08a;color:#172b4d;font-weight:bold;margin-bottom:16px;">LAYOUT PREVIEW — fictional sample reports. No live node connection or research data.</aside>')
            html = html.replace('<title>', '<title>SAMPLE PREVIEW — ')
            self.reply(200, html, 'text/html; charset=utf-8')
        elif path == '/api/live_incidents':
            query = parse_qs(urlsplit(self.path).query)
            try:
                page = int(query.get('page', ['1'])[0])
                snapshot = int(query.get('snapshot', [str(len(SAMPLES))])[0])
                if 'snapshot' in query and query.get('session') != ['777']:
                    self.reply(409, '{"error":"Sample session changed"}', 'application/json'); return
                if page < 1 or page > 6 or snapshot != len(SAMPLES):
                    raise ValueError('Unavailable sample page')
            except ValueError:
                self.reply(400, '{"error":"Invalid sample page"}', 'application/json'); return
            end = snapshot - (page - 1) * 20
            body = json.dumps(SAMPLES[max(0, end - 20):end]).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Recent-Limit', '20')
            self.send_header('X-History-Capacity', '200')
            self.send_header('X-History-Retained', str(len(SAMPLES)))
            self.send_header('X-History-Pages', '6')
            self.send_header('X-History-Snapshot', str(snapshot))
            self.send_header('X-Hub-Session', '777')
            self.send_header('X-Hub-Uptime-Ms', str(200000 + int((time.monotonic() - PREVIEW_START) * 1000)))
            self.send_header('X-Recorded-Since-Boot', str(len(SAMPLES)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.reply(404, 'Layout preview only', 'text/plain')


if __name__ == '__main__':
    print('Fictional layout preview: http://127.0.0.1:8766/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8766), LayoutPreview).serve_forever()
