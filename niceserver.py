import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

def run(server_class=HTTPServer,
        handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8002)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        for i in range(61, 71):
            print i
            time.sleep(1)
            self.wfile.write(chr(i))

run(HTTPServer, handler)
