"""Trusted local echo service used to expose proxy behavior."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from urllib.parse import urlsplit


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond()
    def do_POST(self):
        self.respond()
    def respond(self):
        parsed=urlsplit(self.path)
        size=int(self.headers.get('Content-Length','0'))
        body=self.rfile.read(min(size,65536)).decode('utf-8')
        result={'path':parsed.path,'query':parsed.query,'method':self.command,'body':body,
                'forwarded_for':self.headers.get('X-Forwarded-For',''),
                'request_id':self.headers.get('X-Request-ID','')}
        payload=json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self,*args):
        pass


if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',9001),Handler).serve_forever()
