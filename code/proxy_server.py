import socketserver
import http.server
from requests.models import Response
import socket
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from circuit_breaker import CircuitBreaker

PORT = 9097

responses = {
    200: ("OK", "Request fulfilled, document follows"),
    500: ("Internal Server Error", "Server got itself in trouble"),
}

obj = CircuitBreaker(
    exceptions=(Exception,), max_failure_count=2, reset_timeout=15, call_timeout=2
)


class MyProxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = self.path
        try:
            res = obj.redirect_call(url)
            print("Circuit Breaker Object: ", vars(obj))
            if res.code == 200:
                self.send_response(200)
                self.end_headers()
                self.copyfile(res, self.wfile)
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(res.content)
        except socket.timeout as exception:
            print("Circuit Breaker Object: ", vars(obj))
            self.send_response(504, "timed out")
            self.end_headers()
            self.wfile.write(b'{"msg": "Request Timeout"}')
        except Exception as exception:
            print("Circuit Breaker Object: ", vars(obj))
            self.send_response(500, "server failed")
            self.end_headers()
            self.wfile.write(b'{"msg": "Failure endpoint"}')


httpd = socketserver.TCPServer(("", PORT), MyProxy)
print("Now serving at", str(PORT))
httpd.serve_forever()
