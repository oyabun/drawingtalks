import http.server, functools, sys

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

root = sys.argv[1]
http.server.ThreadingHTTPServer(('0.0.0.0', 8080), functools.partial(NoCache, directory=root)).serve_forever()
