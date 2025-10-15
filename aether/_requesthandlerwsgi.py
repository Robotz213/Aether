from werkzeug.serving import WSGIRequestHandler as WerkzeugWSGIRequestHandler

__version__ = "0.1"


class WSGIRequestHandler(WerkzeugWSGIRequestHandler): ...
