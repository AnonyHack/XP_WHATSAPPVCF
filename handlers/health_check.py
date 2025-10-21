import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from config import RENDER_PORT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    """Run the health check server on the specified port."""
    try:
        server = HTTPServer(('0.0.0.0', RENDER_PORT), HealthHandler)
        logger.info(f"🌐 Health server started on port {RENDER_PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server on port {RENDER_PORT}: {e}")
        raise