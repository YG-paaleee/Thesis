"""Local HTML preview only. No Heltec API or test messages are simulated."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent


class Preview(BaseHTTPRequestHandler):
    def reply(self, code, content, content_type):
        body = content.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        pages = {'/': 'index.html', '/index.html': 'index.html',
                 '/admin': 'admin.html', '/admin.html': 'admin.html'}
        if path in pages:
            self.reply(200, (ROOT / pages[path]).read_text(encoding='utf-8'), 'text/html; charset=utf-8')
        elif path.startswith('/api/'):
            self.reply(503, '{"status":"error","message":"Local preview only. Connect to the Heltec Wi-Fi to use the real service."}', 'application/json')
        else:
            self.reply(404, 'Not found', 'text/plain')

    def do_POST(self):
        self.reply(503, '{"status":"error","message":"Local preview only. No message was sent. Connect to the Heltec Wi-Fi for a real submission."}', 'application/json')


if __name__ == '__main__':
    print('Portal preview: http://127.0.0.1:8765/  Admin preview: http://127.0.0.1:8765/admin', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Preview).serve_forever()
