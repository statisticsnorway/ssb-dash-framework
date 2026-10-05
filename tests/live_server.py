import threading
from collections.abc import Generator
from contextlib import contextmanager

from dash import Dash
from werkzeug.serving import make_server


@contextmanager
def serve_dash_app(app: Dash) -> Generator[str]:
    """Serves a Dash app on a free local port until the context exits.

    Build the app with `app_setup(..., service_prefix=None, enable_logging=False)`
    so requests are not routed through the JupyterHub proxy path, and so several
    apps can be built in the same test session.

    Args:
        app: The app to serve.

    Yields:
        str: The base URL of the running app, e.g. 'http://127.0.0.1:54321/'.
    """
    server = make_server("127.0.0.1", 0, app.server, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
