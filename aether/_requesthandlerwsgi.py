from wsgiref.simple_server import WSGIRequestHandler as BaseHTTPRequestHandler

__version__ = "0.1"


class WSGIRequestHandler(BaseHTTPRequestHandler):
    server_version = "WSGIServer/" + __version__
